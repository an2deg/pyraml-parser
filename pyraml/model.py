__author__ = 'ad'

import six
from .fields import BaseField
from . import ValidationError

class BaseModel(object):
    pass


class Schema(type):
    def __new__(mcs, name, bases, attrs):
        # Initialize special `_structure` class attribute which
        # contains info about all model fields'
        _structure = dict((_name, _type) for _name, _type in
            attrs.items() if isinstance(_type, BaseField))

        # Merge structures of parent classes into the structure of new model
        # class
        for base in bases:
            parent = base.__mro__[0]  # Multi inheritance is evil )
            if issubclass(parent, BaseModel) and not parent is BaseModel:
                for field_name, field_type in parent._structure.items():
                    if field_name not in _structure:
                        _structure[field_name] = field_type

        # Propagate field name from structure to the field, so we can access
        # RAML field name
        for field_name, field_obj in _structure.items():
            if field_obj.field_name is None:
                field_obj.field_name = field_name

        attrs['_structure'] = _structure

        return super(Schema, mcs).__new__(mcs, name, bases, attrs)


@six.add_metaclass(Schema)
class Model(BaseModel):
    """
    Base class for models

    >>> class Thing(Model):
    ...    field1 = String(max_len=100)
    ...    field2 = List(String(max_len=200), required=False)
    >>> t = Thing(field2=[u'field2 value'])
    >>> t.validate()
    Traceback (most recent call last):
    ...
    ValidationError: { 'field1': 'missed value for required field' }
    >>> t.field1 = u'field1 value'
    >>> t.validate()
    >>> t
    { 'field1': 'field1 value', 'field2': [ 'field2 value' ] }
    """
    def __init__(self, **kwargs):
        super(BaseModel, self).__init__()

        # Propagate an object attributes from field names
        for field_name, field_type in self.__class__._structure.items():
            if field_name in kwargs:
                setattr(self, field_name,
                        field_type.to_python(kwargs[field_name]))
            else:
                setattr(self, field_name, None)

    def __repr__(self):
        rv = {}
        for field_name in self.__class__._structure.keys():
            rv[field_name] = getattr(self, field_name, None)
        return rv.__repr__()

    def validate(self):
        errors = {}
        for field_name, field_type in self.__class__._structure.items():
            # Validate and process a field of JSON object
            try:
                field_type.validate(getattr(self, field_name))
            except ValueError as e:
                errors[field_name] = six.text_type(e)
        if errors:
            raise ValidationError(errors)

    @classmethod
    def from_json(cls, json_object):
        """
        Initialize a model from JSON object

        :param json_object: JSON object to initialize a model
        :type json_object: dict

        :return: instance of BaseModel
        :rtype: instance of BaseModel
        """
        rv = cls()
        errors = {}

        for model_field_name, field_type in cls._structure.items():
            # Validate and process a field of JSON object
            try:
                value = field_type.to_python(
                    json_object.get(model_field_name, None))
                setattr(rv, model_field_name, value)
            except ValueError as e:
                errors[model_field_name] = six.text_type(e)

        # Look for aliased attributes
        for field_name, field_value in json_object.items():
            if not field_name in cls._structure:
                for model_field_name, field_type in cls._structure.items():
                    if field_type.field_name == field_name:
                        try:
                            value = field_type.to_python(field_value)
                            setattr(rv, model_field_name, value)
                        except ValueError as e:
                            errors[model_field_name] = six.text_type(e)
        if errors:
            raise ValidationError(errors)

        return rv
