__author__ = 'ad'

from .model import Model
from .fields import (
    String, Reference, Map, List, Bool, Int, Float, Or, Null,
    Choice, RamlNamedParametersMap, JSONData, XMLData)
from .constants import NAMED_PARAMETER_TYPES, RAML_VALID_PROTOCOLS


class SecuredEntity(object):
    # [foo, {bar: {baz: [buz]}}, null]
    securedBy = List(
        Or(String(),
           Map(String(),
               Map(String(), List(String()))),
           Null()))


class TraitedEntity(object):
    """ Represents entities that may have traits specified
    in ``is`` field.
    """
    is_ = List(
        Or(String(),
           Map(String(),
               Map(String(), String()))),
        field_name='is')


class ResourceTypedEntity(object):
    """ Represents entities that may have resourceTypes
    specified in ``type`` field.
    """
    type_ = Or(String(),
               Map(String(),
                   Map(String(), Or(String(), Int()))),
               field_name='type')


class RamlDocumentation(Model):
    """ The documentation property MUST be an array of documents.
    Each document MUST contain title and content attributes, both
    of which are REQUIRED. If the documentation property is specified,
    it MUST include at least one document.
    """
    title = String(required=True)
    content = String(required=True)


class RamlNamedParameters(Model):
    """ http://raml.org/spec.html#named-parameters """
    displayName = String()
    description = String()
    type = Choice(default='string', choices=NAMED_PARAMETER_TYPES)
    name = String()
    example = Or(String(), Int(), Float())
    enum = List(Or(String(), Float(), Int()))
    pattern = String()
    minLength = Int()
    maxLength = Int()
    repeat = Bool()
    required = Bool()
    default = Or(String(), Int(), Float())
    minimum = Or(Int(), Float())
    maximum = Or(Int(), Float())


class RamlQueryParameter(RamlNamedParameters):
    """ Kept for compatibility reasons. """
    pass


class RamlHeader(RamlNamedParameters):
    """ Kept for compatibility reasons. """
    pass


class RamlBody(Model):
    """ A method's body is defined in the body property as a hashmap,
    in which the key MUST be a valid media type.
    """
    schema = Or(JSONData(), XMLData(), String())
    example = Or(JSONData(), String())
    notNull = Bool()
    formParameters = RamlNamedParametersMap()


class RamlResponse(Model):
    """ Responses MUST be a map of one or more HTTP status codes,
    where each status code itself is a map that describes that status
    code.
    """
    notNull = Bool()
    description = String()
    headers = RamlNamedParametersMap()
    body = Map(String(), Reference("pyraml.entities.RamlBody"))


class RamlTrait(Model):
    """ A trait is a partial method definition that, like a method,
    can provide method-level properties such as
    description, headers, query string parameters, and responses.
    """
    usage = String()
    description = String()
    headers = RamlNamedParametersMap()
    queryParameters = RamlNamedParametersMap()
    responses = Map(Int(), Reference(RamlResponse))


class RamlMethod(TraitedEntity, SecuredEntity, Model):
    """ http://raml.org/spec.html#methods """
    notNull = Bool()
    description = String()
    body = Map(String(), Reference(RamlBody))
    responses = Map(Int(), Reference(RamlResponse))
    queryParameters = RamlNamedParametersMap()
    baseUriParameters = RamlNamedParametersMap()
    headers = RamlNamedParametersMap()
    protocols = List(Choice(
        field_name='protocols',
        choices=RAML_VALID_PROTOCOLS))


class RamlResource(ResourceTypedEntity, TraitedEntity, SecuredEntity, Model):
    """ http://raml.org/spec.html#resources-and-nested-resources """
    displayName = String()
    description = String()
    parentResource = Reference("pyraml.entities.RamlResource")
    methods = Map(String(), Reference(RamlMethod))
    resources = Map(String(), Reference("pyraml.entities.RamlResource"))
    uriParameters = RamlNamedParametersMap()
    baseUriParameters = RamlNamedParametersMap()

    def __repr__(self):
        res = self.__dict__.copy()
        res.pop('parentResource')  # Avoid Circular reference
        return res.__repr__()


class RamlResourceType(Model):
    """ A resource type is a partial resource definition that,
    like a resource, can specify a description and methods and
    their properties.
    """
    usage = String()
    description = String()
    methods = Map(String(), Reference(RamlMethod))


class RamlSecuritySchemeDescription(Model):
    """ The describedBy attribute MAY be used to apply a trait-like
    structure to a security scheme mechanism so as to extend the
    mechanism, such as specifying response codes, HTTP headers or
    custom documentation.
    """
    description = String()
    body = Map(String(), Reference(RamlBody))
    headers = RamlNamedParametersMap()
    queryParameters = RamlNamedParametersMap()
    responses = Map(Int(), Reference(RamlResponse))
    baseUriParameters = RamlNamedParametersMap()
    protocols = List(Choice(
        field_name='protocols',
        choices=RAML_VALID_PROTOCOLS))


class RamlSecurityScheme(Model):
    """ http://raml.org/spec.html#security """
    description = String()
    type = String()
    describedBy = Reference(RamlSecuritySchemeDescription)
    settings = Map(String(),
                   Or(String(),
                      List(String())))


class RamlRoot(SecuredEntity, Model):
    """ http://raml.org/spec.html#root-section """
    raml_version = String(required=True)
    title = String(required=True)
    version = Or(String(), Int(), Float())
    baseUri = String(required=True)
    protocols = List(Choice(
        field_name='protocols',
        choices=RAML_VALID_PROTOCOLS))
    mediaType = String()
    documentation = List(Reference(RamlDocumentation))
    traits = Map(String(), Reference(RamlTrait))
    resources = Map(String(), Reference(RamlResource))
    resourceTypes = Map(String(), Reference(RamlResourceType))
    schemas = Map(String(), Or(JSONData(), XMLData(), String()))
    baseUriParameters = RamlNamedParametersMap()
    securitySchemes = Map(String(), Reference(RamlSecurityScheme))
