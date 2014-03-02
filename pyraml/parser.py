__author__ = 'ad'

import contextlib
import urllib2
import mimetypes
import json
import os.path
import lxml
import urlparse
import yaml

from raml_elements import ParserRamlInclude, ParserRamlNotNull
from entities import RamlRoot, RamlDocumentation, RamlResource, RamlTrait
from constants import RAML_SUPPORTED_FORMAT_VERSION, RAML_VALID_PROTOCOLS, RAML_CONTENT_MIME_TYPES
import bootstrap

class RamlException(StandardError):
    pass


class RamlNotFoundException(RamlException):
    pass


class RamlParseException(RamlException):
    pass


class ParseContext(object):
    def __init__(self, data, relative_path):
        self.data = data
        self.relative_path = relative_path

    def get(self, property_name):
        return self.data.get(property_name)

    def iter(self):
        return iter(self.data)

    def get_string_property(self, property_name, required=False):
        property_value = self.get(property_name)
        if not property_value:
            if required:
                raise RamlParseException("Property `{}` is required".format(property_name))

            return None

        if isinstance(property_value, ParserRamlInclude):
            property_value, _ = self._load_include(property_value.file_name)

         # version should be string but if version specified as "0.1" yaml package recognized
        # it as float, so we should handle this situation
        if isinstance(property_value, (int, float)):
            property_value = unicode(property_value)

        if not isinstance(property_value, basestring):
            raise RamlParseException("Property `{}` must be string".format(property_name))

        return property_value

    def get_list_property(self, property_name, target_field):
        """
        Parse and extract list property

        :param property_name: property name to extract
        :type property_name: str

        :param target_field: entity class
        :type target_field: pyraml.fields.BaseField

        :return: list of target_class  or None
        :rtype: list
        """
        property_value = self.get(property_name)
        if not property_value:
            return None

        # documentation: !include include/include-documentation.yaml
        if isinstance(property_value, ParserRamlInclude):
            property_value = list(self._load_raml_include(property_value.file_name).iter())

        if not isinstance(property_value, list):
            raise RamlParseException("Property `{}` must be list of objects".format(property_name))

        return target_field.to_python(property_value)

    def get_map_property(self, property_name, target_class):
        """
        Parse and extract list property

        :param property_name: property name to extract
        :type property_name: str

        :param target_class: entity class
        :type target_class: class

        :return: list of target_class  or None
        :rtype: list
        """
        property_value = self.get(property_name)
        if not property_value:
            return None

        # documentation: !include include/include-documentation.yaml
        if isinstance(property_value, ParserRamlInclude):
            property_value = list(self._load_raml_include(property_value.file_name).iter())

        if not isinstance(property_value, list):
            raise RamlParseException("Property `{}` must be list of objects".format(property_name))

        res = []
        for row in property_value:
            if not isinstance(row, dict):
                raise RamlParseException("Property `{}` must be list of objects".format(property_name))
            row_context = ParseContext(row, self.relative_path)

            doc = target_class()
            for field_name in row:
                setattr(doc, field_name, row_context.get_string_property(field_name))

            res.append(doc)

        return res

    def _load_include(self, file_name):
        """
        Load RAML include from file_name.
        :param file_name: name of file to include
        :type file_name: str

        :return: 2 elements tuple: file content and file type
        :rtype: str,str
        """

        if not _is_network_resource(self.relative_path):
            full_path = os.path.join(self.relative_path, file_name)
            return _load_local_file(full_path)
        else:
            url = urlparse.urljoin(self.relative_path, file_name)
            return _load_network_resource(url)

    def _load_raml_include(self, file_name):
        c, file_type = self._load_include(file_name)
        if not _is_mime_type_raml(file_type):
            raise RamlParseException("Include in property `documentation` expected to be RAML or YAML")

        # recalculate relative_path
        relative_path = _calculate_new_relative_path(self.relative_path, file_name)
        return ParseContext(yaml.load(c), relative_path)


def load(uri):
    """
    Load and parse RAML file

    :param uri:
    :type uri: str

    :return:
    """

    if _is_network_resource(uri):
        relative_path = _build_network_relative_path(uri)
        c, _ = _load_network_resource(uri)
    else:
        relative_path = os.path.dirname(uri)
        c, _ = _load_local_file(uri)

    return parse(c, relative_path)

