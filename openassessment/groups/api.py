"""
Public interface for the Assessment Workflow.

"""
import logging

from openassessment.groups.models import WorkGroup, WorkGroupMember
from openassessment.groups.errors import WorkGroupError
from openassessment.groups.serializers import WorkGroupSerializer, WorkGroupMemberSerializer


logger = logging.getLogger(__name__)


def join_group(student_item, student_name, student_email, group_size, project_location=None):
    """
    Join a group. Looks for a group that does not have enough members in it.

    Args:
        student_item (dict): The student that needs to join a group for the
            given location and course.
        student_name (str): The name of the student.
        student_email (str): The student's email address.
        group_size (int): The size of a group; this determines if any of the
            current groups need more members.

    Kwargs:
        project_location (str): The location this group is associated with

    Returns:
        Serialized representation of the group this student is now a part of. If
        no group was found, or requires more members, returns None.

    """
    item_id = project_location if project_location else student_item['item_id']
    members = WorkGroupMember.objects.filter(
        student_id=student_item['student_id'],
        item_id=item_id,
        course_id=student_item['course_id']
    )
    if members:
        raise WorkGroupError("Student is already in a workgroup.")

    groups = WorkGroup.objects.filter(
        item_id=item_id,
        course_id=student_item['course_id']
    )

    for group in groups:
        if len(group.members.all()) < group_size:
            _create_group_member(student_item, student_name, student_email, group.pk, project_location=item_id)
            return WorkGroupSerializer(group).data


def create_group(student_item, student_name, student_email, project_location=None):
    """
    Creates a new group with the current student as the first member.

     Args:
        student_item (dict): A dict defining the first student, location, and
            course.
        student_name (str): The name of the student.
        student_email (str): The email address for the student.

    Kwargs:
        project_location (str): The location this group is associated with

    Returns:
        Serialized representation of the newly created group.

    """
    item_id = project_location if project_location else student_item['item_id']
    # First we'll create the new group.
    group_data = {
        'item_id': item_id,
        'course_id': student_item['course_id']
    }
    group = WorkGroupSerializer(data=group_data)

    if not group.is_valid():
        raise WorkGroupError("Could not save new work group.")
    group_model = group.save()

    # Once we create the new group, we can add its first member.
    _create_group_member(student_item, student_name, student_email, group_model.pk, project_location=item_id)
    return group.data


def _create_group_member(student_item, student_name, student_email, group_id, project_location=None):
    """
    Create a group member and associate the member with the given group id.

    Args:
        student_item (dict): Student Item to create a member from.
        student_name (str): The name of the student.
        student_email (str): The email address.
        group_id (int): The unique ID of the group to add the member to.

    Kwargs:
        project_location (str): The location this group is associated with

    Returns:
        The serialized representation of the new member.

    """
    item_id = project_location if project_location else student_item['item_id']
    # Once we create the new group, we can add its first member.
    member_data = {
        'student_id': student_item['student_id'],
        'item_id': item_id,
        'course_id': student_item['course_id'],
        'student_name': student_name,
        'student_email': student_email,
        'group': group_id

    }
    member = WorkGroupMemberSerializer(data=member_data)
    if not member.is_valid():
        raise WorkGroupError(member.errors)
    member.save()
    return member.data


def get_group(student_item, project_location=None):
    """
    Return the group this student belongs to for the location and course.

    Args:
        student_item (dict): Student, location, and course to use to find an
            associated group.

    Kwargs:
        project_location (str): The location this group is associated with

    Returns:
        A serialized representation of the student's group.

    """
    item_id = project_location if project_location else student_item['item_id']
    try:
        members = WorkGroupMember.objects.filter(
            student_id=student_item["student_id"],
            item_id=item_id,
            course_id=student_item['course_id']
        )
        if members:
            return WorkGroupSerializer(members[0].group).data
    except WorkGroupMember.DoesNotExist:
        return None



