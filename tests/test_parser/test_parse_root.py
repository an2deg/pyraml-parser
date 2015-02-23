from ..base import SampleParseTestCase
from pyraml import entities


class RootParseTestCase(SampleParseTestCase):

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
        self.assertTrue(hasattr(data, 'securitySchemes'))

    def test_baseuriparameters_parsed(self):
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

    def test_baseuriparameters_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.baseUriParameters)

    def test_documentation_parsed(self):
        data = self.load('full-config.yaml')
        docs = data.documentation
        self.assertEqual(len(docs), 4)
        self.assertEqual(docs[1].title, 'section')
        self.assertEqual(docs[1].content, 'section content')
        self.assertIsNone(docs[2].title, None)
        self.assertEqual(docs[2].content, 'content without title')
        self.assertEqual(docs[3].title, 'title without content')
        self.assertIsNone(docs[3].content, None)

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

    def test_protocols_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertListEqual(data.protocols, ['HTTP'])
        data = self.load('numeric-api-version.yaml')
        self.assertListEqual(data.protocols, ['HTTPS'])

    def test_root_mediatype_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.mediaType, None)
