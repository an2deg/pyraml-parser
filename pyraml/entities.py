__author__ = 'ad'

from model import Model
from fields import String, Reference, Map, List, Bool, Int, Float, Or, Null


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
    type = Or(String(),
              Map(String(),
                  Map(String(), String())))


class RamlDocumentation(Model):
    """ The documentation property MUST be an array of documents.
    Each document MUST contain title and content attributes, both
    of which are REQUIRED. If the documentation property is specified,
    it MUST include at least one document.
    """
    title = String(required=True)
    content = String(required=True)


class RamlSchema(Model):
    """ The value of the schemas property is an array of maps;
    in each map, the keys are the schema name, and the values
    are schema definitions.
    """
    name = String()
    schema = String()

    @classmethod
    def from_json(self, json_object):
        """ Restructure input data
        from {name: schema}
        to   {name: name, schema: schema} form.
        """
        data = {
            'name': json_object.keys()[0],
            'schema': json_object.values()[0],
        }
        return super(RamlSchema, self).from_json(data)


class RamlNamedParameters(Model):
    """ http://raml.org/spec.html#named-parameters """
    name = String()
    description = String()
    example = Or(String(), Int(), Float())
    displayName = String()
    type = String()
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
    schema = String()
    example = String()
    notNull = Bool()
    formParameters = Map(
        String(),
        Or(Reference(RamlNamedParameters),
           List(Reference(RamlNamedParameters)))
    )
    body = Map(String(), Reference("pyraml.entities.RamlBody"))


class RamlResponse(Model):
    """ Responses MUST be a map of one or more HTTP status codes,
    where each status code itself is a map that describes that status
    code.
    """
    notNull = Bool()
    description = String()
    headers = Map(String(), Reference(RamlNamedParameters))
    body = Map(String(), Reference("pyraml.entities.RamlBody"))


class RamlTrait(Model):
    """ A trait is a partial method definition that, like a method,
    can provide method-level properties such as
    description, headers, query string parameters, and responses.
    """
    usage = String()
    description = String()
    headers = Map(String(), Reference(RamlNamedParameters))
    queryParameters = Map(String(), Reference(RamlNamedParameters))
    responses = Map(Int(), Reference(RamlResponse))


class RamlMethod(TraitedEntity, SecuredEntity, Model):
    """ http://raml.org/spec.html#methods """
    notNull = Bool()
    description = String()
    body = Map(String(), Reference(RamlBody))
    responses = Map(Int(), Reference(RamlResponse))
    queryParameters = Map(String(), Reference(RamlNamedParameters))
    baseUriParameters = Map(String(), Reference(RamlNamedParameters))
    headers = Map(String(), Reference(RamlNamedParameters))
    protocols = List(String())


class RamlResource(ResourceTypedEntity, TraitedEntity, SecuredEntity, Model):
    """ http://raml.org/spec.html#resources-and-nested-resources """
    displayName = String()
    description = String()
    parentResource = Reference("pyraml.entities.RamlResource")
    methods = Map(String(), Reference(RamlMethod))
    resources = Map(String(), Reference("pyraml.entities.RamlResource"))
    uriParameters = Map(String(), Reference(RamlNamedParameters))
    baseUriParameters = Map(String(), Reference(RamlNamedParameters))


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
    headers = Map(String(), Reference(RamlNamedParameters))
    queryParameters = Map(String(), Reference(RamlNamedParameters))
    responses = Map(Int(), Reference(RamlResponse))
    baseUriParameters = Map(String(), Reference(RamlNamedParameters))
    protocols = List(String())


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
    version = String()
    baseUri = String(required=True)
    protocols = List(String())
    mediaType = String()
    documentation = List(Reference(RamlDocumentation))
    traits = Map(String(), Reference(RamlTrait))
    resources = Map(String(), Reference(RamlResource))
    resourceTypes = Map(String(), Reference(RamlResourceType))
    schemas = List(Reference(RamlSchema))
    baseUriParameters = Map(String(), Reference(RamlNamedParameters))
    securitySchemes = Map(String(), Reference(RamlSecurityScheme))
