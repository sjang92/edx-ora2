# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WorkGroup'
        db.create_table('groups_workgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(db_index=True, unique=True, max_length=36, blank=True)),
            ('item_id', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
        ))
        db.send_create_signal('groups', ['WorkGroup'])

        # Adding model 'WorkGroupMember'
        db.create_table('groups_workgroupmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='members', to=orm['groups.WorkGroup'])),
            ('student_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('item_id', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('student_name', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('student_email', self.gf('django.db.models.fields.CharField')(max_length=120)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
        ))
        db.send_create_signal('groups', ['WorkGroupMember'])


    def backwards(self, orm):
        # Deleting model 'WorkGroup'
        db.delete_table('groups_workgroup')

        # Deleting model 'WorkGroupMember'
        db.delete_table('groups_workgroupmember')


    models = {
        'groups.workgroup': {
            'Meta': {'object_name': 'WorkGroup'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        'groups.workgroupmember': {
            'Meta': {'object_name': 'WorkGroupMember'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'members'", 'to': "orm['groups.WorkGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'student_email': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'student_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'student_name': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        }
    }

    complete_apps = ['groups']