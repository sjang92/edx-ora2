"""
Serializers for WorkGroups and group members.

"""
from rest_framework import serializers
from openassessment.groups.models import WorkGroup, WorkGroupMember


class WorkGroupMemberSerializer(serializers.ModelSerializer):
    """
    Represents a member in a group.
    """
    class Meta:
        model = WorkGroupMember
        fields = (
            'student_id',
            'item_id',
            'course_id',
            'student_name',
            'student_email',
            'created_at',
            'group'
        )


class WorkGroupSerializer(serializers.ModelSerializer):
    """
    Representation of the WorkGroup.

    """
    members = WorkGroupMemberSerializer(many=True, default=None, required=False)

    class Meta:
        model = WorkGroup
        fields = (
            'uuid',
            'item_id',
            'course_id',
            'created_at',
            'members'
        )