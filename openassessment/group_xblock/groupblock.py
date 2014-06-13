"""An XBlock  for students to join work groups"""
import logging
import pkg_resources

import pytz

from django.template.context import Context
from django.template.loader import get_template
from webob import Response

from xblock.core import XBlock
from xblock.fields import Scope, String, Integer
from xblock.fragment import Fragment
from openassessment.groups.errors import WorkGroupError

from openassessment.group_xblock.xml import update_from_xml
from openassessment.xblock.lms_mixin import LmsCompatibilityMixin

from openassessment.groups import api


logger = logging.getLogger(__name__)


def load(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


class GroupBlock(XBlock, LmsCompatibilityMixin):

    member_count = Integer(
        default=2, scope=Scope.settings,
        help="The number of members per group."
    )

    title = String(
        default="Group Finder",
        scope=Scope.content,
        help="A title to display to a student (plain text)."
    )

    prompt = String(
        default="Enter your name and email to find a group.",
        scope=Scope.content,
        help="A prompt to display to a student (plain text)."
    )

    course_id = String(
        default=u"TestCourse",
        scope=Scope.content,
        help="The course_id associated with this prompt (until we can get it from runtime)."
    )

    explicit_location = String(
        default=None,
        scope=Scope.content,
        help="Explicit location this group is bound to. Typically an ORA2 project."
    )

    def get_student_item_dict(self):
        """Create a student_item_dict from our surrounding context.

        TODO: SHAMELESSLY COPIED FROM OPENASSESSMENT XBLOCK. REFACTOR LATER.

        See also: submissions.api for details.

        Returns:
            (dict): The student item associated with this XBlock instance. This
                includes the student id, item id, and course id.
        """

        item_id = self._serialize_opaque_key(self.scope_ids.usage_id)

        # This is not the real way course_ids should work, but this is a
        # temporary expediency for LMS integration
        if hasattr(self, "xmodule_runtime"):
            course_id = self._serialize_opaque_key(self.xmodule_runtime.course_id)  # pylint:disable=E1101
            student_id = self.xmodule_runtime.anonymous_student_id  # pylint:disable=E1101
        else:
            course_id = "edX/Enchantment_101/April_1"
            if self.scope_ids.user_id is None:
                student_id = None
            else:
                student_id = unicode(self.scope_ids.user_id)

        student_item_dict = dict(
            student_id=student_id,
            item_id=item_id,
            course_id=course_id,
            item_type='openassessment'
        )
        return student_item_dict

    def student_view(self, context=None):
        """Main view for displaying Group setup.

        Args:
            context: Not used for this view.

        Returns:
            (Fragment): The HTML Fragment for this XBlock

        """

        # All data we intend to pass to the front end.
        context_dict = {
            "title": self.title,
            "prompt": self.prompt,
        }

        template = get_template("groupblock/group_base.html")
        context = Context(context_dict)
        frag = Fragment(template.render(context))
        # TODO: Cheat further by using ORA2 styles
        frag.add_css(load("static/css/openassessment.css"))
        # TODO: reuse some handy JS from ORA2, but this should be refactored.
        frag.add_javascript(load("static/js/group_base.js"))
        frag.initialize_js('GroupBlock')
        return frag


    @XBlock.json_handler
    def join_group(self, data, suffix=''):
        """Join a group.

        Given a name and email address, attempt to join or create a group for
        a student.

        Args:
            data (dict): Data should contain two attributes: name and email.
                These values are used to create a new member in a new group.
            suffix (str): Not used in this handler.

        Returns:
            (tuple): Returns the status (boolean) of this request, the
                associated group to the student.

        """
        student_name = data['student_name']
        student_email = data['student_email']
        student_item_dict = self.get_student_item_dict()

        try:
            group = api.join_group(
                student_item_dict,
                student_name,
                student_email,
                self.member_count,
                project_location=self.explicit_location
            )
            if not group:
                group = api.create_group(
                    student_item_dict,
                    student_name,
                    student_email,
                    project_location=self.explicit_location
                )
        except WorkGroupError as err:
            return "fail", err.message

        return "success", group['uuid']

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench.

        These scenarios are only intended to be used for Workbench XBlock
        Development.

        """
        return [
            (
                "Group XBlock",
                load('static/xml/basic.xml')
            )
        ]

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """Instantiate XBlock object from runtime XML definition.

        Inherited by XBlock core.

        """
        block = runtime.construct_xblock_from_class(cls, keys)

        return update_from_xml(block, node)

    def _serialize_opaque_key(self, key):
        """
        Gracefully handle opaque keys, both before and after the transition.
        https://github.com/edx/edx-platform/wiki/Opaque-Keys

        Currently uses `to_deprecated_string()` to ensure that new keys
        are backwards-compatible with keys we store in ORA2 database models.

        Args:
            key (unicode or OpaqueKey subclass): The key to serialize.

        Returns:
            unicode

        """
        if hasattr(key, 'to_deprecated_string'):
            return key.to_deprecated_string()
        else:
            return unicode(key)