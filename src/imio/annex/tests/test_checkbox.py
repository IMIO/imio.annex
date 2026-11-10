# -*- coding: utf-8 -*-

from imio.annex.tests.base import BaseTestCase
from plone import api

import re


class TestOrderableCheckBoxWidget(BaseTestCase):
    """Test imio.annex.widgets.checkbox.OrderableCheckBoxWidget."""

    def setUp(self):
        super(TestOrderableCheckBoxWidget, self).setUp()
        self._add_annex(title=u'PDF annex')
        self._add_annex(title=u'Text annex', annex_file=self.file_txt)
        form = self.folder.restrictedTraverse('@@export-pdf-form')
        form.update()
        self.widget = form.widgets['elements']

    def test_portal_url(self):
        self.assertEqual(self.widget.portal_url,
                         api.portal.get().absolute_url())

    def test_items(self):
        """Terms disabled/readonly/description are reported on the items."""
        items = self.widget.items
        self.assertEqual([item['disabled'] for item in items], [False, True])
        self.assertEqual([item['readonly'] for item in items], [False, False])
        self.assertEqual([item['description'] for item in items], ['', ''])
        # the view sets sortable, the widget defaults to False
        self.assertTrue(self.widget.sortable)

    def test_render_odd_even(self):
        """Options get an "odd"/"even" CSS class, first option is "odd"."""
        self._add_annex(title=u'Third annex')
        form = self.folder.restrictedTraverse('@@export-pdf-form')
        form.update()
        rendered = form.widgets['elements'].render()
        self.assertEqual(
            re.findall(r'<span class="(option [a-z]+)"', rendered),
            ['option odd', 'option even', 'option odd'])
        # odd/even are recomputed after a drag and drop
        self.assertIn("addClass(index % 2 ? 'even' : 'odd')", rendered)
