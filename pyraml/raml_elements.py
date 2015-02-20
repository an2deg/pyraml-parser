__author__ = 'ad'

import yaml


class ParserRamlInclude(yaml.YAMLObject):
    yaml_tag = u'!include'

    def __init__(self, file_name):
        self.file_name = file_name

    @staticmethod
    def loader(loader, node):
        value = loader.construct_scalar(node)
        return ParserRamlInclude(value)

    @staticmethod
    def representer(dumper, data):
        return dumper.represent_scalar(ParserRamlInclude.yaml_tag, u' ' + data)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.file_name)
