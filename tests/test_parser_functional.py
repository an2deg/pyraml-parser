from .base import SampleParseTestCase
from pyraml import entities

from mock import patch

try:
    from lxml.etree import _Element as XMLElement
except ImportError:
    from xml.etree.ElementTree import Element as XMLElement

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
        * securedBy (root)
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
        self.assertTrue(hasattr(data, 'securitySchemes'))
        self.assertTrue(hasattr(data, 'securedBy'))

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

    def test_root_schemas_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.schemas), 2)
        self.assertDictEqual(data.schemas['league-json'], {
            "$schema": "http://json-schema.org/draft-03/schema",
            "title": "League Schema",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string"
                },
                "name": {
                    "type": "string",
                    "required": True
                }
            }
        })
        self.assertIsInstance(data.schemas['league-xml'], XMLElement)
        self.assertSetEqual(
            set(data.schemas['league-xml'].items()), set([
                ('elementFormDefault', 'qualified'),
                ('targetNamespace', 'http://example.com/schemas/soccer')
            ]))

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

    def test_secured_by_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.securedBy), 3)
        oauth2, oauth1, null = data.securedBy
        self.assertIsNone(null)
        self.assertDictEqual(oauth2, {
            'oauth_2_0': {'scopes': ['foobar']}
        })
        self.assertEqual(oauth1, 'oauth_1_0')


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
    """ Test pasing of resources and all included structures. """

    def test_name_desc_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.resources), 3)
        # Order or resources is preserved
        self.assertListEqual(list(data.resources.keys()), ['/', '/media', '/tags'])
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

    def test_resource_baseuriparameters_parsed(self):
        data = self.load('full-config.yaml')
        mediaResource = data.resources['/media']
        self.assertEqual(len(mediaResource.baseUriParameters), 1)
        host = mediaResource.baseUriParameters['host']
        self.assertEqual(host.enum, ['api1'])
        self.assertIsNone(host.displayName)
        self.assertIsNone(host.description)
        self.assertIsNone(host.pattern)

    def test_method_uriparameters_parsed(self):
        data = self.load('full-config.yaml')
        head = data.resources['/media'].methods['head']
        self.assertEqual(len(head.baseUriParameters), 1)
        host = head.baseUriParameters['host']
        self.assertEqual(host.enum, ['api2'])
        self.assertIsNone(host.description)

    def test_method_description_parsed(self):
        data = self.load('full-config.yaml')
        get = data.resources['/media'].methods['get']
        self.assertEqual(get.description, 'retrieve media')
        head = data.resources['/media'].methods['head']
        self.assertIsNone(head.description)

    def test_method_headers_parsed(self):
        data = self.load('full-config.yaml')
        headers = data.resources['/media'].methods['get'].headers
        self.assertEqual(len(headers), 1)
        apikey = headers['Zencoder-Api-Key']
        self.assertEqual(apikey.displayName, 'Api key')
        self.assertEqual(apikey.description, 'Api key description')
        self.assertEqual(apikey.type, 'string')
        self.assertTrue(apikey.required)
        self.assertEqual(apikey.minLength, 10)
        self.assertEqual(apikey.maxLength, 10)
        self.assertEqual(apikey.example, '0123456789')

    def test_method_headers_not_provided(self):
        data = self.load('full-config.yaml')
        headers = data.resources['/media'].methods['head'].headers
        self.assertIsNone(headers)

    def test_method_protocols_parsed(self):
        data = self.load('full-config.yaml')
        head = data.resources['/'].methods['head']
        self.assertListEqual(head.protocols, ['HTTP'])

    def test_method_protocols_not_provided(self):
        data = self.load('full-config.yaml')
        head = data.resources['/media'].methods['head']
        self.assertIsNone(head.protocols)

    def test_method_queryparameters_parsed(self):
        data = self.load('full-config.yaml')
        params = data.resources['/media'].methods['get'].queryParameters
        self.assertEqual(len(params), 2)
        self.assertEqual(params['page'].displayName, 'Page')
        self.assertEqual(params['page'].type, 'integer')
        self.assertEqual(params['page'].default, 1)
        self.assertEqual(params['page'].minimum, 1)
        self.assertIsNone(params['page'].example)
        self.assertEqual(params['offset'].displayName, 'Offset')
        self.assertEqual(params['offset'].description, 'Offset value')
        self.assertEqual(params['offset'].type, 'integer')
        self.assertEqual(params['offset'].minimum, 0)
        self.assertEqual(params['offset'].example, 2)
        self.assertIsNone(params['offset'].required)

    def test_nested_resource_method_queryparameters_parsed(self):
        data = self.load('full-config.yaml')
        resource = data.resources['/media'].resources['/{mediaId}']
        params = resource.methods['get'].queryParameters
        self.assertEqual(len(params), 1)
        self.assertEqual(params['length'].displayName, 'length')
        self.assertEqual(params['length'].type, 'integer')

    def test_method_queryparameters_not_provided(self):
        data = self.load('full-config.yaml')
        params = data.resources['/media'].methods['head'].queryParameters
        self.assertIsNone(params)

    def test_method_body_notnull_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/media'].methods['get'].body
        self.assertTrue(body['text/xml'].notNull)
        self.assertIsNone(body['text/xml'].formParameters)

    def test_method_body_json_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/media'].methods['get'].body
        appjson = body['application/json']
        self.assertDictEqual(appjson.schema, {
            "$schema": "http://json-schema.org/draft-03/schema",
            "properties": {
                "input": {
                    "required": False,
                    "type": "string"
                }
            },
            "required": False,
            "type": "object"
        })
        self.assertEqual(appjson.example, '{ "input": "hola" }')
        self.assertIsNone(appjson.formParameters)

    def test_method_body_xml_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/'].methods['post'].body
        self.assertIsInstance(body['text/xml'].schema, XMLElement)
        self.assertEqual(body['text/xml'].schema.items(), [('bar', 'baz')])

    def test_method_body_named_schema_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/'].methods['post'].body
        self.assertEqual(body['application/json'].schema, 'league-json')

    def test_method_body_multipart_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/media'].methods['get'].body
        formParams = body['multipart/form-data'].formParameters
        self.assertEqual(len(formParams), 2)
        form1 = formParams['form-1']
        self.assertEqual(len(form1), 2)
        self.assertEqual(form1[0].displayName, 'form 1')
        self.assertEqual(form1[0].description, 'form 1 description')
        self.assertEqual(form1[0].type, 'number')
        self.assertTrue(form1[0].required)
        self.assertEqual(form1[0].minimum, 9.5)
        self.assertEqual(form1[0].maximum, 10.5)
        self.assertIsNone(form1[0].enum)
        self.assertEqual(form1[1].type, 'string')
        self.assertListEqual(form1[1].enum, ['one', 'two', 'three'])
        form2 = formParams['form-2']
        self.assertEqual(form2.type, 'boolean')
        self.assertTrue(form2.required)

    def test_method_body_form_urlencoded_parsed(self):
        data = self.load('full-config.yaml')
        body = data.resources['/media'].methods['get'].body
        formParams = body['application/x-www-form-urlencoded'].formParameters
        self.assertEqual(len(formParams), 2)
        form3 = formParams['form-3']
        self.assertEqual(form3.displayName, 'form 3')
        self.assertEqual(form3.type, 'number')
        form4 = formParams['form-4']
        self.assertEqual(form4.type, 'boolean')
        self.assertTrue(form4.required)

    def test_method_responses_desc_body_parsed(self):
        data = self.load('full-config.yaml')
        responses = data.resources['/media'].methods['get'].responses
        self.assertEqual(len(responses), 2)
        self.assertEqual(
            responses[200].description, 'regular success response')
        self.assertEqual(len(responses[200].body), 1)
        self.assertEqual(
            responses[200].body['application/json'].example,
            '{ "key": "value" }')
        self.assertEqual(
            responses[200].body['application/json'].schema,
            'league-json')
        self.assertEqual(
            responses[400].body['text/xml'].example,
            '<root>none</root>')
        self.assertTrue(responses[400].body['text/plain'].notNull)

    def test_method_responses_headers_parsed(self):
        data = self.load('full-config.yaml')
        responses = data.resources['/media'].methods['get'].responses
        headers = responses[200].headers
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers['one'].type, 'string')
        self.assertTrue(headers['one'].required)
        self.assertIsNone(headers['one'].maxLength)
        self.assertEqual(headers['two'].type, 'integer')
        self.assertIsNone(headers['two'].maxLength)
        self.assertIsNone(headers['two'].required)

    def test_resource_type_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(data.resources['/'].type, 'basic')
        self.assertDictEqual(data.resources['/media'].type, {
            'complex': {'value': 'complicated'}})

    def test_resource_and_method_traits_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(data.resources['/media'].is_, ['simple'])
        self.assertEqual(
            data.resources['/'].methods['head'].is_,
            ['simple', {'knotty': {'value': 'mingled'}}])

    def test_resource_secured_by_parsed(self):
        data = self.load('full-config.yaml')
        secured = data.resources['/'].securedBy
        self.assertEqual(len(secured), 3)
        oauth2, oauth1, null = secured
        self.assertIsNone(null)
        self.assertDictEqual(oauth2, {
            'oauth_2_0': {'scopes': ['comments']}
        })
        self.assertEqual(oauth1, 'oauth_1_0')

    def test_resource_method_secured_by_parsed(self):
        data = self.load('full-config.yaml')
        secured = data.resources['/'].methods['head'].securedBy
        self.assertEqual(len(secured), 2)
        oauth2, oauth1 = secured
        self.assertDictEqual(oauth2, {
            'oauth_2_0': {'scopes': ['more comments']}
        })
        self.assertEqual(oauth1, 'oauth_1_0')


