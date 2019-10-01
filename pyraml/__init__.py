__author__ = 'ad'

import mimetypes
import yaml


from .constants import RAML_CONTENT_MIME_TYPES


class ValidationError(Exception):
    def __init__(self, validation_errors):
        self.errors = validation_errors

    def __str__(self):
        return repr(self.errors)


# Bootstrapping: making able mimetypes package to recognize RAML and YAML
# file types
for mtype in RAML_CONTENT_MIME_TYPES:
    mimetypes.add_type(mtype, ".raml")
    mimetypes.add_type(mtype, ".yaml")

# making able mimetypes package to recognize JSON file type
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/json", ".schema")
