"""
Rudimentary Group Project models for defining a project, and its associated
group.
"""
import logging
from django.db import models
from django_extensions.db.fields import UUIDField
from django.utils.timezone import now


logger = logging.getLogger(__name__)


class GroupProject(models.Model):

    uuid = UUIDField(version=1, db_index=True, unique=True)
    rep_uuid = models.CharField(max_length=36, db_index=True, null=True)
    group_uuid = models.CharField(max_length=36, db_index=True)
    item_id = models.CharField(max_length=128, db_index=True)
    course_id = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(default=now, db_index=True)


class GroupProjectPart(models.Model):

    group_project = models.ForeignKey(GroupProject, related_name='parts')
    submission_uuid = models.CharField(max_length=255)
    order_num = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=now, db_index=True)