class ResourceTypesParseTestCase(SampleParseTestCase):
    """ Test parsing of root resourceTypes """

    def test_simple_resourcetypes_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.resourceTypes), 3)
        self.assertIsNone(data.resourceTypes['basic'].description)
        self.assertEqual(
            data.resourceTypes['basic'].usage,
            'use this for basic operations')
        self.assertEqual(data.resourceTypes['complex'].description,
                         'complex desc')
        self.assertIsNone(data.resourceTypes['complex'].usage)

    def test_complex_resourcetypes_parsed(self):
        data = self.load('full-config.yaml')
        collection = data.resourceTypes['collection']
        self.assertIsInstance(collection, entities.RamlResourceType)
        self.assertEqual(collection.usage, 'Use when working with collections')
        self.assertEqual(
            collection.description,
            'Collection of available items.')
        self.assertEqual(len(collection.methods), 2)
        self.assertIn('get', collection.methods)
        post = collection.methods['post']
        self.assertEqual(post.description, 'Add a new item.')
        self.assertEqual(len(post.queryParameters), 1)
        token = post.queryParameters['access_token']
        self.assertEqual(token.description, 'The access token')
        self.assertEqual(token.example, 'AABBCCDD')
        self.assertTrue(token.required)
        self.assertEqual(token.type, 'string')
        self.assertEqual(len(post.body), 1)
        appjson = post.body['application/json']
        self.assertEqual(appjson.schema, '<<resourcePathName>>')
        self.assertEqual(appjson.example, '<<exampleItem>>')
        self.assertEqual(len(post.responses), 1)
        resp200 = post.responses[200]
        self.assertEqual(resp200.body['application/json'].example,
                         '{ "message": "Foo" }')


