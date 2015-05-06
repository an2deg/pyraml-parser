from unittest import TestCase

import collections

from pyraml.fields import Reference


class ValidationTestCase(TestCase):
    """ Test validation and invalid values processing stuff. """

    def test_reference_dotted_path_import(self):
        reference = Reference("collections.deque")
        reference._lazy_import()
        assert reference.ref_class is collections.deque
