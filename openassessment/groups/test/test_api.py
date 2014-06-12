from django.test import TestCase
from openassessment.groups import api

STUDENT_ITEM = dict(
    student_id="Tim",
    course_id="Demo_Course",
    item_id="item_one",
    item_type="Peer_Submission",
)


class TestWorkGroupApi(TestCase):
    """
    Testing Work Groups
    """

    def test_create_work_group(self):
        group = api.create_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com")
        self.assertIsNotNone(group)
        self.assertEquals(STUDENT_ITEM['course_id'], group['course_id'])

    def test_join_work_group(self):
        group = api.join_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com", 2)
        self.assertIsNone(group)
        group = api.create_group(STUDENT_ITEM, "Timmy", "tim@timtastic.com")

        bob = STUDENT_ITEM.copy()
        bob['student_id'] = "bob"
        group = api.join_group(bob, "Bobby", "bob@timtastic.com", 2)
        self.assertIsNotNone(group)
        self.assertEquals(STUDENT_ITEM['course_id'], group['course_id'])
        self.assertEquals(2, len(group['members']))

        get_group = api.get_group(bob)
        self.assertEquals(group, get_group)
