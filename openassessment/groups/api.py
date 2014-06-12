"""
Public interface for the Assessment Workflow.

"""
import logging

from openassessment.groups.models import WorkGroup, WorkGroupMember
from openassessment.groups.errors import WorkGroupError
from openassessment.groups.serializers import WorkGroupSerializer, WorkGroupMemberSerializer


logger = logging.getLogger(__name__)


def join_group(student_item, student_name, student_email, group_size):
    """
    Join a group. Looks for a group that does not have enough members in it.

    Args:
        student_item (dict): The student that needs to join a group for the
            given location and course.
        student_name (str): The name of the student.
        student_email (str): The student's email address.
        group_size (int): The size of a group; this determines if any of the
            current groups need more members.

    Returns:
        Serialized representation of the group this student is now a part of. If
        no group was found, or requires more members, returns None.

    """
    members = WorkGroupMember.objects.filter(
        student_id=student_item['student_id'],
        item_id=student_item['item_id'],
        course_id=student_item['course_id']
    )
    if members:
        raise WorkGroupError("Student is already in a workgroup.")

    groups = WorkGroup.objects.filter(
        item_id=student_item['item_id'],
        course_id=student_item['course_id']
    )

    for group in groups:
        if len(group.members.all()) < group_size:
            _create_group_member(student_item, student_name, student_email, group.pk)
            return WorkGroupSerializer(group).data


def create_group(student_item, student_name, student_email):
    """
    Creates a new group with the current student as the first member.

     Args:
        student_item (dict): A dict defining the first student, location, and
            course.
        student_name (str): The name of the student.
        student_email (str): The email address for the student.

    Returns:
        Serialized representation of the newly created group.

    """
    # First we'll create the new group.
    group_data = {
        'item_id': student_item['item_id'],
        'course_id': student_item['course_id']
    }
    group = WorkGroupSerializer(data=group_data)

    if not group.is_valid():
        raise WorkGroupError("Could not save new work group.")
    group_model = group.save()

    # Once we create the new group, we can add its first member.
    _create_group_member(student_item, student_name, student_email, group_model.pk)

    return group.data


def _create_group_member(student_item, student_name, student_email, group_id):
    """
    Create a group member and associate the member with the given group id.

    Args:
        student_item (dict): Student Item to create a member from.
        student_name (str): The name of the student.
        student_email (str): The email address.
        group_id (int): The unique ID of the group to add the member to.

    Returns:
        The serialized representation of the new member.

    """
    # Once we create the new group, we can add its first member.
    member_data = {
        'student_id': student_item['student_id'],
        'item_id': student_item['item_id'],
        'course_id': student_item['course_id'],
        'student_name': student_name,
        'student_email': student_email,
        'group': group_id

    }
    member = WorkGroupMemberSerializer(data=member_data)
    if not member.is_valid():
        raise WorkGroupError("Could not create new member.")
    member.save()
    return member.data


def get_group(student_item):
    """
    Return the group this student belongs to for the location and course.

    Args:
        student_item (dict): Student, location, and course to use to find an
            associated group.

    Returns:
        A serialized representation of the student's group.

    """
    try:
        member = WorkGroupMember.objects.get(
            student_id=student_item["student_id"],
            item_id=student_item['item_id'],
            course_id=student_item['course_id']
        )
        return WorkGroupSerializer(member.group).data
    except WorkGroupMember.DoesNotExist:
        return None



