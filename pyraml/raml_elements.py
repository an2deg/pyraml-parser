__author__ = 'ad'

import yaml
from . import ValidationError

try:
    from collections import OrderedDict
except ImportError:
    # For python 2.6 additional package ordereddict should be installed
    from ordereddict import OrderedDict


class ParserRamlInclude(yaml.YAMLObject):
    """Teach PyYAML about the `!include` tag

    Usage in .yaml:
        test: !include foo.yml
    Will expand to:
        test:
          foo: bar
    If the contents of the foo.yml file are:
        foo: bar

    This class will be found by PyYAML with inspection magic, because it
    extends the yaml.YAMLObject class.
    """

    yaml_tag = u'!include'
    # we're using SafeLoader, this class needs to be explicitly allowed
    yaml_loader = yaml.SafeLoader

    def __init__(self, file_name):
        self.file_name = file_name

    @classmethod
    def from_yaml(cls, loader, node):
        value = loader.construct_scalar(node)
        return cls(value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, u' ' + data.file_name)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.file_name)


class UniqueOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if key in self:
            raise ValidationError("Property already used: {0}".format(key))
        super(UniqueOrderedDict, self).__setitem__(key, value)

class ParserRamlDict(yaml.YAMLObject, UniqueOrderedDict):
    """Teach PyYAML to preserve dict (map) key order

    Uses OrderedDict with unique key values to preserve order.
    """

    yaml_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
    # we're using SafeLoader, this class needs to be explicitly allowed
    yaml_loader = yaml.SafeLoader

    @classmethod
    def from_yaml(cls, loader, node):
        value = loader.construct_pairs(node)
        return UniqueOrderedDict(value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_dict(data.iteritems())