def parse(c, relative_path):
    """
    Parse RAML file

    :param c: file content
    :type c: str
    :return:
    """

    # Read RAML header
    first_line, c = c.split('\n', 1)
    raml_version = _validate_raml_header(first_line)

    context = ParseContext(yaml.load(c), relative_path)

    root = RamlRoot(raml_version=raml_version)
    root.title = context.get_string_property('title', True)

    root.baseUri = context.get_string_property('baseUri')
    root.version = context.get_string_property('version')
    root.mediaType = context.get_string_property('mediaType')
    #root.protocols = _parse_raml_protocols(context)

    root.documentation = context.get_list_property('documentation',  RamlRoot._structure['documentation'])
    root.traits = context.get_list_property('traits', RamlRoot._structure['traits'])
    #root.resourceTypes = context.get_list_property('resourceTypes', RamlResource)
    #root.schemas = context.get_list_property('schemas')

    return root


def parse_non_root(c, relative_path):
    raw_content = yaml.load(c)


def _validate_raml_header(line):
    """
    Parse header of RAML file and ensure than we can work with it

    :param line: RAML header
    :type line: str

    :return: RAML format string
    :rtype: str

    :raise RamlParseException: in case of parsing errors
    """

    # Line should look like "#%RAML 0.8". Split it by whitespace and validate
    header_tuple = line.split()
    if len(header_tuple) != 2:
        raise RamlParseException("Invalid format of RAML header")

    if header_tuple[0] != "#%RAML":
        raise RamlParseException("Unable to found RAML header")

    try:
        # Extract first 2 numbers from format version, e.g. "0.8.2" -> "0.8"
        major_format_version = ".".join(header_tuple[1].split(".")[:2])

        if float(major_format_version) > RAML_SUPPORTED_FORMAT_VERSION:
            raise RamlParseException("Unsupported format of RAML file", header_tuple[1])

        return header_tuple[1]
    except ValueError:
        raise RamlParseException("Invalid RAML format version", header_tuple[1])


def _is_mime_type_raml(mime_type):
    return mime_type.lower() in ["text/yaml", "application/raml+yaml",
                                 "text/x-yaml", "application/yaml", "application/x-yaml"]


def _is_mime_type_json(mime_type):
    return mime_type.lower() == "application/json"


def _is_mime_type_xml(mime_type):
    return mime_type.lower() == "application/xml"


def _is_network_resource(uri):
    return urlparse.urlparse(uri).scheme


def _build_network_relative_path(url):
    p = urlparse.urlparse(url)
    return urlparse.urlunparse(urlparse.ParseResult(p.scheme, p.netloc, os.path.dirname(p.path), '', '', ''))

def _calculate_new_relative_path(base, uri):
    if _is_network_resource(base):
        return _build_network_relative_path(urlparse.urljoin(base, uri))
    else:
        return os.path.dirname(os.path.join(base, uri))

def _load_local_file(full_path):
     # include locates at local file system
    if not os.path.exists(full_path):
        raise RamlNotFoundException("No such file {} found".format(full_path))

    # detect file type... we should able to parse raml, yaml, json, xml and read all other content types as plain
    # files
    mime_type = mimetypes.guess_type(full_path)[0]
    if mime_type is None:
        mime_type = "text/plain"

    with contextlib.closing(open(full_path, 'rU')) as f:
        return f.read(), mime_type


def _load_network_resource(url):
    with contextlib.closing(urllib2.urlopen(url, timeout=60.0)) as f:
        # We fully rely of mime type to remote server b/c according
        # of specs it MUST support RAML mime
        mime_type = f.headers.gettype()
        return f.read(), mime_type

def _parse_raml_version(content):
    """
    Get optional property `version` and make sure than it is string.
    If not such property exists function returns None

    :return: string - property value or None
    :rtype : basestring or None
    """

    property_value = content.get('version')
    if not property_value:
        return None

    # version should be string but if version specified as "0.1" yaml package recognized
    # it as float, so we should handle this situation
    if not isinstance(property_value, (basestring, float)):
        raise RamlParseException("Property `version` must be string")

    if isinstance(property_value, float):
        res = str(property_value)

    return property_value


def _parse_raml_protocols(content):
    """
    Get optional property `protocols` and make sure than it is list of strings.
    If not such property exists function returns None

    :return: list of string - property value or None
    :rtype : list str or None
    """
    if not content.get('protocols'):
        return None

    res = content['protocols']

    # The protocols property MUST be an array of strings, of values "HTTP" and/or "HTTPS".
    if not isinstance(res, list):
        raise RamlParseException("Property `protocols` must be array of strings")

    invalid_protocols = set(res).difference(RAML_VALID_PROTOCOLS)
    if invalid_protocols:
        raise RamlParseException("Property `protocols` contains invalid value", invalid_protocols)

    return res
