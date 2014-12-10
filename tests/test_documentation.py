__author__ = 'ad'

from nose.tools import raises, eq_
import os.path
import pyraml.parser
from pyraml.entities import RamlRoot, RamlDocumentation

fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'samples')

def test_include_raml():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'root-elements-includes.yaml'))
    assert isinstance(p, RamlRoot), RamlRoot
    assert p.raml_version == "0.8", p.raml_version
    assert p.title == "included title", p.title
    assert p.version == "v1", p.version
    assert p.baseUri == "https://sample.com/api", p.baseUri

    assert len(p.documentation) == 2, p.documentation
    assert isinstance(p.documentation[0], RamlDocumentation), p.documentation
    assert isinstance(p.documentation[1], RamlDocumentation), p.documentation

    assert p.documentation[0].title == "Home", p.documentation[0].title
    assert p.documentation[0].content == \
        """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do
eiusmod tempor incididunt ut labore et dolore magna...
""", p.documentation[0].content

    assert p.documentation[1].title == "Section", p.documentation[0].title
    assert p.documentation[1].content == "section content", p.documentation[1].content

def test_numeric_version():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'numeric-api-version.yaml'))
    assert isinstance(p, RamlRoot), RamlRoot
    assert p.version == 1, p.version
