__author__ = 'ad'

import itertools
import contextlib
import mimetypes
import os.path
import codecs
import yaml
import json
try:
    from collections import OrderedDict
except ImportError:
    # For python 2.6 additional package ordereddict should be installed
    from ordereddict import OrderedDict
from .constants import RAML_VALID_PROTOCOLS

from six.moves import urllib_parse as urlparse
from six.moves import urllib_request as urllib2
from six.moves import reduce

from .raml_elements import ParserRamlInclude
from .entities import (
    RamlRoot, RamlResource, RamlMethod, RamlResourceType)
from .constants import (
    RAML_SUPPORTED_FORMAT_VERSION, RAML_CONTENT_MIME_TYPES,
    HTTP_METHODS)


__all__ = ["RamlException", "RamlNotFoundException", "RamlParseException",
           "ParseContext", "load", "parse"]


class RamlException(Exception):
    pass


class RamlNotFoundException(RamlException):
    pass


class RamlParseException(RamlException):
    pass


class ParseContext(object):
    def __init__(self, data, relative_path):
        self.data = data
        self.relative_path = relative_path

    def _handle_load(self, data):
        """ Handle loading of included resources from ``data``.

        ``data`` can be of type:
            ParserRamlInclude:
                YAML/RAML resource: load its resources recursively
                Any other type: return value as a string
            dict: load values
            list: load items

        Otherwise return value as is.
        """
        if isinstance(data, ParserRamlInclude):
            file_content, file_type = self._load_resource(data.file_name)

            if _is_mime_type_json(file_type):
                file_content_dict = {}
                file_content_dict['fileName'] = data.file_name
                file_content_dict['content'] = file_content
                file_content = json.dumps(file_content_dict)

            if _is_mime_type_raml(file_type):
                new_relative_path = _calculate_new_relative_path(
                    self.relative_path, data.file_name)
                _included_ctx = ParseContext(
                    yaml.load(file_content),
                    new_relative_path)
                return _included_ctx._handle_load(_included_ctx.data)
            return file_content
        if isinstance(data, dict):
            new_data = OrderedDict(((key, self._handle_load(val)) for key, val in data.items()))
            return new_data
        if isinstance(data, list):
            return [self._handle_load(x) for x in data]
        return data

    def preload_included_resources(self):
        self.data = self._handle_load(self.data)

    def get(self, property_name):
        """
        Extract property with name `property_name` from context

        :param property_name: property name to extract
        :type property_name: str

        :return: object
        :rtype: object or None or dict
        """

        # Handle special case with null object
        if self.data is None:
            return None
        property_value = self.data.get(property_name)
        return property_value

    def __iter__(self):
        return iter(self.data)

    def get_property_with_schema(self, property_name, property_schema):
        property_value = self.get(property_name)
        return property_schema.to_python(property_value)

    def _load_resource(self, file_name):
        """
        Load RAML include from file_name.
        :param file_name: name of file to include
        :type file_name: str

        :return: 2 elements tuple: file content and file type
        :rtype: str,str
        """
        # Filename is a complete URI (http://example.com/foo.raml)
        if _is_network_resource(file_name):
            return _load_network_resource(file_name)
        # Filename relative to self network path
        elif _is_network_resource(self.relative_path):
            url = urlparse.urljoin(self.relative_path, file_name)
            return _load_network_resource(url)
        # Filename relative to self filename path
        else:
            full_path = os.path.join(self.relative_path, file_name)
            return _load_local_file(full_path)


def load(uri):
    """
    Load and parse RAML file

    :param uri: URL which points to a RAML resource or path to the RAML
        resource on local file system
    :type uri: str

    :return: RamlRoot object
    :rtype: pyraml.entities.RamlRoot
    """

    if _is_network_resource(uri):
        relative_path = _build_network_relative_path(uri)
        c, _ = _load_network_resource(uri)
    else:
        relative_path = os.path.dirname(uri)
        c, _ = _load_local_file(uri)

    return parse(c, relative_path)


