__author__ = 'ad'

from model import Model
from fields import String, Reference, Map, List, Bool, Int


class RamlDocumentation(Model):
    content = String()
    title = String()


class RamlSchema(Model):
    name = String()
    type = String()
    schema = String()
    example = String()


class RamlQueryParameter(Model):
    name = String()
    description = String()
    example = String()


class RamlHeader(Model):
    type = String()
    required = Bool()

class RamlBody(Model):
    schema = String()
    example = String()
    notNull = Bool()
    formParameters = Map(String(), Reference(RamlHeader))
    headers = Map(String(), Reference(RamlHeader))
    body = Map(String(), Reference("pyraml.entities.RamlBody"))

    @classmethod
    def from_json(cls, json_object):
        res = super(RamlBody, cls).from_json(json_object)

        return res


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
    method = String()
    queryParameters = Map(String(), Reference(RamlQueryParameter))
    body = Reference(RamlBody)


class RamlMethod(Model):
    notNull = Bool()
    description = String()
    body = Reference(RamlBody)
    responses = Map(Int(), Reference(RamlBody))


class RamlResource(Model):
    displayName = String()
    description = String()
    uri = String()
    parentResource = Reference("pyraml.entities.RamlResource")
    methods = Map(String(), Reference(RamlBody))
    resources = Map(String(), Reference("pyraml.entities.RamlResource"))


class RamlRoot(Model):
    raml_version = String(required=True)
    title = String()
    version = String()
    baseUri = String()
    protocols = List(String())
    mediaType = String()
    documentation = List(Reference(RamlDocumentation))
    traits = Map(String(), Reference(RamlTrait))
    resources = Map(String(), Reference(RamlResource))