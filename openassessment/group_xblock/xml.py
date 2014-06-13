"""
Serialize and deserialize OpenAssessment XBlock content to/from XML.
"""
import lxml.etree as etree
import pytz
import defusedxml.ElementTree as safe_etree
from django.utils.translation import ugettext as _


class UpdateFromXmlError(Exception):
    """
    Error occurred while deserializing the Group XBlock content from XML.
    """
    pass


def _safe_get_text(element):
    """
    Retrieve the text from the element, safely handling empty elements.

    Args:
        element (lxml.etree.Element): The XML element.

    Returns:
        unicode
    """
    return unicode(element.text) if element.text is not None else u""


def serialize_content_to_xml(group_block, root):
    """
    Serialize the Group XBlock's content to XML.

    Args:
        oa_block (GroupBlock): The group block to serialize.
        root (etree.Element): The XML root node to update.

    Returns:
        etree.Element

    """
    root.tag = 'group'

    # Group displayed title
    title = etree.SubElement(root, 'title')
    title.text = unicode(group_block.title)

    # Group displayed prompt
    prompt = etree.SubElement(root, 'prompt')
    prompt.text = unicode(group_block.prompt)

    # Group associated location
    location = etree.SubElement(root, 'explicit-location')
    location.text = unicode(group_block.explicit_location)


def serialize_content(group_block):
    """
    Serialize the Group XBlock's content to an XML string.

    Args:
        group_block (GroupBlock): The group block to serialize.

    Returns:
        xml (unicode)
    """
    root = etree.Element('group')
    serialize_content_to_xml(group_block, root)

    # Return a UTF-8 representation of the XML
    return etree.tostring(root, pretty_print=True, encoding='unicode')


def update_from_xml(group_block, root):
    """
    Update the XBlock's content from an XML definition.

    We need to be strict about the XML we accept, to avoid setting
    the XBlock to an invalid state (which will then be persisted).

    Args:
        group_block (GroupBlock): The group block to update.
        root (lxml.etree.Element): The XML definition of the XBlock's content.

    Returns:
        GroupBlock

    Raises:
        UpdateFromXmlError: The XML definition is invalid or the XBlock could not be updated.
    """

    # Check that the root has the correct tag
    if root.tag != 'group':
        raise UpdateFromXmlError(_('Every group block must contain a "group" element.'))

    member_count = None
    if 'member_count' in root.attrib:
        member_count = root.attrib['member_count']

    # Retrieve the title
    title_el = root.find('title')
    if title_el is None:
        raise UpdateFromXmlError(_('Every group must contain a "title" element.'))
    else:
        title = _safe_get_text(title_el)

    prompt_el = root.find('prompt')
    if prompt_el is None:
        raise UpdateFromXmlError(_('Every group must contain a "prompt" element.'))
    else:
        prompt = _safe_get_text(prompt_el)

    explicit_location = None
    explicit_location_el = root.find('explicit-location')
    if explicit_location_el is not None:
        explicit_location = _safe_get_text(explicit_location_el)

    # If we've gotten this far, then we've successfully parsed the XML
    # and validated the contents.  At long last, we can safely update the XBlock.
    group_block.title = title
    group_block.prompt = prompt
    group_block.member_count = member_count
    group_block.explicit_location = explicit_location
    return group_block


def update_from_xml_str(group_block, xml, **kwargs):
    """
    Update from XML String via Studio

    Args:
        group_block (OpenAssessmentBlock): The open assessment block to update.
        xml (unicode): The XML definition of the XBlock's content.

    Returns:
        GroupBlock

    Raises:
        UpdateFromXmlError: The XML definition is invalid or the XBlock could not be updated.
    """
    # Parse the XML content definition
    # Use the defusedxml library implementation to avoid known security vulnerabilities in ElementTree:
    # http://docs.python.org/2/library/xml.html#xml-vulnerabilities
    try:
        root = safe_etree.fromstring(xml.encode('utf-8'))
    except (ValueError, safe_etree.ParseError):
        raise UpdateFromXmlError(_("An error occurred while parsing the XML content."))

    return update_from_xml(group_block, root)
