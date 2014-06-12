"""
Rudimentary WorkGroup models for defining a group and its members.
"""
import logging
from django.db import models
from django_extensions.db.fields import UUIDField
from django.utils.timezone import now


logger = logging.getLogger(__name__)


class WorkGroup(models.Model):

    uuid = UUIDField(version=1, db_index=True, unique=True)
    item_id = models.CharField(max_length=128, db_index=True)
    course_id = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(default=now, db_index=True)


class WorkGroupMember(models.Model):

    group = models.ForeignKey(WorkGroup, related_name='members')
    student_id = models.CharField(max_length=40, db_index=True)
    item_id = models.CharField(max_length=128, db_index=True)
    course_id = models.CharField(max_length=40, db_index=True)
    student_name = models.CharField(max_length=120)
    student_email = models.CharField(max_length=120)
    created_at = models.DateTimeField(default=now, db_index=True)