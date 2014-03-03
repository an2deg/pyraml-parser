__author__ = 'ad'

import os.path
import pyraml.parser
from pyraml.entities import RamlRoot, RamlTrait, RamlBody, RamlResourceType

fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'samples')


def test_parse_traits_with_schema():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'media-type.yaml'))
    assert isinstance(p, RamlRoot), RamlRoot
    assert p.traits, "Property `traits` should be set"
    assert len(p.traits) == 1, p.traits
    assert isinstance(p.traits["traitOne"], RamlTrait), p.traits
    assert isinstance(p.traits["traitOne"].body, RamlBody), p.traits["traitOne"]
    assert p.traits["traitOne"].body.schema == """{  "$schema": "http://json-schema.org/draft-03/schema",
   "type": "object",
   "description": "A product presentation",
   "properties": {
     "id":  { "type": "string" },
     "title":  { "type": "string" }
   }
}
""", p.traits["traitOne"].body.schema


def test_parse_raml_with_many_traits():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'full-config.yaml'))
    assert isinstance(p, RamlRoot), RamlRoot
    assert p.traits, "Property `traits` should be set"
    assert len(p.traits) == 2, p.traits
    assert isinstance(p.traits["simple"], RamlTrait), p.traits
    assert isinstance(p.traits["knotty"], RamlTrait), p.traits
    assert p.traits["simple"].displayName == "simple trait"
    assert p.traits["knotty"].displayName == "<<value>> trait"


def test_parse_resource_type_with_references_to_traits():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'media-type.yaml'))
    assert isinstance(p, RamlRoot), RamlRoot
    assert p.resourceTypes, "Property `traits` should be set"
    assert len(p.resourceTypes)

    assert 'typeParent' in p.resourceTypes, p.resourceTypes
    assert isinstance(p.resourceTypes['typeParent'], RamlResourceType), p.resourceTypes
    parent_resource_type = p.resourceTypes['typeParent']
    assert parent_resource_type.methods, p.resourceTypes['typeParent']
    assert 'get' in parent_resource_type.methods

    assert 'typeChild' in p.resourceTypes, p.resourceTypes
    assert isinstance(p.resourceTypes['typeChild'], RamlResourceType), p.resourceTypes