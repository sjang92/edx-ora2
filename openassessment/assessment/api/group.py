"""
API for assessing group members.

"""
import logging
from openassessment.assessment.errors.group import GroupAssessmentError
from openassessment.assessment.models import Assessment, AssessmentPart
from openassessment.assessment.models.group import GroupWorkflow, GroupWorkflowItem
from openassessment.assessment.serializers import rubric_from_dict, AssessmentSerializer, serialize_assessments
from openassessment.groups import api as group_api
from openassessment.projects import api as project_api

# Assessments are tagged as "group-evaluation"
GROUP_TYPE = "GE"

logger = logging.getLogger(__name__)

# TODO NOTE TO SELF: may need a 'representative submission uuid' for a project


def submitter_is_finished(submission_uuid, requirements):
    if requirements is None or 'student_item' not in requirements:
        return False
    student_item = requirements['student_item']
    finished, count = finished_requirements(student_item)
    return finished


def finished_requirements(student_item):
    project = project_api.get_group_project(student_item)
    group = group_api.get_group_by_uuid(project['group_uuid'])
    workflows = GroupWorkflow.objects.filter(
        student_id=student_item['student_id'],
        course_id=student_item['course_id'],
        item_id=student_item['item_id'],
        project_uuid=project['uuid']
    )

    if not workflows:
        return False, 0
    count = len(workflows[0].graded.filter(assessment__isnull=False))
    return count >= len(group['members']) - 1, count


def assessment_is_finished(submission_uuid, requirements):
    if requirements is None or 'student_item' not in requirements:
        return False
    student_item = requirements['student_item']

    project = project_api.get_project_by_submission_uuid(submission_uuid)
    group = group_api.get_group_by_uuid(project['group_uuid'])

    workflows = GroupWorkflow.objects.filter(
        student_id=student_item['student_id'],
        course_id=student_item['course_id'],
        item_id=student_item['item_id'],
        project_uuid=project['uuid']
    )
    if not workflows:
        return False
    count = len(workflows[0].graded.filter(assessment__isnull=False))
    return count >= len(group['members']) - 1


def on_start(submission_uuid):
    """
    When initializing group workflow, create a new workflow per group member.

    """
    project = project_api.get_project_by_submission_uuid(submission_uuid)
    group = group_api.get_group_by_uuid(project['group_uuid'])
    for member in group['members']:
        workflow = GroupWorkflow.objects.create(
            student_id=member['student_id'],
            item_id=member['item_id'],
            course_id=member['course_id'],
            project_uuid=project['uuid']
        )
        workflow.save()


def get_score(submission_uuid, requirements):
    # TODO worry about scores when we care about scores.
    return {"points_earned": 0, "points_possible": 0}


def create_assessment(
        student_item,
        options_selected,
        criterion_feedback,
        overall_feedback,
        rubric_dict,
        scored_at=None):

    project = project_api.get_group_project(student_item)
    rubric = rubric_from_dict(rubric_dict)
    option_ids = rubric.options_ids(options_selected)

    scorer_workflow = GroupWorkflow.objects.filter(
        student_id=student_item['student_id'],
        course_id=project['course_id'],
        item_id=project['item_id'],
        project_uuid=project['uuid']
    )

    items = scorer_workflow.graded.filter(assessment__isnull=True)
    if not items:
        raise GroupAssessmentError("No workflow item found for group members")

    assessment = {
        "rubric": rubric.id,
        "scorer_id": student_item['student_id'],
        "submission_uuid": project['rep_uuid'],
        "score_type": GROUP_TYPE,
        "feedback": overall_feedback[0:Assessment.MAXSIZE],
    }

    if scored_at is not None:
        assessment["scored_at"] = scored_at

    serializer = AssessmentSerializer(data=assessment)

    if not serializer.is_valid():
        msg = (
            u"An error occurred while serializing the assessment associated with "
            u"the scorer's project UUID {}."
        ).format(project['uuid'])
        raise GroupAssessmentError(msg)

    assessment = serializer.save()

    # We do this to do a run around django-rest-framework serializer
    # validation, which would otherwise require two DB queries per
    # option to do validation. We already validated these options above.
    AssessmentPart.add_to_assessment(assessment, option_ids, criterion_feedback=criterion_feedback)

    items[0].assessment = assessment
    items[0].save()


def get_assessment_median_scores(submission_uuid):
    # TODO steal from peer
    pass


def get_assessments(student_item, project_uuid, scored_only=True, limit=None):
    workflows = GroupWorkflow.objects.filter(
        student_id=student_item['student_id'],
        course_id=student_item['course_id'],
        item_id=student_item['item_id'],
        project_uuid=project_uuid
    )

    if not workflows:
        return None

    assessments = Assessment.objects.filter(
        pk__in=[
            item.assessment.pk for item in GroupWorkflowItem.objects.filter(
                author=workflows[0], assessment__isnull=False
            )
        ]
    )
    return serialize_assessments(assessments)


def get_members_to_assess(student_item):
    project = project_api.get_group_project(student_item)
    group = group_api.get_group_by_uuid(project['group_uuid'])

    workflows = GroupWorkflow.objects.filter(
        student_id=student_item['student_id'],
        course_id=student_item['course_id'],
        item_id=student_item['item_id'],
        project_uuid=project['uuid']
    )

    if not workflows:
        raise GroupAssessmentError("No workflow found for the current user.")
    items = workflows[0].graded.filter(assessment__isnull=True)
    if items:
        current_member = items[0].author.student_id
        for member in group['members']:
            if current_member == member['student_id']:
                return member

    next_member = _get_next_member(workflows[0], group)
    if next_member is None:
        return None

    author_workflows = GroupWorkflow.objects.filter(
        student_id=next_member['student_id'],
        course_id=next_member['course_id'],
        item_id=next_member['item_id'],
        project_uuid=project['uuid']
    )

    if not author_workflows:
        raise GroupAssessmentError("No workflow found for group member.")

    GroupWorkflowItem.objects.create(
        scorer=workflows[0],
        author=author_workflows[0],
        project_uuid=project['uuid']
    )

    return next_member


def _get_next_member(workflow, group):
    already_scored = workflow.graded.filter(assessment__isnull=False)
    for member in group['members']:
        if member['student_id'] == workflow.student_id:
            continue
        elif member['student_id'] not in [graded.author.student_id for graded in already_scored]:
            return member


def get_member_count(student_item):
    project = project_api.get_group_project(student_item)
    group = group_api.get_group_by_uuid(project['group_uuid'])
    return len(group['members'])