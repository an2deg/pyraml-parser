from .base import SampleParseTestCase
from pyraml import entities

from mock import patch


class RootParseTestCase(SampleParseTestCase):
    """ Test parsing of:

        * title
        * version
        * baseUri
        * baseUriParameters (root)
        * mediaType (root)
        * documentation
        * schemas
        * protocols (root)
    """
    def test_basic_root_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(data.title, 'Sample API')
        self.assertEqual(data.version, 'v1')
        self.assertEqual(data.baseUri,
                         'https://{host}.sample.com:{port}/{path}')
        self.assertEqual(data.mediaType, 'application/json')
        self.assertListEqual(data.protocols, ['HTTP', 'HTTPS'])
        self.assertTrue(hasattr(data, 'schemas'))
        self.assertTrue(hasattr(data, 'resourceTypes'))
        self.assertTrue(hasattr(data, 'traits'))
        self.assertTrue(hasattr(data, 'resources'))
        self.assertTrue(hasattr(data, 'baseUriParameters'))
        # self.assertTrue(hasattr(data, 'securitySchemes'))

    def test_root_baseuriparameters_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.baseUriParameters), 3)
        host = data.baseUriParameters['host']
        port = data.baseUriParameters['port']
        path = data.baseUriParameters['path']
        self.assertEqual(host.displayName, 'Host')
        self.assertEqual(host.description, 'host name')
        self.assertEqual(host.type, 'string')
        self.assertEqual(host.minLength, 5)
        self.assertEqual(host.maxLength, 10)
        self.assertEqual(host.pattern, '[a-z]*')
        self.assertIsNone(host.example)
        self.assertEqual(port.type, 'integer')
        self.assertEqual(port.minimum, 1025)
        self.assertEqual(port.maximum, 65535)
        self.assertEqual(port.example, 8090)
        self.assertEqual(port.default, 8080)
        self.assertEqual(port.required, True)
        self.assertIsNone(port.description)
        self.assertEqual(path.type, 'string')
        self.assertListEqual(path.enum, ['one', 'two', 'three'])

    def test_root_baseuriparameters_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.baseUriParameters)

    def test_documentation_parsed(self):
        data = self.load('full-config.yaml')
        docs = data.documentation
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].title, 'Home')
        self.assertEqual(docs[1].title, 'section')
        self.assertEqual(docs[1].content, 'section content')

    def test_schemas_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.schemas), 2)
        self.assertIsInstance(data.schemas[0], entities.RamlSchema)
        self.assertEqual(data.schemas[0].name, 'league-json')
        self.assertIn('"type": "object"', data.schemas[0].schema)
        self.assertIsInstance(data.schemas[1], entities.RamlSchema)
        self.assertEqual(data.schemas[1].name, 'league-xml')
        self.assertIn(
            '<?xml version="1.0" encoding="ISO-8859-1" ?>',
            data.schemas[1].schema)

    def test_schemas_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.schemas)

    def test_root_protocols_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertListEqual(data.protocols, ['HTTP'])
        data = self.load('numeric-api-version.yaml')
        self.assertListEqual(data.protocols, ['HTTPS'])

    def test_root_mediatype_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.mediaType, None)


