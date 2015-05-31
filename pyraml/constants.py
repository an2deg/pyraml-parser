__author__ = 'ad'

RAML_SUPPORTED_FORMAT_VERSION = 0.8
RAML_VALID_PROTOCOLS = set(['HTTP', 'HTTPS'])
RAML_CONTENT_MIME_TYPES = [
    'text/yaml',
    'application/raml+yaml',
    'text/x-yaml',
    'application/yaml',
    'application/x-yaml',
]
HTTP_METHODS = set([
    'connect', 'options', 'patch', 'trace',
    'get', 'post', 'put', 'delete', 'head',
])
NAMED_PARAMETER_TYPES = set([
    'string', 'number', 'integer',
    'date', 'boolean',  'file',
])
