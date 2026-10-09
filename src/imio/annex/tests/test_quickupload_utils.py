# -*- coding: utf-8 -*-
from imio.annex.quickupload.utils import is_iconified_categorized
from imio.annex.testing import ImioAnnexTestCase


class TestUtils(ImioAnnexTestCase):
    def test_is_iconified_categorized(self):
        self.assertTrue(is_iconified_categorized("annex"))
        self.assertFalse(is_iconified_categorized("File"))
        self.assertFalse(is_iconified_categorized("unknown"))
        self.assertFalse(is_iconified_categorized(""))
