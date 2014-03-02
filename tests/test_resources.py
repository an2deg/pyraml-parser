__author__ = 'ad'

import os.path
import pyraml.parser
from collections import OrderedDict
from pyraml.entities import RamlResource, RamlMethod

fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'samples')


def test_resource_nested():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'resource-nested.yaml'))
    assert isinstance(p.resources, OrderedDict), p.resources
    assert len(p.resources) == 1, p.resources

    # Validate root resource
    assert "/media" in p.resources, p.resources
    root_resource = p.resources["/media"]

    assert isinstance(root_resource, RamlResource), p.resources
    assert root_resource.parentResource is None, p.resources
    assert root_resource.methods is not None, p.resources
    assert "get" in root_resource.methods, p.resources
    assert isinstance(root_resource.methods["get"], RamlMethod), p.resources
    assert root_resource.methods["get"].notNull, p.resources

    # validate sub-resources
    assert root_resource.resources is not None, root_resource

    assert "/search" in root_resource.resources is not None, root_resource
    assert root_resource.resources["/search"].displayName == "Media Search", root_resource
    assert "get" in root_resource.resources["/search"].methods, root_resource
    assert root_resource.resources["/search"].methods["get"].notNull, root_resource

    assert "/tags" in root_resource.resources is not None, root_resource
    assert root_resource.resources["/tags"].displayName == "Tags", root_resource
    assert "get" in root_resource.resources["/tags"].methods, root_resource
    assert root_resource.resources["/tags"].methods["get"].notNull, root_resource

    # /media/tags has their own resource /search
    tag_resource = root_resource.resources["/tags"]
    assert tag_resource.resources is not None, tag_resource
    assert "/search" in tag_resource.resources, tag_resource
    assert tag_resource.resources["/search"].displayName == "Tag Search", tag_resource
    assert tag_resource.resources["/search"].methods["get"].notNull, root_resource

    # Ensure than every sub-resource have correct parentResource
    assert root_resource.resources["/search"].parentResource is root_resource
    assert root_resource.resources["/tags"].parentResource is root_resource
    assert tag_resource.resources["/search"].parentResource is tag_resource


def test_resource_with_responses():
    p = pyraml.parser.load(os.path.join(fixtures_dir, 'null-elements.yaml'))
    assert isinstance(p.resources, OrderedDict), p.resources

    assert "/leagues" in p.resources, p

    leagues_resource = p.resources["/leagues"]
    assert leagues_resource.displayName == "Leagues", leagues_resource
    assert leagues_resource.methods, leagues_resource
    assert leagues_resource.methods["get"], leagues_resource

    leagues_resource_get = leagues_resource.methods["get"]
    assert leagues_resource_get.responses, leagues_resource_get
    assert leagues_resource_get.responses[200], leagues_resource_get
    assert leagues_resource_get.responses[200].body, leagues_resource_get

    assert "application/json" in leagues_resource_get.responses[200].body, leagues_resource_get
    assert "text/xml" in leagues_resource_get.responses[200].body, leagues_resource_get