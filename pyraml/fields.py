__author__ = 'ad'

import six
import json
from abc import ABCMeta
try:
    from collections import OrderedDict
except ImportError:
    # For python 2.6 additional package ordereddict should be installed
    from ordereddict import OrderedDict

try:
    from lxml.etree import fromstring as parse_xml_string
    from lxml.etree import _Element as XMLElement
except ImportError:
    from xml.etree.ElementTree import fromstring as parse_xml_string
    from xml.etree.ElementTree import Element as XMLElement

@six.add_metaclass(ABCMeta)
class BaseField(object):
    def __init__(self, required=False, field_name=None, default=None):
        super(BaseField, self).__init__()
        self.required = required
        self.field_name = field_name
        self.default = default

    def check_default_value(self, value):
        if value is None and self.default is not None:
            value = self.default
        return value

    def validate(self, value):
        """ Validate ``value``

        :raise ValueError: in case of validation errors
        """
        if value is None and self.required:
            raise ValueError(
                "Missed value for the required field: {0}".format(
                    self.field_name))

    def from_python(self, value):
        """
        Do serialization steps on `value`
        """
        return value

    def to_python(self, value):
        """
        Convert JSON representation of an object ``value`` to python
        representation. If not overriden, this method returns results
        of call to self.validate.
        """
        value = self.check_default_value(value)
        self.validate(value)
        return value


class Null(BaseField):
    """ Class represent JSON null """

    def validate(self, value):
        super(Null, self).validate(value)
        if value is not None:
            raise ValueError('Expected None, got {0}'.format(value))


class Choice(BaseField):
    """ Field with a set of choices.

    Choices may be of any type and provided value is
    checked for inclusion in provided choices collection.
    """
    def __init__(self, choices=None, **kwargs):
        super(Choice, self).__init__(**kwargs)
        self._choices = choices or set()

    def validate(self, value):
        """ Check ``value`` is present in ``self._choices``.
        """
        super(Choice, self).validate(value)
        if (value is not None) and (value not in self._choices):
            raise ValueError(
                "Got an unexpected value in the field `{0}`: {1}. "
                "Value should be one of: {2}.".format(
                    self.field_name, value, self._choices))


class String(BaseField):
    """
    Class represent JSON string type

     >>> some_field = String(max_len=1000)
     >>> some_field.to_python("Some thing") == "Some thing"
    """

    def __init__(self, max_len=None, **kwargs):
        """
        Constructor

        :param max_len: Restrict maximum length of the field
        :type max_len: int
        """
        super(String, self).__init__(**kwargs)
        self._max_len = max_len

    def validate(self, value):
        super(String, self).validate(value)

        if value is None:
            return

        if not isinstance(value, six.string_types):
            raise ValueError(
                "{0!r} expected to be string but got {1}".format(
                    value, type(value).__name__))

        if self._max_len is not None:
            value_len = len(value)
            if value_len > self._max_len:
                raise ValueError(
                    "Length of field exceeds maximum allowed: {0}."
                    "Expected max length more than {1}".format(
                        value_len, self._max_len))


class Bool(BaseField):
    """
    Class represent JSON bool type

     >>> some_field = Bool()

     >>> some_field.to_python(True) == True
    """
    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: bool
        :return: None
        """
        super(Bool, self).validate(value)
        if (value is not None) and not isinstance(value, bool):
            raise ValueError("{0!r} expected to be bool".format(value))


class Int(BaseField):
    """
    Class represent JSON integer type

     >>> some_field = Int()
     >>> some_field.to_python(1) == 1

    """
    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: int or long
        :return: None
        """
        super(Int, self).validate(value)
        if (value is not None) and not isinstance(value, six.integer_types):
            raise ValueError("{0!r} expected to be integer".format(value))


