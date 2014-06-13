"""
Public Interface for working with Group Projects.

"""
import logging

from submissions import api as submission_api
from openassessment.groups import api as group_api
from openassessment.projects.models import GroupProject
from openassessment.projects.errors import GroupProjectError
from openassessment.projects.serializers import GroupProjectSerializer, GroupProjectPartSerializer


logger = logging.getLogger(__name__)


def create_group_project(student_item):
    """
    Create a group project if one does not exist for the given group

    TODO: Ideally, take in the student item, have location mapping configured,
    and do not require manually punching in group UUID.

    Args:
        student_item (dict): The student item representing this student for this
            location and course.
        group_uuid (str): The UUID for the group we want to begin a project for.

    Returns:
        A dict containing the serialized form of the new project.

    """
    group = group_api.get_group(student_item)
    project = get_group_project(student_item)
    if project:
        msg = "Group Project already exists for group {}".format(group['uuid'])
        logger.warn(msg)
        raise GroupProjectError(msg)

    # Serializers won't allow nullable fields on creation?
    new_project = GroupProject.objects.create(
        group_uuid=group['uuid'],
        course_id=student_item['course_id'],
        item_id=student_item['item_id'],
    )
    new_project.save()
    return GroupProjectSerializer(new_project).data


def get_project_by_submission_uuid(submission_uuid):
    """
    Get a project by its representative submission UUID.

    Args:
        submission_uuid (str): The representative submission for this project.

    Returns:
        The project, serialized. If no submission UUID is matched, returns
        None.

    """
    projects = GroupProject.objects.filter(rep_uuid=submission_uuid)
    if projects:
        return GroupProjectSerializer(projects[0]).data


def get_group_project(student_item):
    """
    Retrieves a group project for the given student and group.

    Args:
        student_item (dict): The student id, course, and location.
        group_uuid (str): The unique identifier for the student's group.

    Returns:
        Serialized form (dict) of the group project.

    """
    project = _get_latest_group_project(student_item)
    if project:
        return GroupProjectSerializer(project).data


def submit_project_part(student_item, order_num, answer):
    """
    Creates a 'part' of the group project.

    This part represents some work that needs to be submitted to complete the
    project and initiate assessment.

    Args:
        student_item (dict): The student id, course, location
        group_uuid (str): The group UUID.
        order_num (int): Associated configuration for which part of the project
            we are submitting an answer to.
        answer (str): The answer to this part of the project.

    Returns:
        The serialized form of the project part.

    """
    # Make sure the project exists.
    project = _get_latest_group_project(student_item)
    if not project:
        raise GroupProjectError("No project found to add this part to!")

    # Check to see if any group members already submitted an answer for this
    # part
    parts = project.parts.filter(order_num=order_num)
    if parts:
        raise GroupProjectError("This part of the project has already been submitted.")

    # If all is well, submit the answer and create the part associated with
    # the project.
    submission = submission_api.create_submission(student_item, answer)
    part_data = {
        'group_project': project.pk,
        'submission_uuid': submission['uuid'],
        'order_num': order_num
    }
    new_part = GroupProjectPartSerializer(data=part_data)
    if not new_part.is_valid():
        raise GroupProjectError(new_part.errors)

    if len(project.parts.all()) == 0:
        project.rep_uuid = submission['uuid']
        project.save()

    new_part.save()

    return new_part.data


def _get_latest_group_project(student_item):
    """
    Private function to return the model object for the latest group project.

    """
    group = group_api.get_group(student_item)
    if not group:
        return None

    projects = GroupProject.objects.filter(
        group_uuid=group['uuid'],
        item_id=student_item['item_id'],
        course_id=student_item['course_id']
    )

    if projects:
        return projects[0]