def parse_protocols(ctx, base_uri=None):
    """ Parse ``protocols`` from a root context.

    If protocols are not provided in root, use baseUri protocol.
    """
    protocols = ctx.get_property_with_schema(
        'protocols', RamlRoot.protocols)
    if protocols is None and base_uri is not None:
        protocols = [base_uri.partition(':')[0]]
    if protocols:
        protocols = [p.upper() for p in protocols]
    return protocols


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
    context.preload_included_resources()

    root = RamlRoot(raml_version=raml_version)
    root.title = context.get_property_with_schema(
        'title', RamlRoot.title)
    root.baseUri = context.get_property_with_schema(
        'baseUri', RamlRoot.baseUri)
    root.protocols = parse_protocols(context, root.baseUri)
    root.version = context.get_property_with_schema(
        'version', RamlRoot.version)
    root.mediaType = context.get_property_with_schema(
        'mediaType', RamlRoot.mediaType)
    root.schemas = context.get_property_with_schema(
        'schemas', RamlRoot.schemas)
    root.baseUriParameters = context.get_property_with_schema(
        "baseUriParameters", RamlRoot.baseUriParameters)
    root.documentation = context.get_property_with_schema(
        'documentation', RamlRoot.documentation)
    root.traits = context.get_property_with_schema(
        'traits', RamlRoot.traits)
    root.securedBy = context.get_property_with_schema(
        'securedBy', RamlRoot.securedBy)
    root.securitySchemes = context.get_property_with_schema(
        'securitySchemes', RamlRoot.securitySchemes)
    root.resourceTypes = parse_resource_types(context)

    resources = OrderedDict()
    for property_name in context.__iter__():
        if property_name.startswith("/"):
            resources[property_name] = parse_resource(
                context, property_name, root)

    if resources:
        root.resources = resources

    return root


def parse_resource_methods(resource_ctx):
    """ Parse existing HTTP_METHODS from a resource_ctx. """
    methods = OrderedDict()
    for _http_method in HTTP_METHODS:
        if _http_method not in resource_ctx:
            continue
        _method = resource_ctx.get(_http_method)
        if _method:
            methods[_http_method] = parse_method(
                ParseContext(_method, resource_ctx.relative_path))
        else:
            methods[_http_method] = RamlMethod(notNull=True)
    return methods


def parse_resource(ctx, property_name, parent_object):
    """ Parse and extract resource with name.


    Parsing happens in a separate function(this) because resource's
    parsing requires additional actions to decide what to parse/not
    parse (when parsing methods).

    :param ctx:
    :type ctx: ParseContext

    :param parent_object: RamlRoot object or RamlResource object
    :type parent_object: RamlRoot or RamlResource

    :param property_name: resource name to extract
    :type property_name: str

    :return: RamlResource  or None
    :rtype: RamlResource
    """
    property_value = ctx.get(property_name)
    if not property_value:
        return None

    resource = RamlResource()
    resource_ctx = ParseContext(property_value, ctx.relative_path)
    resource.description = resource_ctx.get_property_with_schema(
        "description", RamlResource.description)
    resource.displayName = resource_ctx.get_property_with_schema(
        "displayName", RamlResource.displayName)
    resource.uriParameters = resource_ctx.get_property_with_schema(
        "uriParameters", RamlResource.uriParameters)
    resource.type = resource_ctx.get_property_with_schema(
        RamlResource.type_.field_name, RamlResource.type_)
    resource.is_ = resource_ctx.get_property_with_schema(
        RamlResource.is_.field_name, RamlResource.is_)
    resource.baseUriParameters = resource_ctx.get_property_with_schema(
        "baseUriParameters", RamlResource.baseUriParameters)
    resource.securedBy = resource_ctx.get_property_with_schema(
        'securedBy', RamlResource.securedBy)

    # Parse methods
    methods = parse_resource_methods(resource_ctx)
    if methods:
        resource.methods = methods

    # Parse resources
    resources = OrderedDict()
    for property_name in resource_ctx.__iter__():
        if property_name.startswith("/"):
            resources[property_name] = parse_resource(
                resource_ctx, property_name, resource)

    if resources:
        resource.resources = resources
    if isinstance(parent_object, RamlResource):
        resource.parentResource = parent_object
    return resource