class TraitsParseTestCase(SampleParseTestCase):
    """ Test parsing of root traits """

    def test_no_traits_provided(self):
        data = self.load('null-elements.yaml')
        self.assertIsNone(data.traits)

    def test_simple_traits_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.traits), 3)
        self.assertListEqual(
            list(data.traits.keys()),
            ['simple', 'knotty', 'orderable'])
        self.assertEqual(data.traits['simple'].usage, 'simple trait')
        self.assertIsNone(data.traits['simple'].description)
        self.assertEqual(data.traits['knotty'].description, '<<value>> trait')
        self.assertIsNone(data.traits['knotty'].usage)
        orderable = data.traits['orderable']
        self.assertEqual(orderable.usage, 'Use to order items')
        self.assertEqual(orderable.description, 'Orderable trait desc')

    def test_traits_headers_parsed(self):
        data = self.load('full-config.yaml')
        xord = data.traits['orderable'].headers['X-Ordering']
        self.assertEqual(len(data.traits['orderable'].headers), 1)
        self.assertEqual(len(xord), 2)
        self.assertEqual(xord[0].type, 'string')
        self.assertListEqual(xord[0].enum, ['desc', 'asc'])
        self.assertEqual(xord[1].type, 'integer')
        self.assertEqual(xord[1].minimum, 0)
        self.assertEqual(xord[1].maximum, 1)

    def test_traits_queryparameters_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.traits['orderable'].queryParameters), 2)
        orderBy = data.traits['orderable'].queryParameters['orderBy']
        self.assertEqual(orderBy.description, 'Order by field: <<fieldsList>>')
        self.assertEqual(orderBy.type, 'string')
        self.assertFalse(orderBy.required)
        order = data.traits['orderable'].queryParameters['order']
        self.assertEqual(order.description, 'Order')
        self.assertListEqual(order.enum, ['desc', 'asc'])
        self.assertEqual(order.default, 'desc')
        self.assertTrue(order.required)

    def test_traits_responses_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.traits['orderable'].responses), 1)
        resp200 = data.traits['orderable'].responses[200]
        self.assertEqual(len(resp200.body), 1)
        self.assertEqual(resp200.body['application/json'].example,
                         '{ "message": "Bar" }')


