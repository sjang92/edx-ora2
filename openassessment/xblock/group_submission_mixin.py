import dateutil
import logging

from django.utils.translation import ugettext as _
from xblock.core import XBlock

from openassessment.projects import api
from openassessment.groups import api as group_api
from submissions import api as submission_api
from .resolve_dates import DISTANT_FUTURE


logger = logging.getLogger(__name__)


class GroupSubmissionMixin(object):

    @XBlock.json_handler
    def submit_project_part(self, data, suffix=''):
        """Submit a part of the project.

        Allows submission of new responses to a project.

        Args:
            data (dict): Data should contain one attribute: submission. This is
                the response from the student which should be stored in the
                Open Assessment system.
            suffix (str): Not used in this handler.

        Returns:
            (tuple): success and message.

        """
        student_sub = data['submission']
        order_num = int(data['order'])
        student_item_dict = self.get_student_item_dict()

        # Short-circuit if no user is defined (as in Studio Preview mode)
        # Since students can't submit, they will never be able to progress in the workflow
        if self.in_studio_preview:
            return False, "Cannot submit in preview."

        workflow = self.get_workflow_info()
        if not workflow:
            try:
                part = self.create_group_part(student_item_dict, student_sub, order_num)
                return True, "Create new project part with submission uuid {}".format(part['submission_uuid'])
            except (api.GroupProjectError):
                logger.exception("This response was not submitted.")
                return False, "Unknown error submitting project part."

    def create_group_part(self, student_item_dict, student_sub, order_num):

        # Store the student's response text in a JSON-encodable dict
        # so that later we can add additional response fields.
        student_sub_dict = {'text': student_sub}
        part = api.submit_project_part(student_item_dict, order_num, student_sub_dict)
        # If the project now has enough parts, create the assessment workflow
        # using the project UUID instead of the submission UUID.
        project = api.get_group_project(student_item_dict)
        assessment = self.get_assessment_module('group-project-assessment')
        if len(project['parts']) >= len(assessment['parts']):
            # TODO: We're cheating and just giving the last submission in
            # the project.
            self.create_workflow(part["submission_uuid"])
            self.submission_uuid = part["submission_uuid"]

        # Emit analytics event...
        self.runtime.publish(
            self,
            "openassessmentblock.create_project_part",
            {
                "submission_uuid": part["submission_uuid"],
                "order_num": part["order_num"],
                "created_at": part["created_at"],
            }
        )
        return part

    @staticmethod
    def get_user_submission(submission_uuid):
        """Return the most recent submission by user in workflow

        Return the most recent submission.  If no submission is available,
        return None. All submissions are preserved, but only the most recent
        will be returned in this function, since the active workflow will only
        be concerned with the most recent submission.

        Args:
            submission_uuid (str): The uuid for the submission to retrieve.

        Returns:
            (dict): A dictionary representation of a submission to render to
                the front end.

        """
        try:
            return api.get_submission(submission_uuid)
        except api.SubmissionRequestError:
            # This error is actually ok.
            return None

    @XBlock.handler
    def render_group_submission(self, data, suffix=''):
        """Renders the group submission section

        Replaces the submission section of the XBlock with a group submission
        section. This section takes multiple parts, and submissions, instead
        of just one.

        """
        path, context = self.group_submission_path_and_context()
        return self.render_assessment(path, context_dict=context)

    def group_submission_path_and_context(self):
        """
        Determine the template path and context to use when
        rendering the response (submission) step.

        Returns:
            tuple of `(path, context)`, where `path` (str) is the path to the template,
            and `context` (dict) is the template context.

        """
        workflow = self.get_workflow_info()
        student_item = self.get_student_item_dict()
        problem_closed, reason, start_date, due_date = self.is_closed('submission')

        path = 'openassessmentblock/group_response/oa_group_response.html'
        context = {}

        assessment = self.get_assessment_module('group-project-assessment')
        if assessment:
            context['parts'] = assessment['parts']

        group = group_api.get_group(student_item)
        if not group:
            return 'openassessmentblock/response/oa_response_unavailable.html', context

        project = api.get_group_project(student_item)
        if not project:
            project = api.create_group_project(student_item)

        for part in project['parts']:
            order = part['order_num']
            sub = submission_api.get_submission(part['submission_uuid'])
            for context_part in context['parts']:
                if context_part['order_num'] == order:
                    context_part['answer'] = sub['answer']['text']

        # Due dates can default to the distant future, in which case
        # there's effectively no due date.
        # If we don't add the date to the context, the template won't display it.
        if due_date < DISTANT_FUTURE:
            context["submission_due"] = due_date

        if not workflow and problem_closed:
            if reason == 'due':
                path = 'openassessmentblock/response/oa_response_closed.html'
            elif reason == 'start':
                context['submission_start'] = start_date
                path = 'openassessmentblock/response/oa_response_unavailable.html'
        elif not workflow:
            path = 'openassessmentblock/group_response/oa_group_response.html'
        elif workflow["status"] == "done":
            student_submission = self.get_user_submission(
                workflow["submission_uuid"]
            )
            context["student_submission"] = student_submission
            path = 'openassessmentblock/response/oa_response_graded.html'
        else:
            context["student_submission"] = self.get_user_submission(
                workflow["submission_uuid"]
            )
            path = 'openassessmentblock/response/oa_response_submitted.html'

        return path, context
