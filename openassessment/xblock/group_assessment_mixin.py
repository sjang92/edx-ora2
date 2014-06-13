import logging

from django.utils.translation import ugettext as _
from webob import Response
from xblock.core import XBlock

from openassessment.assessment.errors.group import GroupAssessmentError
from openassessment.assessment.api import group as group_api
from openassessment.workflow.errors import AssessmentWorkflowError

from .resolve_dates import DISTANT_FUTURE

logger = logging.getLogger(__name__)


class GroupAssessmentMixin(object):
    """
    The Group Assessment Mixin

    """

    @XBlock.json_handler
    def group_assess(self, data, suffix=''):
        """
        Assess group members

        """
        # Validate the request
        if 'options_selected' not in data:
            return {'success': False, 'msg': _('Must provide options selected in the assessment')}

        if 'overall_feedback' not in data:
            return {'success': False, 'msg': _('Must provide overall feedback in the assessment')}

        if 'criterion_feedback' not in data:
            return {'success': False, 'msg': _('Must provide feedback for criteria in the assessment')}

        assessment_ui_model = self.get_assessment_module('group-assessment')
        if assessment_ui_model:
            rubric_dict = {
                'criteria': self.rubric_criteria
            }

            try:
                # Create the assessment
                assessment = group_api.create_assessment(
                    self.get_student_item_dict(),
                    data['options_selected'],
                    self._clean_criterion_feedback(data['criterion_feedback']),
                    data['overall_feedback'],
                    rubric_dict,
                    assessment_ui_model['must_be_graded_by']
                )

            except GroupAssessmentError:
                logger.warning(
                    u"Group API error for submission UUID {}".format(self.submission_uuid),
                    exc_info=True
                )
                return {'success': False, 'msg': _(u"Your group assessment could not be submitted.")}

            # Update both the workflow that the submission we're assessing
            # belongs to, as well as our own (e.g. have we evaluated enough?)
            try:
                if assessment:
                    self.update_workflow_status(submission_uuid=assessment['submission_uuid'])
                self.update_workflow_status()
            except AssessmentWorkflowError:
                logger.exception(
                    u"Workflow error occurred when submitting group assessment "
                    u"for submission {}".format(self.submission_uuid)
                )
                msg = _('Could not update workflow status.')
                return {'success': False, 'msg': msg}

            # Temp kludge until we fix JSON serialization for datetime
            assessment["scored_at"] = str(assessment["scored_at"])

            return {'success': True, 'msg': u''}

        else:
            return {'success': False, 'msg': _('Could not load group assessment.')}

    @XBlock.handler
    def render_group_assessment(self, data, suffix=''):
        """
        Render

        """
        if "group-assessment" not in self.assessment_steps:
            return Response(u"")
        path, context_dict = self.group_path_and_context()
        return self.render_assessment(path, context_dict)

    def group_path_and_context(self):
        """
        Return the template path and context for rendering the group assessment step.

        """
        path = 'openassessmentblock/group_assessment/oa_group_unavailable.html'
        finished = False
        problem_closed, reason, start_date, due_date = self.is_closed(step="group-assessment")

        context_dict = {
            "rubric_criteria": self.rubric_criteria
        }

        if self.rubric_feedback_prompt is not None:
            context_dict["rubric_feedback_prompt"] = self.rubric_feedback_prompt

        # We display the due date whether the problem is open or closed.
        # If no date is set, it defaults to the distant future, in which
        # case we don't display the date.
        if due_date < DISTANT_FUTURE:
            context_dict['group_due'] = due_date

        workflow = self.get_workflow_info()
        if not workflow:
            return path, {}

        student_item = self.get_student_item_dict()
        assessment = self.get_assessment_module('group-assessment')
        if assessment:
            context_dict["must_grade"] = group_api.get_member_count(student_item) - 1
            finished, count = group_api.finished_requirements(student_item)
            context_dict["graded"] = count
            context_dict["review_num"] = count + 1

            if context_dict["must_grade"] - count == 1:
                context_dict["submit_button_text"] = _(
                    "Submit your assessment & move onto next step"
                )
            else:
                context_dict["submit_button_text"] = _(
                    "Submit your assessment & move to member #{response_number}"
                ).format(response_number=(count + 2))

        # Once a student has completed a problem, it stays complete,
        # so this condition needs to be first.
        if workflow.get('status') == 'done' or finished:
            path = "openassessmentblock/group_assessment/oa_group_complete.html"
        elif reason == 'due' and problem_closed:
            path = 'openassessmentblock/group_assessment/oa_group_closed.html'
        elif reason == 'start' and problem_closed:
            context_dict["group_start"] = start_date
            path = 'openassessmentblock/group_assessment/oa_group_unavailable.html'
        elif workflow.get("status") == "group":
            member = self.get_group_member(student_item)
            if member:
                path = 'openassessmentblock/group_assessment/oa_group_assessment.html'
                context_dict["member"] = member

        return path, context_dict

    def get_group_member(self, student_item_dict):
        """
        Retrieve a member to assess

        """
        member = False
        try:
            member = group_api.get_members_to_assess(student_item_dict)
        except GroupAssessmentError as err:
            logger.exception(err)

        return member

    def _clean_criterion_feedback(self, criterion_feedback):
        """
        Remove per-criterion feedback for criteria with feedback disabled
        in the rubric.

        Args:
            criterion_feedback (dict): Mapping of criterion names to feedback text.

        Returns:
            dict

        """
        return {
            criterion['name']: criterion_feedback[criterion['name']]
            for criterion in self.rubric_criteria
            if criterion['name'] in criterion_feedback
        and criterion.get('feedback', 'disabled') == 'optional'
        }