class Float(BaseField):
    """
    Class represent JSON integer type

     >>> some_field = Float()
     >>> some_field.to_python(1.0) == 1.0

    """
    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: float
        :return: None
        """
        super(Float, self).validate(value)
        if (value is not None) and not isinstance(value, float):
            raise ValueError(
                "{0!r} expected to be integer but got {1}".format(
                    value, type(value).__name__))


class List(BaseField):
    """
    Class represent JSON list type

     >>> list_field = List(String(max_len=100))
     >>> list_field.to_python(["Some string"]) == ["Some string"]

     >>> list_field.to_python([2])
     Traceback (most recent call last):
     ...
     ValueError: '2' expected to be string
    """

    def __init__(self, element_type, min_len=None, max_len=None, **kwargs):
        """
        Constructor for List field type

        :param element_type: list element type
        :type element_type: instance of BaseField
        """
        super(List, self).__init__(**kwargs)

        if not isinstance(element_type, BaseField):
            raise ValueError(
                "Invalid type of 'element_type': expected to be instance of "
                "subclass of BaseField but got {0!r}".format(element_type))
        self._min_len = min_len
        self._max_len = max_len
        self._element_type = element_type

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: list
        :return: None
        """
        super(List, self).validate(value)

        if value is None:
            return

        if not isinstance(value, list):
            raise ValueError("{0!r} expected to be list".format(value))

        value_len = len(value)
        if (self._max_len is not None) and (value_len > self._max_len):
            raise ValueError(
                "Length of field exceeds maximum allowed: {0}. "
                "Expected value of length not more than {1}".format(
                    value_len, self._max_len))

        if (self._min_len is not None) and (value_len < self._min_len):
            raise ValueError(
                "Length of field is less than minimum allowed: {0}."
                "Expected value of length not less than {1}".format(
                    value_len, self._max_len))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a list to process
        :type value: list

        :return: list
        :rtype: list
        """
        value = self.check_default_value(value)
        if value is not None:
            value = [self._element_type.to_python(element) for element in value]

        return super(List, self).to_python(value)


class Map(BaseField):
    """
    Class represent JSON object type

     >>> some_field = Map(String, List(String))
     >>> some_field.to_python({"f1": ["val"]}) == {"f1": ["val"]}

     >>> some_field.to_python({2: ["val"]})
     Traceback (most recent call last):
     ...
     ValueError: '2' expected to be string
    """

    def __init__(self, key_type, value_type, **kwargs):
        """
        Constructor for List field type
        """
        super(Map, self).__init__(**kwargs)

        if not isinstance(key_type, BaseField):
            raise ValueError(
                "Invalid type of 'key_type': expected to be instance of "
                "subclass of BaseField but it is {0!r}".format(key_type))
        if not isinstance(value_type, BaseField):
            raise ValueError(
                "Invalid type of 'value_type': expected to be instance "
                "of subclass of BaseField but it is {0!r}".format(value_type))

        self._value_type = value_type
        self._key_type = key_type

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: dict
        :return: None
        """
        super(Map, self).validate(value)

        if value is None:
            return

        if not isinstance(value, dict):
            raise ValueError("{0!r} expected to be dict".format(value))

        for key, val in value.items():
            self._key_type.to_python(key)
            self._value_type.to_python(val)

    def to_python(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: list or dict
        :return: None
        """
        from pyraml.parser import ParseContext
        value = self.check_default_value(value)
        if value is not None:
            # At this point we could get list of dict or dict
            if isinstance(value, ParseContext):
                value = value.data
            if isinstance(value, list):
                _value = OrderedDict()
                for item in value:
                    if not isinstance(item, (dict, OrderedDict)):
                        raise ValueError("{0!r} expected to be dict or list of "
                                         "dict".format(value))

                    _value.update(
                        OrderedDict([
                            (self._key_type.to_python(key), self._value_type.to_python(val))
                            for key, val in item.items()])
                    )
                value = _value
            else:
                _value = OrderedDict()
                for key, val in value.items():
                    _value[self._key_type.to_python(key)] = self._value_type.to_python(val)
                value = _value

        return super(Map, self).to_python(value)


class Reference(BaseField):
    """
    Class represent reference to another model

     >>> from model import Model
     >>> class RamlDocumentation(Model):
     >>>    content = String()
     >>>    title = String()
     >>> some_field = List(Reference(RamlDocumentation))
     >>> doc = RamlDocumentation(content="Test content", title="Title")
     >>> some_field.to_python([doc]) == [doc]

     >>> some_field.to_python([2])
     Traceback (most recent call last):
     ...
     ValueError: '2' expected to be RamlDocumentation
    """

    def __init__(self, ref_class, **kwargs):
        """
        Constructor for Reference

        :param ref_class: model class to reference to
        :type ref_class: class of pyraml.model.Model

        :param kwargs: additional attributes for BaseField constructor
        :type kwargs: dict
        """
        super(Reference, self).__init__(**kwargs)
        self.ref_class = ref_class

    def _lazy_import(self):
        """
        If self.ref_class is string like "pyraml.entities.RamlTrait"
        just import the class and assign it to self.ref_class

        :return: None
        """
        if isinstance(self.ref_class, six.string_types):
            module_path, _, class_name = self.ref_class.rpartition('.')
            mod = __import__(module_path, fromlist=[class_name])
            self.ref_class = getattr(mod, class_name)

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: pyraml.model.Model
        :return: None
        """
        self._lazy_import()
        super(Reference, self).validate(value)

        if value is None:
            return

        if not isinstance(value, self.ref_class):
            raise ValueError("{0!r} expected to be {1} or dict".format(
                value, self.ref_class))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a model to process
        :type value: pyraml.model.Model or dict

        :return: int or long
        :rtype: int or long
        """
        self._lazy_import()
        value = self.check_default_value(value)

        if hasattr(self.ref_class, 'notNull') and value is None:
            value = {'notNull': True}

        if isinstance(value, self.ref_class):
            # Value is already instance of ref_class, don't need to convert it
            pass
        elif isinstance(value, dict):
            # Value is JSON object, convert it to `ref_class`
            value = self.ref_class.from_json(value)
        elif value is None:
            # Value empty, just instantiate empty `ref_class`
            value = self.ref_class()
        else:
            raise ValueError("{0!r} expected to be {1} or dict".format(
                value, self.ref_class))

        return super(Reference, self).to_python(value)


class Or(BaseField):
    """
    Class represent reference to another model

     >>> some_field = Or(String(),Float())
     >>> some_field.to_python("1") == "1"
     >>> some_field.to_python(2.1) == 2.1
     >>> some_field.to_python(False)
     Traceback (most recent call last):
     ...
     ValueError: u'False' expected to be one of: String, Float

    """

    def __init__(self, *args, **kwargs):
        """
        Constructor for Reference

        :param args: list of fields
        :type args: list of BaseField

        :param kwargs: additional attributes for BaseField constructor
        :type kwargs: dict
        """
        super(Or, self).__init__(**kwargs)
        self.variants = []
        for field in args:
            if not isinstance(field, BaseField):
                raise ValueError(
                    "Invalid argument supplied {0!r}: expected list of "
                    "BaseField instances".format(field))
            self.variants.append(field)

        if len(self.variants) < 2:
            raise ValueError(
                "Required at least 2 variants but got only {0}".format(
                    len(self.variants)))

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :return: None
        :raise ValueError: in case of validation errors
        """
        super(Or, self).validate(value)

        if value is None:
            return

        for field in self.variants:
            try:
                return field.to_python(value)
            except ValueError:
                pass
        else:
            # No one of variants doesn't accept `value`
            raise ValueError(
                "{0!r} expected to be one of: {1}".format(
                    value, ",".join([type(f).__name__ for f in self.variants])))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a field to process
        :type value: any

        :return: first of accepted variant
        """
        value = self.check_default_value(value)
        return self.validate(value)


class EncodedDataBase(BaseField):
    """ Base class for data that may be encoded in some format.

    Subclasses must set ``result_type`` to a type which the final
    result will have and define ``load_data`` that will perform
    the loading operation itself.
    """
    result_type = None

    def validate(self, value):
        """ Validata value by trying to load it as JSON.

        If data is already a dict - just return the current value.
        """
        super(EncodedDataBase, self).validate(value)
        if value is None:
            return
        if isinstance(value, self.result_type):
            return value
        try:
            return self.load_data(value)
        except Exception as ex:
            raise ValueError(str(ex))

    def to_python(self, value):
        value = self.check_default_value(value)
        return self.validate(value)

    def load_data(self, value):
        raise NotImplementedError


class JSONData(EncodedDataBase):
    """ Represents a JSON encoded data. """
    result_type = OrderedDict

    def load_data(self, value):
        return json.loads(value, object_pairs_hook=OrderedDict)


class XMLData(EncodedDataBase):
    """ Represents a XML encoded data. Uses built-in xml parsing library. """
    result_type = XMLElement

    def load_data(self, value):
        return parse_xml_string(value)


class RamlNamedParametersMap(Map):
    """ Map of String to a list or a single instance of
    RamlNamedParameters.
    """
    def __init__(self, *args, **kwargs):
        from .entities import RamlNamedParameters
        key_type = String()
        value_type = Or(
            Reference(RamlNamedParameters),
            List(Reference(RamlNamedParameters))
        )
        super(RamlNamedParametersMap, self).__init__(
            key_type=key_type, value_type=value_type, **kwargs)
