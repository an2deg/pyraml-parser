__author__ = 'ad'

import contextlib
import urllib2
import mimetypes
import os.path
import urlparse
import yaml
from collections import OrderedDict

from raml_elements import ParserRamlInclude
from fields import String, Reference, List
from entities import (
    RamlRoot, RamlResource, RamlMethod, RamlBody,
    RamlResourceType, RamlTrait, RamlQueryParameter)
from constants import (
    RAML_SUPPORTED_FORMAT_VERSION, RAML_CONTENT_MIME_TYPES,
    RAML_VALID_PROTOCOLS)


__all__ = ["RamlException", "RamlNotFoundException", "RamlParseException",
           "ParseContext", "load", "parse"]

HTTP_METHODS = ("get", "post", "put", "delete", "head")


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
            if _is_mime_type_raml(file_type):
                new_relative_path = _calculate_new_relative_path(
                    self.relative_path, data.file_name)
                _included_ctx = ParseContext(
                    yaml.load(file_content),
                    new_relative_path)
                return _included_ctx._handle_load(_included_ctx.data)
            return file_content
        if isinstance(data, dict):
            for key, val in data.items():
                data[key] = self._handle_load(val)
            return data
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

    def get_string_property(self, property_name, required=False):
        property_value = self.get_property_with_schema(
            property_name,
            String(required=required))
        return property_value

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
        protocols = [urllib2.splittype(base_uri)[0]]
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
    root.title = context.get_string_property('title', True)

    root.baseUri = context.get_string_property('baseUri')
    root.protocols = parse_protocols(context, root.baseUri)

    root.version = context.get('version')
    root.mediaType = context.get_string_property('mediaType')
    root.schemas = context.get_property_with_schema(
        'schemas', RamlRoot.schemas)
    root.baseUriParameters = context.get_property_with_schema(
        "baseUriParameters", RamlRoot.baseUriParameters)

    root.documentation = context.get_property_with_schema(
        'documentation', RamlRoot.documentation)
    root.traits = parse_traits(
        context,
        RamlRoot.traits.field_name,
        root.mediaType)
    root.resourceTypes = parse_resource_type(context)

    resources = OrderedDict()
    for property_name in context.__iter__():
        if property_name.startswith("/"):
            resources[property_name] = parse_resource(
                context, property_name, root, root.mediaType)

    if resources > 0:
        root.resources = resources

    return root


def parse_resource(c, property_name, parent_object, global_media_type):
    """
    Parse and extract resource with name

    :param c:
    :type c: ParseContext

    :param parent_object: RamlRoot object or RamlResource object
    :type parent_object: RamlRoot or RamlResource

    :param property_name: resource name to extract
    :type property_name: str

    :return: RamlResource  or None
    :rtype: RamlResource
    """
    property_value = c.get(property_name)
    if not property_value:
        return None

    resource = RamlResource(uri=property_name)
    new_context = ParseContext(property_value, c.relative_path)
    resource.description = new_context.get_string_property("description")
    resource.displayName = new_context.get_string_property("displayName")
    resource.uriParameters = new_context.get_property_with_schema(
        "uriParameters", RamlResource.uriParameters)
    resource.baseUriParameters = new_context.get_property_with_schema(
        "baseUriParameters", RamlResource.baseUriParameters)

    if isinstance(parent_object, RamlResource):
        resource.parentResource = parent_object

    # Parse methods
    methods = OrderedDict()
    for _http_method in HTTP_METHODS:
        _method = new_context.get(_http_method)
        if _method:
            methods[_http_method] = parse_method(
                ParseContext(_method, c.relative_path),
                global_media_type)
        elif _http_method in new_context.data:
            # workaround: if _http_method is already in new_context.data than
            # it's marked as !!null
            methods[_http_method] = RamlMethod(notNull=True)
    if len(methods):
        resource.methods = methods

    # Parse resources
    resources = OrderedDict()
    for property_name in new_context.__iter__():
        if property_name.startswith("/"):
            resources[property_name] = parse_resource(
                new_context, property_name, resource, global_media_type)

    if resources > 0:
        resource.resources = resources

    return resource


