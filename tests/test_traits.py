__author__ = 'ad'

import os.path
import pyraml.parser
from pyraml.entities import RamlRoot, RamlTrait, RamlBody

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