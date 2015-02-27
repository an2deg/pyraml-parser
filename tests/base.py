import os
from unittest import TestCase

from pyraml import parser


class SampleParseTestCase(TestCase):
    samples_dir = os.path.join(
        os.path.dirname(__file__), 'samples')

    def load(self, *parts):
        path = self.sample_path(*parts)
        return parser.load(path)

    def sample_path(self, *parts):
        return os.path.join(self.samples_dir, *parts)