def parse_resource_type(ctx):
    """
    Parse and extract resourceType

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
        lambda x, y: dict(x.items() + y.items()),
        resource_types)

    resource_types_context = ParseContext(resource_types, ctx.relative_path)
    resource_types = {}

    for rtype_name in resource_types_context:
        rtype_ctx = ParseContext(
            resource_types_context.get(rtype_name),
            resource_types_context.relative_path)

        rtype_obj = RamlResourceType()
        rtype_obj.type = rtype_ctx.get_string_property("type")
        rtype_obj.is_ = rtype_ctx.get_property_with_schema(
            "is", RamlResourceType.is_)

        # Parse methods
        methods = OrderedDict()
        for http_method in HTTP_METHODS:
            if http_method not in rtype_ctx.data:
                continue
            method_data = rtype_ctx.get(http_method)
            if method_data:
                _method_ctx = ParseContext(method_data, rtype_ctx.relative_path)
                method_data = _method_ctx.get_property_with_schema(
                    'traits', Reference(RamlTrait))
                raml_method = parse_method(
                    _method_ctx,
                    ctx.get_string_property('mediaType'))
            else:
                raml_method = RamlMethod(notNull=True)
            methods[http_method] = raml_method

        if methods:
            rtype_obj.methods = methods
        resource_types[rtype_name] = rtype_obj

    return resource_types


def parse_method(ctx, global_media_type):
    """
    Parse RAML method

    :param ctx: ParseContext object which contains RamlMethod
    :type ctx: ParseContext

    :param parent_object: RamlRoot, RamlResource or RamlResourceType object
    :type parent_object: RamlRoot or RamlResource or RamlResourceType

    :return: RamlMethod or None
    :rtype: RamlMethod
    """

    method = RamlMethod()

    method.description = ctx.get_string_property("description")
    method.body = parse_inline_body(
        ctx.get("body"), ctx.relative_path, global_media_type)
    method.baseUriParameters = ctx.get_property_with_schema(
        "baseUriParameters", RamlMethod.baseUriParameters)

    parsed_responses = parse_inline_body(
        ctx.get("responses"), ctx.relative_path, global_media_type)
    if parsed_responses:
        new_parsed_responses = OrderedDict()
        for resp_code, parsed_data in parsed_responses.iteritems():
            if resp_code == "<<":
                # Check for default code (equivalent of wildcard "*")
                new_parsed_responses.setdefault(parsed_data)
            else:
                # Otherwise response code should be numeric HTTP response code
                try:
                    resp_code = int(resp_code)
                except ValueError:
                    raise RamlParseException(
                        "Expected numeric HTTP response code in responses "
                        "but got {!r}".format(resp_code))
                new_parsed_responses[resp_code] = parsed_data
        method.responses = new_parsed_responses

    method.queryParameters = ctx.get_property_with_schema(
        "queryParameters", RamlMethod.queryParameters)

    return method


def parse_traits(c, property_name, global_media_type):
    """
    Parse and extract RAML trait from context field with name `property_name`

    :param c: parsing context
    :type c: ParseContext

    :param property_name: resource name to extract from context
    :type property_name: str

    :return: dict of (str,RamlTrait) or None
    :rtype: dict of (str,RamlTrait)
    """
    property_value = c.get(property_name)
    if not property_value:
        return None

    traits = {}

    # We got list of dict from c.get(property_name) so we need to iterate
    # over it
    for trait_raw_value in property_value:
        traits_context = ParseContext(trait_raw_value, c.relative_path)

        for trait_name in traits_context:
            new_context = ParseContext(
                traits_context.get(trait_name),
                traits_context.relative_path)
            trait = RamlTrait()

            for field_name, field_class in RamlTrait._structure.iteritems():
                # parse string fields
                if isinstance(field_class, String):
                    _new_value = new_context.get_string_property(
                        field_class.field_name)
                    setattr(trait, field_name, _new_value)
            trait.queryParameters = c.get_property_with_schema(
                RamlTrait.queryParameters.field_name,
                RamlTrait.queryParameters)
            trait.body = parse_body(
                ParseContext(new_context.get("body"), new_context.relative_path),
                global_media_type)
            trait.is_ = new_context.get_property_with_schema(
                RamlTrait.is_.field_name,
                RamlTrait.is_)
            trait.responses = c.get_property_with_schema(
                RamlTrait.responses.field_name,
                RamlTrait.responses)

            traits[trait_name] = trait

    return traits


def parse_map_of_entities(parser, context, relative_path, parent_resource):
    """

    :param parser: function which accepts 3 arguments: data, relative_path
        and parent_resource where entity is content
    :type parser: callable
    :param context: current parse context
    :type context: dict
    :param relative_path:
    :param parent_resource:
    :return:
    """
    res = OrderedDict()

    if context:
        for key, value in context.items():
            if value:
                res[key] = parser(value, relative_path, parent_resource)
            else:
                # workaround: if `key` is already in `context` than
                # it's marked as !!null
                res[key] = RamlMethod(notNull=True)

    return res


def parse_body(c, global_media_type):
    """
    Parse and extract resource with name

    :param c: ParseContext object which contains RamlBody
    :type c: ParseContext

    :return: RamlBody or None
    :rtype: RamlBody
    """
    if c.data is None:
        return None

    body = RamlBody()
    body.example = c.get_string_property("example")
    body.body = parse_inline_body(
        c.get("body"),
        c.relative_path,
        global_media_type)
    body.schema = c.get_string_property("schema")
    body.example = c.get_string_property("example")
    body.formParameters = c.get_property_with_schema(
        "formParameters", RamlBody.formParameters)
    body.headers = c.get_property_with_schema("headers", RamlBody.headers)

    return body


def parse_inline_body(data, relative_path, global_media_type):
    """
    Parse not null `body` inline property

    :param data: value of `body` property
    :type data: dict
    :param relative_path: relative path on filesystem to a RAML resource for
        handling `include` tags
    :type relative_path: str
    :return: OrderedDict of RamlBody or None
    :rtype: OrderedDict of RamlBody
    """
    if data is None:
        return None

    res = OrderedDict()

    # Data could be map of mime_type => body, http_code => body but also it
    # could be direct value of RamlBody with global mediaType
    # (grrr... so consistent)
    for field_name in RamlBody._structure:
        if field_name in data:
            # This is direct value of RamlBody
            parsed_data = parse_body(
                ParseContext(data, relative_path),
                global_media_type)
            res[global_media_type] = parsed_data
            return res

    for key, body_data in data.iteritems():
        if body_data:
            res[key] = parse_body(
                ParseContext(body_data, relative_path),
                global_media_type)
        else:
            # body marked as !!null
            res[key] = RamlBody(notNull=True)

    return res


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
    return urlparse.urlparse(uri).scheme


def _build_network_relative_path(url):
    p = urlparse.urlparse(url)
    parse_result = urlparse.ParseResult(
        p.scheme,
        p.netloc,
        os.path.dirname(p.path),
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
        raise RamlNotFoundException("No such file {} found".format(full_path))

    # Detect file type... we should able to parse raml, yaml, json, xml and read
    # all other content types as plain files
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
