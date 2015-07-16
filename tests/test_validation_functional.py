from .base import SampleParseTestCase
from pyraml.model import ValidationError


class DefaultValuesTestCase(SampleParseTestCase):
    """ Test default values set while parsing. """

    def test_ramlnamedparameters_type_default_value(self):
        data = self.load('full-config.yaml')
        self.assertEqual(data.baseUriParameters['host'].type, 'string')


class ValidationTestCase(SampleParseTestCase):
    """ Test validation and invalid values processing stuff. """

    def test_invalid_named_parameter_type(self):
        args = ('invalid', 'invalid-named-parameter-type.yaml')
        expected = (
            "Got an unexpected value in the field `type`: "
            "foobar. Value should be one of:")
        self.assertRaisesRegexp(
            ValidationError, expected, self.load, *args)

    def test_invalid_protocol(self):
        args = ('invalid', 'invalid-protocol.yaml')
        expected = (
            "Got an unexpected value in the field `protocols`: "
            "IAmInvalidProtocol. Value should be one of:")
        self.assertRaisesRegexp(
            ValueError, expected, self.load, *args)

    def test_invalid_json_schema_parsed_as_string(self):
        data = self.load('invalid', 'invalid-schemas.yaml')
        self.assertEqual(
            data.schemas['invalid-json'].strip(),
            '{{"foo": "bar"[]}')

    def test_invalid_xml_schema_parsed_as_string(self):
        data = self.load('invalid', 'invalid-schemas.yaml')
        self.assertEqual(
            data.schemas['invalid-xml'].strip(),
            '<?xml version="1.0" encoding="ISO-8859-1" ?>')

    def test_invalid_double_title(self):
        args = ('invalid', 'invalid-double-title.yaml')
        expected = ("Property already used: title")
        self.assertRaisesRegexp(
            ValidationError, expected, self.load, *args)