class SecuritySchemesParseTestCase(SampleParseTestCase):
    """ Test parsing securitySchemes from root """

    def test_desc_type_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(len(data.securitySchemes), 2)
        self.assertEqual(
            data.securitySchemes['oauth_2_0'].description,
            'OAuth 2.0 for authenticating all API requests.')
        self.assertEqual(
            data.securitySchemes['oauth_2_0'].type,
            'OAuth 2.0')
        self.assertEqual(
            data.securitySchemes['oauth_1_0'].description,
            'OAuth 1.0 continues to be supported for all API requests')
        self.assertEqual(
            data.securitySchemes['oauth_1_0'].type,
            'OAuth 1.0')

    def test_settings_parsed(self):
        data = self.load('full-config.yaml')
        oauth1_settings = data.securitySchemes['oauth_1_0'].settings
        oauth2_settings = data.securitySchemes['oauth_2_0'].settings
        self.assertDictEqual(oauth1_settings, {
            'requestTokenUri': 'https://api.foobox.com/1/oauth/request_token',
            'authorizationUri': 'https://www.foobox.com/1/oauth/authorize',
            'tokenCredentialsUri': 'https://api.foobox.com/1/oauth/access_token',
        })
        self.assertDictEqual(oauth2_settings, {
            'authorizationUri': 'https://www.foobox.com/1/oauth2/authorize',
            'accessTokenUri': 'https://api.foobox.com/1/oauth2/token',
            'authorizationGrants': ['code', 'token'],
            'scopes': ['https://www.google.com/m8/feeds'],
        })

    def test_describedby_desc_parsed(self):
        data = self.load('full-config.yaml')
        self.assertEqual(
            data.securitySchemes['oauth_2_0'].describedBy.description,
            'foo')

    def test_describedby_baseuriparameters_parsed(self):
        data = self.load('full-config.yaml')
        params = data.securitySchemes['oauth_2_0'].describedBy.baseUriParameters
        self.assertEqual(len(params), 1)
        self.assertEqual(params['host'].enum, ['api3secured'])

    def test_describedby_queryparameters_parsed(self):
        data = self.load('full-config.yaml')
        params = data.securitySchemes['oauth_2_0'].describedBy.queryParameters
        self.assertEqual(len(params), 1)
        secured = params['isSecured']
        self.assertEqual(secured.type, 'integer')
        self.assertEqual(secured.displayName, 'Is secured')
        self.assertIsNone(secured.description)

    def test_describedby_body_parsed(self):
        data = self.load('full-config.yaml')
        body = data.securitySchemes['oauth_2_0'].describedBy.body
        self.assertEqual(len(body), 2)
        appjson = body['application/json']
        self.assertDictEqual(appjson.schema, {"foo": "bar"})
        self.assertEqual(appjson.example, '{ "input": "hola" }')
        self.assertIsNone(appjson.formParameters)
        xmlbody = body['text/xml']
        self.assertIsInstance(xmlbody.schema, XMLElement)
        self.assertEqual(xmlbody.schema.items(), [('buz', 'biz')])

    def test_describedby_headers_parsed(self):
        data = self.load('full-config.yaml')
        headers = data.securitySchemes['oauth_2_0'].describedBy.headers
        self.assertEqual(len(headers), 1)
        header = headers['Authorization']
        self.assertEqual(
            header.description,
            'Used to send a valid OAuth 2 access token.')
        self.assertEqual(header.type, 'string')
        self.assertIsNone(header.displayName)

    def test_describedby_responses_parsed(self):
        data = self.load('full-config.yaml')
        responses = data.securitySchemes['oauth_2_0'].describedBy.responses
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[403].description, 'Bad OAuth request')
        resp401 = responses[401]
        self.assertEqual(resp401.description, 'Bad or expired token')
        self.assertEqual(len(resp401.body), 1)
        self.assertEqual(resp401.body['application/json'].example,
                         '{ "message": "fail" }')
        self.assertIsNone(resp401.body['application/json'].schema)

    def test_describedby_not_provided(self):
        data = self.load('full-config.yaml')
        oauth1 = data.securitySchemes['oauth_1_0']
        self.assertIsNone(oauth1.describedBy.description)
        self.assertIsNone(oauth1.describedBy.body)
        self.assertIsNone(oauth1.describedBy.headers)
        self.assertIsNone(oauth1.describedBy.queryParameters)
        self.assertIsNone(oauth1.describedBy.responses)
        self.assertIsNone(oauth1.describedBy.baseUriParameters)
        self.assertIsNone(oauth1.describedBy.protocols)
