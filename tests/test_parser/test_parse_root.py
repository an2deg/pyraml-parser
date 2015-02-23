from ..base import SampleParseTestCase


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
        self.assertTrue(hasattr(data, 'securitySchemes'))
        self.assertTrue(hasattr(data, 'resourceTypes'))
        self.assertTrue(hasattr(data, 'traits'))
        self.assertTrue(hasattr(data, 'resources'))

    def test_baseuriparameters_parsed(self):
        pass

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
        self.assertEqual(data.schemas[0].name, 'league-json')
        self.assertIn('"type": "object"', data.schemas[0].schema)
        self.assertEqual(data.schemas[1].name, 'league-xml')
        self.assertIn(
            '<?xml version="1.0" encoding="ISO-8859-1" ?>',
            data.schemas[1].schema)

    def test_protocols_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertListEqual(data.protocols, ['HTTP'])
        data = self.load('numeric-api-version.yaml')
        self.assertListEqual(data.protocols, ['HTTPS'])

    def test_root_mediatype_not_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.mediaType, None)
