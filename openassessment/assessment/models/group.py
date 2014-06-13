"""
Models for the Group Member Assessment API

"""
from django.db import models
from django.utils.timezone import now
from openassessment.assessment.models.base import Assessment

import logging
logger = logging.getLogger(__name__)


class GroupWorkflow(models.Model):
    """Tracks the progress of a student's evaluation of their group members.

    """
    student_id = models.CharField(max_length=40, db_index=True)
    item_id = models.CharField(max_length=128, db_index=True)
    course_id = models.CharField(max_length=40, db_index=True)
    project_uuid = models.CharField(max_length=128, db_index=True)
    created_at = models.DateTimeField(default=now, db_index=True)
    completed_at = models.DateTimeField(null=True, db_index=True)
    grading_completed_at = models.DateTimeField(null=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
        app_label = "assessment"


class GroupWorkflowItem(models.Model):
    """Represents an assessment associated with a particular workflow

    Created every time a submission is requested for peer assessment. The
    associated workflow represents the scorer of the given submission, and the
    assessment represents the completed assessment for this work item.

    """
    scorer = models.ForeignKey(GroupWorkflow, related_name='graded')
    author = models.ForeignKey(GroupWorkflow, related_name='graded_by')
    project_uuid = models.CharField(max_length=128, db_index=True)
    started_at = models.DateTimeField(default=now, db_index=True)
    assessment = models.ForeignKey(Assessment, null=True)

    # This WorkflowItem was used to determine the final score for the Workflow.
    scored = models.BooleanField(default=False)

    class Meta:
        ordering = ["started_at", "id"]
        app_label = "assessment"