def parse_resource_types(ctx):
    """ Parse and extract resourceType.

    Parsing happens in a separate function(this) because resourceTypes'
    parsing requires additional actions to decide what to parse/not
    parse (when parsing methods).

    :param ctx: ParseContext object
    :type ctx: ParseContext

    :return: RamlResource  or None
    :rtype: RamlResource
    """

    resource_types = ctx.get('resourceTypes')
    if not resource_types:
        return None

    if isinstance(resource_types, ParseContext):
        resource_types = resource_types.data
    resource_types = reduce(
        lambda x, y: dict(itertools.chain(x.items(), y.items())),
        resource_types)

    resource_types_context = ParseContext(resource_types, ctx.relative_path)
    resource_types = {}

    for rtype_name in resource_types_context:
        rtype_ctx = ParseContext(
            resource_types_context.get(rtype_name),
            resource_types_context.relative_path)

        rtype_obj = RamlResourceType()
        rtype_obj.description = rtype_ctx.get_property_with_schema(
            "description", RamlResourceType.description)
        rtype_obj.usage = rtype_ctx.get_property_with_schema(
            "usage", RamlResourceType.description)

        methods = parse_resource_methods(rtype_ctx)
        if methods:
            rtype_obj.methods = methods
        resource_types[rtype_name] = rtype_obj

    return resource_types


def parse_method(ctx):
    """ Parse RAML resource method.

    Parsing happens in a separate function(here) because of need to
    parse ``is`` key as ``is_`` field.

    :param ctx: ParseContext object which contains RamlMethod
    :type ctx: ParseContext

    :param parent_object: RamlRoot, RamlResource or RamlResourceType object
    :type parent_object: RamlRoot or RamlResource or RamlResourceType

    :return: RamlMethod or None
    :rtype: RamlMethod
    """

    method = RamlMethod()
    method.description = ctx.get_property_with_schema(
        "description", RamlMethod.description)
    method.body = ctx.get_property_with_schema("body", RamlMethod.body)
    method.baseUriParameters = ctx.get_property_with_schema(
        "baseUriParameters", RamlMethod.baseUriParameters)
    method.headers = ctx.get_property_with_schema(
        "headers", RamlMethod.headers)
    method.protocols = ctx.get_property_with_schema(
        "protocols", RamlMethod.protocols)
    method.responses = ctx.get_property_with_schema(
        "responses", RamlMethod.responses)
    method.is_ = ctx.get_property_with_schema(
        RamlMethod.is_.field_name, RamlMethod.is_)
    method.queryParameters = ctx.get_property_with_schema(
        "queryParameters", RamlMethod.queryParameters)
    method.securedBy = ctx.get_property_with_schema(
        'securedBy', RamlMethod.securedBy)
    return method


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
            raise RamlParseException("Unsupported format of RAML file",
                                     header_tuple[1])

        return header_tuple[1]
    except ValueError:
        raise RamlParseException("Invalid RAML format version", header_tuple[1])


def _is_mime_type_raml(mime_type):
    return mime_type.lower() in RAML_CONTENT_MIME_TYPES


def _is_mime_type_json(mime_type):
    return mime_type.lower() == "application/json"


def _is_mime_type_xml(mime_type):
    return mime_type.lower() == "application/xml"


def _is_network_resource(uri):
    return urlparse.urlparse(uri).scheme.upper() in RAML_VALID_PROTOCOLS


def _build_network_relative_path(url):
    p = urlparse.urlparse(url)
    parse_result = urlparse.ParseResult(
        p.scheme,
        p.netloc,
        os.path.dirname(p.path) + '/',
        '', '', '')
    return urlparse.urlunparse(parse_result)


def _calculate_new_relative_path(base, uri):
    if _is_network_resource(base):
        return _build_network_relative_path(urlparse.urljoin(base, uri))
    else:
        return os.path.dirname(os.path.join(base, uri))


def _load_local_file(full_path):
    # include locates at local file system
    if not os.path.exists(full_path):
        raise RamlNotFoundException("No such file {0} found".format(full_path))

    # Detect file type... we should able to parse raml, yaml, json, xml and read
    # all other content types as plain files
    mime_type = mimetypes.guess_type(full_path)[0]
    if mime_type is None:
        mime_type = "text/plain"

    with contextlib.closing(codecs.open(full_path, 'r', 'utf-8')) as f:
        return f.read(), mime_type


def _load_network_resource(url):
    with contextlib.closing(urllib2.urlopen(url, timeout=60.0)) as f:
        # We fully rely of mime type to remote server b/c according
        # of specs it MUST support RAML mime
        mime_type = f.headers.get('Content-Type')
        return f.read(), mime_type
