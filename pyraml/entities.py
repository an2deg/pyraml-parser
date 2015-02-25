__author__ = 'ad'

from model import Model
from fields import String, Reference, Map, List, Bool, Int, Float, Or


class RamlDocumentation(Model):
    title = String(required=True)
    content = String(required=True)


class RamlSchema(Model):
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
    schema = String()
    example = String()
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


class RamlMethod(Model):
    notNull = Bool()
    description = String()
    body = Map(String(), Reference(RamlBody))
    responses = Map(Int(), Reference(RamlResponse))
    queryParameters = Map(String(), Reference(RamlNamedParameters))
    baseUriParameters = Map(String(), Reference(RamlNamedParameters))
    headers = Map(String(), Reference(RamlNamedParameters))
    protocols = List(String())
    is_ = List(
        Or(
            String(),
            Map(String(), Map(String(), String()))
        ),
        field_name="is")


class RamlResource(Model):
    displayName = String()
    description = String()
    is_ = List(
        Or(
            String(),
            Map(String(), Map(String(), String()))
        ),
        field_name="is")
    type = Or(
        String(),
        Map(String(),
            Map(String(), String())))
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


class RamlRoot(Model):
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
