# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from imio.annex import HAS_PLONE_6
from imio.annex.interfaces import IImioAnnexLayer
from imio.annex.testing import IMIO_ANNEX_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.browserlayer import utils as browserlayer_utils
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import unittest


if HAS_PLONE_6:
    from plone.registry.interfaces import IRegistry
    from Products.CMFPlone.utils import get_installer


class TestSetup(unittest.TestCase):
    """Test that imio.annex is properly installed."""

    layer = IMIO_ANNEX_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        if HAS_PLONE_6:
            self.installer = get_installer(self.portal, self.request)
        else:
            self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        if HAS_PLONE_6:
            self.assertTrue(self.installer.is_product_installed('imio.annex'))
        else:
            self.assertTrue(self.installer.isProductInstalled('imio.annex'))

    def test_browserlayer(self):
        """Test that IImioAnnexLayer is registered."""
        self.assertIn(IImioAnnexLayer, browserlayer_utils.registered_layers())

    def test_annex_type_registered(self):
        """Test that the annex content type is registered in portal_types."""
        types_tool = api.portal.get_tool('portal_types')
        self.assertIn('annex', types_tool.objectIds())

    def test_types_use_view_action(self):
        """Test that annex is listed in types_use_view_action_in_listings."""
        if HAS_PLONE_6:
            registry = getUtility(IRegistry)
            types = registry.get('plone.types_use_view_action_in_listings', ())
            self.assertIn('annex', types)
        else:
            props = api.portal.get_tool('portal_properties')
            types = props.site_properties.getProperty(
                'typesUseViewActionInListings', ()
            )
            self.assertIn('annex', types)


@unittest.skipUnless(HAS_PLONE_6, 'Uninstall profile only available on Plone 6')
class TestUninstall(unittest.TestCase):
    """Test that imio.annex is properly uninstalled."""

    layer = IMIO_ANNEX_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer = get_installer(self.portal, self.request)
        self.installer.uninstall_product('imio.annex')
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        self.assertFalse(self.installer.is_product_installed('imio.annex'))

    def test_browserlayer_removed(self):
        """Test that IImioAnnexLayer is removed after uninstall."""
        self.assertNotIn(IImioAnnexLayer, browserlayer_utils.registered_layers())

    def test_types_use_view_action_cleaned(self):
        """Test that annex is removed from types_use_view_action_in_listings."""
        registry = getUtility(IRegistry)
        types = registry.get('plone.types_use_view_action_in_listings', ())
        self.assertNotIn('annex', types)
