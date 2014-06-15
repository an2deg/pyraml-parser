__author__ = 'ad'

from collections import OrderedDict
from nose.tools import raises
from pyraml.model import Model
from pyraml.fields import List, String, Reference, Map, Or, Float


def test_model_structure_inheritance():
    class Thing(Model):
        inner = List(String())

    class SubThing(Thing):
        external = List(String())

    thing = SubThing()

    assert thing._structure.keys() == ['external', 'inner'], thing._structure.keys()
    assert all(isinstance(a, List) for a in thing._structure.values()), thing._structure.values()


def test_model_standard_constructor_without_values():
    class Thing(Model):
        inner = String()

    thing = Thing()
    assert thing.inner is None, thing.inner


def test_model_constructor_with_keyword_arguments():
    class Thing(Model):
        inner = String()

    thing = Thing(inner="some string")
    assert thing.inner == "some string", thing.inner


def test_model_with_reference():
    class Thing(Model):
        title = String()

    class TopThing(Model):
        things = List(Reference(Thing))

    thing = Thing(title="some string")
    top_thing = TopThing(things=[thing])
    assert len(top_thing.things) == 1, top_thing.things
    assert top_thing.things[0] is thing, top_thing.things


def test_model_with_map():
    class Thing(Model):
        title = String()

    class MapThing(Model):
        map = Map(String(), Reference(Thing))

    thing = Thing(title="some string")
    map_thing = MapThing(map={"t1": thing})
    assert isinstance(map_thing.map, OrderedDict), map_thing.map
    assert len(map_thing.map) == 1, map_thing.map
    assert map_thing.map["t1"] is thing, map_thing.map

def test_model_with_reference_and_aliased_field():
    class Thing(Model):
        id_ = String(field_name='id')

    class RefThing(Model):
        ref = Reference(Thing)

    res = RefThing.ref.to_python({"id": "some field"})
    assert isinstance(res, Thing), res
    assert res.id_ == "some field", res

def test_model_with_or_successfully():
    class Thing(Model):
        a = Or(String(), Float())

    res = Thing.a.to_python("a")
    assert res == "a", res

    res = Thing.a.to_python(1.1)
    assert res == 1.1, res