class InclusionTestCase(SampleParseTestCase):
    """Test various cases of using !include."""

    def test_include_root_value(self):
        """ Test root value inclusion via !include.

        E.g.
            title: !include some/file/path/name.yaml
        """
        data = self.load('root-elements-includes.yaml')
        self.assertEqual(data.title, 'included title')
        docs = data.documentation
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].title, 'Home')
        self.assertEqual(
            docs[0].content,
            'Lorem ipsum dolor sit amet, consectetur adipisicing elit, '
            'sed do\neiusmod tempor incididunt ut labore et dolore '
            'magna...\n')
        self.assertEqual(docs[1].title, 'Section')
        self.assertEqual(docs[1].content, 'section content')

    def test_include_resource_type_sequence(self):
        data = self.load('include', 'include-resource-type-sequence.yaml')
        self.assertEqual(len(data.resourceTypes), 2)
        self.assertEqual(
            data.resourceTypes['simple'].methods['get'].description,
            'super')
        self.assertEqual(
            data.resourceTypes['complex'].methods['post'].description,
            'not super')
        self.assertIsNone(data.resourceTypes['simple'].methods['get'].notNull)
        self.assertIsNone(data.resourceTypes['complex'].methods['post'].notNull)
        self.assertTrue(data.resourceTypes['complex'].methods['put'].notNull)

    def test_include_sequence_item(self):
        data = self.load('include', 'include-sequence-item.yaml')
        self.assertEqual(len(data.resourceTypes), 1)
        self.assertEqual(
            data.resourceTypes['simple'].methods['get'].description,
            'super')
        self.assertEqual(data.documentation[0].title, 'section')
        self.assertEqual(data.documentation[0].content, 'section content')

    def test_include_resource_method_params(self):
        data = self.load('include', 'include-action.yaml')
        self.assertEqual(
            data.resources['/simple'].methods['get'].description,
            'get something')

    def test_include_txt_named_parameter_value(self):
        data = self.load('include', 'include-action.yaml')
        self.assertEqual(
            data.baseUriParameters['host'].description,
            'included title')

    def test_multi_level_inclusion(self):
        data = self.load('multi-level-inclusion.yaml')
        docs = data.documentation
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, 'Section')
        self.assertEqual(docs[0].content, 'included title')

    @patch('pyraml.parser._load_network_resource')
    def test_include_non_root_value_only_http(self, mock_load):
        mock_load.return_value = ('http inclusion data', 'text/plain')
        data = self.load('include', 'include-http-non-yaml.yaml')
        self.assertEqual(data.documentation[0].title, 'Home')
        self.assertEqual(
            data.documentation[0].content,
            'http inclusion data')
        mock_load.assert_called_once_with(
            'https://raw.github.com/mulesoft/mule/mule-3.x/README.md')

    def test_regression_include_body_example_json(self):
        """ https://github.com/an2deg/pyraml-parser/issues/4
        """
        data = self.load('include-body-example-json.yaml')
        responses = data.resources['/me'].methods['get'].responses[200]
        json_response = responses.body['application/json']
        self.assertEqual(json_response.example, '{"foo": "bar"}')


class ResourceParseTestCase(SampleParseTestCase):

    def test_name_desc_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.resources), 3)
        self.assertListEqual(data.resources.keys(), ['/', '/tags', '/media'])
        self.assertEqual(data.resources['/'].displayName, 'Root resource')
        self.assertEqual(
            data.resources['/'].description,
            'Root resource description')
        mediaIdResource = data.resources['/media'].resources['/{mediaId}']
        self.assertEqual(mediaIdResource.displayName, 'Media item')
        self.assertIsNone(mediaIdResource.description)

    def test_resource_uriparameters_parsed(self):
        data = self.load('full-config.yaml')
        mediaIdResource = data.resources['/media'].resources['/{mediaId}']
        self.assertEqual(len(mediaIdResource.uriParameters), 1)
        mediaIdParam = mediaIdResource.uriParameters['mediaId']
        self.assertEqual(mediaIdParam.type, 'string')
        self.assertEqual(mediaIdParam.maxLength, 10)
        self.assertIsNone(mediaIdParam.minLength)

    def test_method_uriparameters_parsed(self):
        data = self.load('full-config.yaml')
        head = data.resources['/media'].methods['head']
        self.assertEqual(len(head.baseUriParameters), 1)
        host = head.baseUriParameters['host']
        self.assertEqual(host.enum, ['api2'])
        self.assertIsNone(host.description)

    def test_baseuriparameters_parsed(self):
        data = self.load('full-config.yaml')
        mediaResource = data.resources['/media']
        self.assertEqual(len(mediaResource.baseUriParameters), 1)
        host = mediaResource.baseUriParameters['host']
        self.assertEqual(host.enum, ['api1'])
        self.assertIsNone(host.description)
        self.assertIsNone(host.displayName)
        self.assertIsNone(host.pattern)
