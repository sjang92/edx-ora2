"""
API for assessing group members.

"""
import logging

# Assessments are tagged as "group-evaluation"
GROUP_TYPE = "GE"

logger = logging.getLogger(__name__)

# TODO NOTE TO SELF: may need a 'representative submission uuid' for a project


def submitter_is_finished(submission_uuid, requirements):
    return False


def assessment_is_finished(submission_uuid, requirements):
    return False


def on_start(submission_uuid):
    pass


def get_score(submission_uuid, requirements):
    return {"points_earned": 0, "points_possible": 0}


def create_assessment(
        scorer_submission_uuid,
        scorer_id,
        options_selected,
        criterion_feedback,
        overall_feedback,
        rubric_dict,
        num_required_grades,
        scored_at=None):
    pass


def get_rubric_max_scores(submission_uuid):
    # TODO steal from peer.
    pass


def get_assessment_median_scores(submission_uuid):
    # TODO steal from peer
    pass


def has_finished_required_evaluating(submission_uuid, required_assessments):
    # TODO mock peer, can't steal.
    pass


def get_assessments(student_item, project_uuid, scored_only=True, limit=None):
    # TODO mock peer
    pass


def get_members_to_assess(submission_uuid):
    # TODO get a member from the group.
    pass


def create_group_workflow(project_uuid):
    pass


def create_group_workflow_item(scorer_submission_uuid, submission_uuid):
    pass


def get_assessment_feedback(submission_uuid):
    pass


def set_assessment_feedback(feedback_dict):
    pass