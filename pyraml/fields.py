__author__ = 'ad'

from abc import ABCMeta
import importhelpers
from collections import OrderedDict


class BaseField(object):
    __metaclass__ = ABCMeta

    def __init__(self, required=False, field_name=None):
        super(BaseField, self).__init__()
        self.required = required
        self.field_name = field_name

    def validate(self, value):
        """
        Validate `value`

        :raise ValueError: in case of validation errors

        """

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
        """
        Constructor

        :param max_len: Restrict maximum length of the field
        :type max_len: int
        :param force_conversion: Set to true in order to ignore real type of a value and convert it into unicode.
         We have to have this parameter b/c YAML format doesn't not have schema and string '17.30' is always
         translated to float 17.30
        :type force_conversion: bool
        """
        super(String, self).__init__(**kwargs)
        self._max_len = max_len

    def validate(self, value):
        super(String, self).validate(value)

        if value is None:
            return

        if not isinstance(value, basestring):
            raise ValueError("{!r} expected to be string but got {}".format(value, type(value).__name__))

        if self._max_len is not None:
            value_len = len(value)
            if value_len > self._max_len:
                raise ValueError("length of field is exceeds maximum allowed: {} but expect no more then {}".format(
                    value_len, self._max_len))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a string to process
        :type value: basestring

        :return: string
        :rtype: basestring

        """
        self.validate(value)

        return value


class Bool(BaseField):
    """
    Class represent JSON bool type

     >>> some_field = Bool()

     >>> some_field.to_python(True) == True

    """

    def __init__(self, **kwargs):
        super(Bool, self).__init__(**kwargs)

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: bool
        :return: None
        """
        super(Bool, self).validate(value)

        if value is None:
            return

        if not isinstance(value, bool):
            raise ValueError("{!r} expected to be bool".format(value))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a string to process
        :type value: bool
        :return: None
        """
        self.validate(value)

        return value


class Int(BaseField):
    """
    Class represent JSON integer type

     >>> some_field = Int()
     >>> some_field.to_python(1) == 1

    """

    def __init__(self, **kwargs):
        super(Int, self).__init__(**kwargs)

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: int or long
        :return: None
        """
        super(Int, self).validate(value)

        if value is None:
            return

        if not isinstance(value, (int, long)):
            raise ValueError("{!r} expected to be integer".format(value))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a string to process
        :type value: int or long

        :return: int or long
        :rtype: int or long
        """
        self.validate(value)

        return value


class Float(BaseField):
    """
    Class represent JSON integer type

     >>> some_field = Float()
     >>> some_field.to_python(1.0) == 1.0

    """

    def __init__(self, **kwargs):
        super(Float, self).__init__(**kwargs)

    def validate(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: float
        :return: None
        """
        super(Float, self).validate(value)

        if value is None:
            return

        if not isinstance(value, float):
            raise ValueError("{!r} expected to be integer but got {}".format(value, type(value).__name__))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a string to process
        :type value: float

        :return: float
        :rtype: float
        """
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
            raise ValueError("{!r} expected to be list".format(value))

        value_len = len(value)
        if self._max_len is not None and value_len > self._max_len:
            raise ValueError("length of field is exceeds maximum allowed: {} but expect no more then {}".format(
                value_len, self._max_len))

        if self._min_len is not None and value_len < self._min_len:
            raise ValueError("length of field is less then minimum allowed: {} but expect no less then {}".format(
                value_len, self._max_len))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a list to process
        :type value: list

        :return: list
        :rtype: list
        """
        if value is not None:
            value = [self._element_type.to_python(element) for element in value]

        self.validate(value)

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
            raise ValueError("{!r} expected to be dict".format(value))

        for key, val in value.iteritems():
            self._key_type.validate(key)
            self._value_type.validate(val)

    def to_python(self, value):
        """
        Validate value to match rules

        :param value: value to validate
        :type value: list
        :return: None
        """
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
        If self.ref_class is string like "pyraml.entities.RamlTrait" just import the class
        and assign it to self.ref_class

        :return: None
        """
        if isinstance(self.ref_class, basestring):
            self.ref_class = importhelpers.dotted(self.ref_class)

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
            raise ValueError("{!r} expected to be {}".format(value, self.ref_class))

    def to_python(self, value):
        """
        Convert value to python representation

        :param value: a model to process
        :type value: pyraml.model.Model or dict

        :return: int or long
        :rtype: int or long
        """
        self._lazy_import()

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
            raise ValueError("{!r} expected to be dict".format(value))
        self.validate(value)

        return value


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
                raise ValueError("Invalid argument supplied {!r}: expected list of BaseField instances".format(field))
            self.variants.append(field)

        if len(self.variants) < 2:
            raise ValueError("Required at least 2 variants but got only {}".format(len(self.variants)))

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
                field.validate(value)
                break
            except ValueError:
                pass
        else:
            # No one of variants doesn't accept `value`
            raise ValueError("{!r} expected to be one of: {}".format(value,
                                                                     ",".join(
                                                                         [type(f).__name__ for f in self.variants])))

        def to_python(self, value):
            """
            Convert value to python representation

            :param value: a field to process
            :type value: any

            :return: first of accepted variant
            """

            for field in self.variants:
                try:
                    field.validate(value)
                    return field.to_python(value)
                except ValueError:
                    pass
            else:
                # Raise ValueError
                self.validate(value)