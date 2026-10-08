# -*- coding: utf-8 -*-
from imio.annex.testing import ImioAnnexTestCase
from plone import api


class TestOverrides(ImioAnnexTestCase):
    """overrides.zcml (the columns and quick upload views are tested with their classes)."""

    def test_view(self):
        """The categories configuration uses the imio.helpers container and content views."""
        subcategory = api.content.create(
            container=self.category, type='ContentSubcategory', id='subcategory', title=u'Subcategory')
        config = self.portal['config']
        group = config['group']
        for obj, template in ((config, 'container.pt'), (group, 'container.pt'),
                              (self.category, 'container.pt'), (subcategory, 'content.pt')):
            view = obj.restrictedTraverse('@@view')
            self.assertTrue(view.index.filename.endswith('imio/helpers/browser/{0}'.format(template)), obj)
            self.assertIn('<table class="no-style-table"', view())
