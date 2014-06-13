from django.test import TestCase
from openassessment.projects import api as project_api
from openassessment.groups import api as group_api

STUDENT_ITEM = dict(
    student_id="Tim",
    course_id="Demo_Course",
    item_id="item_one",
    item_type="Peer_Submission",
)


class TestGroupProjectsApi(TestCase):
    """
    Testing Group Projects
    """

    def test_create_project(self):
        group = group_api.create_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com")
        project = project_api.create_group_project(STUDENT_ITEM)
        self.assertIsNotNone(project)
        self.assertEquals(group['uuid'], project['group_uuid']),
        self.assertEquals(STUDENT_ITEM['course_id'], project['course_id'])
        self.assertEquals(0, len(project['parts']))

    def test_get_project(self):
        group = group_api.create_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com")
        created_project = project_api.create_group_project(STUDENT_ITEM)
        retrieved_project = project_api.get_group_project(STUDENT_ITEM)
        self.assertEquals(created_project, retrieved_project)

    def test_submit_project_part(self):
        group = group_api.create_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com")
        project_api.create_group_project(STUDENT_ITEM)
        part_one = project_api.submit_project_part(STUDENT_ITEM, 0, "Foobar")
        part_two = project_api.submit_project_part(STUDENT_ITEM, 1, "Bizbaz")
        project = project_api.get_group_project(STUDENT_ITEM)
        self.assertEquals(2, len(project['parts']))
        self.assertEquals(project['parts'][0]['submission_uuid'], part_one['submission_uuid'])
        self.assertEquals(project['parts'][1]['submission_uuid'], part_two['submission_uuid'])
