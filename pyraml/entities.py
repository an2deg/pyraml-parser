__author__ = 'ad'

from cStringIO import StringIO
from model import Model
from fields import String, Reference, Map, List, Reference


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


class RamlBody(Model):
    schema = String()
    example = String()

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
    method = String()
    queryParameters = Map(String(), Reference(RamlQueryParameter))
    body = Reference(RamlBody)


class RamlRoot(Model):
    raml_version = String(required=True)
    title = String()
    version = String()
    baseUri = String()
    protocols = List(String())
    mediaType = String()
    documentation = List(Reference(RamlDocumentation))
    traits = Map(String(), Reference(RamlTrait))

    #def __init__(self, raml_version):
    #    self.raml_version = raml_version
    #    self.title = None
    #    self.version = None
    #    self.mediaType = None
    #    self.protocols = None
    #    self.baseUri = None
    #    self.documentation = None
    #    self.schemas = None
    #    self.resourceTypes = None
    #    self.traits = None
    #    self.securitySchemes = None
    #    self.resource = None
    #
    #def dumps(self):
    #    res = StringIO()
    #    res.write("#%RAML {}\n".format(self.raml_version))
    #    if self.title:
    #        res.write("title: {}\n".format(self.title))
    #    if self.version:
    #        res.write("version: {}\n".format(self.version))
    #    if self.mediaType:
    #        res.write("mediaType: {}")


class RamlResourceType(object):
    """
    resourceTypes:
      - collection:
          usage: This resourceType should be used for any collection of items
          description: The collection of <<resourcePathName>>
          get:
            description: Get all <<resourcePathName>>, optionally filtered
          post:
            description: Create a new <<resourcePathName | !singularize>>
    """

    def __init__(self):
        self.name = None
        self.usage = None
        self.description = None
        self.resourcePath = None
        self.resourcePathName = None
        self.mediaTypeExtension = None
        self.methods = None


class RamlResource(object):
    def __init__(self):
        self.displayName = None
        self.description = None
        self.uri = None
        self.parentResource = None
        self.uriParameters = None
        self.methods = None


class RamlMethod(RamlResource):
    def __init__(self):
        super(RamlMethod, self).__init__()