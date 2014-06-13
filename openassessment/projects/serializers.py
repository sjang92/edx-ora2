"""
Serializers for Group Projects and their parts.

"""
from rest_framework import serializers
from openassessment.projects.models import GroupProject, GroupProjectPart


class GroupProjectPartSerializer(serializers.ModelSerializer):
    """
    Represents a submission part of the Group Project
    """
    class Meta:
        model = GroupProjectPart
        fields = (
            'submission_uuid',
            'order_num',
            'created_at',
            'group_project'
        )


class GroupProjectSerializer(serializers.ModelSerializer):
    """
    Representation Group Project.

    """
    parts = GroupProjectPartSerializer(many=True, default=None, required=False)

    class Meta:
        model = GroupProject
        fields = (
            'uuid',
            'rep_uuid',
            'group_uuid',
            'item_id',
            'course_id',
            'created_at',
            'parts'
        )