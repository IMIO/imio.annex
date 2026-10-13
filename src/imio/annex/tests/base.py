# -*- coding: utf-8 -*-

from imio.annex import testing
from imio.annex.interfaces import IImioAnnexLayer
from plone import api
from plone import namedfile
from plone.app.testing import login
from zope.interface import alsoProvides

import os
import unittest


class BaseTestCase(unittest.TestCase):

    layer = testing.IMIO_ANNEX_FUNCTIONAL_TESTING

    def _named_file(self, filename):
        f = open(os.path.join(os.path.dirname(__file__), filename), 'r')
        return namedfile.NamedBlobFile(f.read(), filename=unicode(filename))

    @property
    def file_pdf(self):
        return self._named_file('file.pdf')

    @property
    def file_txt(self):
        return self._named_file('file.txt')

    def setUp(self):
        self.maxDiff = None
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.request, IImioAnnexLayer)
        api.user.create(email='test@test.com', username='adminuser', password='secret')
        api.user.grant_roles(username='adminuser', roles=['Manager'])
        login(self.portal, 'adminuser')
        self.folder = api.content.create(
            id='folder', type='Folder', title='Folder', container=self.portal)

    def _add_annex(self, title=u'Annex', annex_file=None,
                   category='config_-_group-1_-_category-1-1'):
        """Add an annex to self.folder."""
        return api.content.create(
            type='annex',
            title=title,
            file=annex_file if annex_file is not None else self.file_pdf,
            container=self.folder,
            content_category=category,
            to_print=False,
            confidential=False,
            publishable=False)
