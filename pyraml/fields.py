__author__ = 'ad'

from abc import ABCMeta
import importhelpers
import importlib
from collections import OrderedDict


class BaseField(object):
    __metaclass__ = ABCMeta

    def __init__(self, required=True):
        super(BaseField, self).__init__()
        self.required = required

    def validate(self, value):
        if value is None and self.required:
            raise ValueError("missed value for required field")

    def from_python(self, value):
        """
        Do serialization steps on `value`
        """
        return value

    def to_python(self, value):
        """
        Do de-from_python steps from converting object from JSON representation to python representation
        """
        self.validate(value)
        return value


class String(BaseField):
    """
    Class represent JSON string type

     >>> some_field = String(max_len=1000)

     >>> some_field.to_python("Some thing") == "Some thing"

    """

    def __init__(self, max_len=None, **kwargs):
        super(String, self).__init__(**kwargs)
        self._max_len = max_len

    def validate(self, value):
        super(String, self).validate(value)

        if value is None:
            return

        if not isinstance(value, basestring):
            raise ValueError("{!r} expected to be string".format(value))
        if self._max_len is not None:
            value_len = len(value)
            if value_len > self._max_len:
                raise ValueError("length of field is exceeds maximum allowed: {} but expect no more then {}".format(
                    value_len, self._max_len))

    def to_python(self, value):
        """

        :param value: a string to process
        :type value: basestring
        :return: None
        """
        value = super(String, self).to_python(value)
        if value is not None:
            self.validate(value)

        return value


class List(BaseField):
    """
    Class represent JSON list type

     >>> some_field = List(String(max_len=100))
     >>> some_field.to_python(["Some string"]) == ["Some string"]

     >>> some_field.to_python([2])
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
                "Invalid type of 'element_type': expected to be instance of subclass of BaseField but it is {!r}".format(
                    element_type))
        self._min_len = min_len
        self._max_len = max_len
        self._element_type = element_type

    def validate(self, value):
        super(List, self).validate(value)

        if value is None:
            return

        if not isinstance(value, list):
            raise ValueError("{!r} expected to be list".format(value))

        value_len = len(value)
        if self._max_len is not None and value_len > self._max_len:
            raise ValueError("length of field is exceeds maximum allowed: {} but expect no more then {}".format(
                value_len, self._max_len))

        if self._min_len is not None and value_len < self._min_len:
            raise ValueError("length of field is less then minimum allowed: {} but expect no less then {}".format(
                value_len, self._max_len))

    def to_python(self, value):
        value = super(List, self).to_python(value)
        self.validate(value)

        if value is not None:
            value = [self._element_type.to_python(element) for element in value]

        return value


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

        :param element_type: list element type
        :type element_type: instance of BaseField
        """
        super(Map, self).__init__(**kwargs)

        if not isinstance(key_type, BaseField):
            raise ValueError(
                "Invalid type of 'key_type': expected to be instance of subclass of BaseField but it is {!r}".format(
                    key_type))
        if not isinstance(value_type, BaseField):
            raise ValueError(
                "Invalid type of 'value_type': expected to be instance of subclass of BaseField but it is {!r}".format(
                    value_type))

        self._value_type = value_type
        self._key_type = key_type

    def validate(self, value):
        super(Map, self).validate(value)

        if value is None:
            return

        if not isinstance(value, dict):
            raise ValueError("{!r} expected to be dict".format(value))

        for key, val in value.iteritems():
            self._key_type.validate(key)
            self._value_type.validate(val)

    def to_python(self, value):
        if value is not None:
            # At this point we could get list of dict or dict
            if isinstance(value, list):
                _value = OrderedDict()
                for item in value:
                    if not isinstance(item, (dict, OrderedDict)):
                        raise ValueError("{!r} expected to be dict or list of dict".format(value))

                    _value.update(
                        OrderedDict([
                            (self._key_type.to_python(key), self._value_type.to_python(val))
                                for key, val in item.items()])
                    )
                value = _value
            else:
                value = OrderedDict([
                    (self._key_type.to_python(key), self._value_type.to_python(val))
                        for key, val in value.items()])

        self.validate(value)

        return value


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
        super(Reference, self).__init__(**kwargs)
        if isinstance(ref_class, basestring):
            # we got string like "pyraml.entities.RamlTrait" for lazy resolving
            ref_class = importhelpers.dotted(ref_class)

        self.ref_class = ref_class

    def validate(self, value):
        super(Reference, self).validate(value)

        if value is None:
            return

        if not isinstance(value, self.ref_class):
            raise ValueError("{!r} expected to be {}".format(value, self.ref_class))

    def to_python(self, value):
        if not isinstance(value, dict):
            raise ValueError("{!r} expected to be dict".format(value))

        value = self.ref_class(**value)
        self.validate(value)

        if value is not None:
            return value
