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


class RamlQueryParameter(Model):
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


class RamlHeader(Model):
    type = String()
    required = Bool()


class RamlBody(Model):
    schema = String()
    example = String()
    notNull = Bool()
    formParameters = Map(
        String(),
        Or(Reference(RamlQueryParameter),
           List(Reference(RamlQueryParameter)))
    )
    headers = Map(String(), Reference(RamlHeader))
    body = Map(String(), Reference("pyraml.entities.RamlBody"))
    is_ = List(String(), field_name="is")


class RamlResponse(Model):
    schema = String()
    example = String()
    notNull = Bool()
    description = String()
    headers = Map(String(), Reference(RamlHeader))
    body = Reference("pyraml.entities.RamlBody")


class RamlTrait(Model):
    """
    traits:
      - secured:
          usage: Apply this to any method that needs to be secured
          description: Some requests require authentication.
          queryParameters:
            access_token:
              description: Access Token
              type: string
              example: ACCESS_TOKEN
              required: true
    """

    name = String()
    usage = String()
    description = String()
    displayName = String()
    responses = Map(Int(), Reference(RamlResponse))
    method = String()
    queryParameters = Map(String(), Reference(RamlQueryParameter))
    body = Reference(RamlBody)
    # Reference to another RamlTrait
    is_ = List(String(), field_name="is")


class RamlResourceType(Model):
    methods = Map(String(), Reference(RamlTrait))
    type = String()
    is_ = List(String(), field_name="is")


class RamlMethod(Model):
    """
    Example:
        get:
            description: ...
            headers:
                ....
            queryParameters:
                ...
            body:
                text/xml: !!null
                application/json:
                    schema: |
                        {
                            ....
                        }
            responses:
                200:
                    ....
                <<:
                    404:
                        description: not found

    """
    notNull = Bool()
    description = String()
    body = Map(String(), Reference(RamlBody))
    responses = Map(Int(), Reference(RamlBody))
    queryParameters = Map(String(), Reference(RamlQueryParameter))


class RamlResource(Model):
    displayName = String()
    description = String()
    uri = String()
    is_ = Reference(RamlTrait, field_name="is")
    type = Reference(RamlResourceType)
    parentResource = Reference("pyraml.entities.RamlResource")
    methods = Map(String(), Reference(RamlBody))
    resources = Map(String(), Reference("pyraml.entities.RamlResource"))


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
    protocols = List(String())
    baseUriParameters = Map(String(), Reference(RamlQueryParameter))
