__author__ = 'ad'

import mimetypes
import yaml
try:
    from collections import OrderedDict
except ImportError:
    # For python 2.6 additional package ordereddict should be installed
    from ordereddict import OrderedDict

from .raml_elements import ParserRamlInclude
from .constants import RAML_CONTENT_MIME_TYPES

class ValidationError(Exception):
    def __init__(self, validation_errors):
        self.errors = validation_errors

    def __str__(self):
        return repr(self.errors)

class UniqOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if key in self:
            raise ValidationError("Property already used: {0}".format(key))
        super(UniqOrderedDict, self).__setitem__(key, value)

# Bootstrapping: making able mimetypes package to recognize RAML and YAML
# file types
for mtype in RAML_CONTENT_MIME_TYPES:
    mimetypes.add_type(mtype, ".raml")
    mimetypes.add_type(mtype, ".yaml")

# making able mimetypes package to recognize JSON file type
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/json", ".schema")

# Configure PyYaml to recognize RAML additional constructions
yaml.add_representer(ParserRamlInclude, ParserRamlInclude.representer)
yaml.add_constructor(ParserRamlInclude.yaml_tag, ParserRamlInclude.loader)


# Configure representer/constructor to save the order of elements
# in a RAML/YAML structure
def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return UniqOrderedDict(loader.construct_pairs(node))


yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                     dict_constructor)
