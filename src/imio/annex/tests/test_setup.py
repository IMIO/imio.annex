# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from imio.annex.interfaces import IImioAnnexLayer
from imio.annex.testing import HAS_PLONE_6
from imio.annex.testing import IMIO_ANNEX_INTEGRATION_TESTING
from imio.annex.testing import ImioAnnexTestCase
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.browserlayer import utils as browserlayer_utils
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.i18n import translate

import unittest


if HAS_PLONE_6:
    from Products.CMFPlone.utils import get_installer

CSS = "++resource++imio.annex.quickupload/quickupload.css"
JS = "++resource++imio.annex.quickupload/helpers.js"


class TestSetup(ImioAnnexTestCase):
    """Test that imio.annex is properly installed."""

    def setUp(self):
        super(TestSetup, self).setUp()
        if HAS_PLONE_6:
            self.installer = get_installer(self.portal, self.request)
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        if HAS_PLONE_6:
            self.assertTrue(self.installer.is_product_installed("imio.annex"))
        else:
            self.assertTrue(self.installer.isProductInstalled("imio.annex"))

    def test_browserlayer(self):
        """Test that IImioAnnexLayer is registered."""
        self.assertIn(IImioAnnexLayer, browserlayer_utils.registered_layers())

    def test_annex_type_registered(self):
        """Test that the annex content type is registered in portal_types."""
        types_tool = api.portal.get_tool("portal_types")
        self.assertIn("annex", types_tool.objectIds())
        fti = types_tool["annex"]
        self.assertEqual(fti.klass, "imio.annex.content.annex.Annex")
        self.assertEqual(fti.schema_policy, "schema_policy_annex")
        self.assertEqual(fti.add_view_expr, "string:${folder_url}/++add++annex")
        self.assertTrue(fti.global_allow)
        self.assertEqual(fti.default_view, "view")
        self.assertEqual(tuple(fti.view_methods), ("view", "documentviewer"))
        self.assertEqual(fti.getMethodAliases()["(Default)"], "@@display-file")
        self.assertEqual(
            tuple(fti.behaviors),
            (
                "plone.app.dexterity.behaviors.filename.INameFromFileName",
                "plone.app.lockingbehavior.behaviors.ILocking",
                "collective.iconifiedcategory.behaviors.iconifiedcategorization.IIconifiedCategorization",
                "collective.dms.scanbehavior.behaviors.IScanFields",
            ),
        )
        actions = dict((action.id, action) for action in fti.listActions())
        self.assertEqual(
            sorted(actions),
            ["download", "edit", "view", "view_element", "view_preview"],
        )
        self.assertEqual(actions["view_element"].permissions, ("Manage portal",))
        self.assertEqual(
            actions["view_preview"].condition.text, "python:object.show_preview()"
        )
        self.assertEqual(
            actions["download"].condition.text, "python:object.show_download()"
        )
        self.assertEqual(
            actions["download"].getActionExpression(),
            "string:${object/absolute_url}/@@download",
        )

    def test_annex_actions(self):
        """object_buttons shown on an annex, depending on the user."""
        portal_actions = api.portal.get_tool("portal_actions")
        # not converted: no preview
        buttons = [
            a["id"]
            for a in portal_actions.listFilteredActionsFor(self.annex)["object_buttons"]
        ]
        self.assertIn("view_element", buttons)
        self.assertIn("download", buttons)
        self.assertNotIn("view_preview", buttons)
        view_element = [
            a
            for a in portal_actions.listFilteredActionsFor(self.annex)["object_buttons"]
            if a["id"] == "view_element"
        ][0]
        self.assertEqual(view_element["url"], "http://nohost/plone/folder/annex/view")
        # 'view_element' is for managers only
        setRoles(self.portal, TEST_USER_ID, ["Member", "Reader"])
        buttons = [
            a["id"]
            for a in portal_actions.listFilteredActionsFor(self.annex)["object_buttons"]
        ]
        self.assertNotIn("view_element", buttons)
        self.assertIn("download", buttons)

    def test_workflow(self):
        """Annexes have no workflow."""
        wf_tool = api.portal.get_tool("portal_workflow")
        self.assertEqual(wf_tool.getChainForPortalType("annex"), ())
        self.assertIsNone(api.content.get_state(self.annex, None))

    def test_types_use_view_action(self):
        """Test that annex is listed in types_use_view_action_in_listings."""
        if HAS_PLONE_6:
            registry = getUtility(IRegistry)
            types = registry.get("plone.types_use_view_action_in_listings", ())
            self.assertIn("annex", types)
        else:
            props = api.portal.get_tool("portal_properties")
            types = props.site_properties.getProperty(
                "typesUseViewActionInListings", ()
            )
            self.assertIn("annex", types)

    def test_resources(self):
        """The quickupload CSS and JS are registered."""
        if HAS_PLONE_6:
            self.assertEqual(
                api.portal.get_registry_record(
                    "plone.bundles/imio.annex.base.csscompilation"
                ),
                CSS,
            )
            self.assertEqual(
                api.portal.get_registry_record(
                    "plone.bundles/imio.annex.base.jscompilation"
                ),
                JS,
            )
        else:
            self.assertIn(CSS, api.portal.get_tool("portal_css").getResourceIds())
            self.assertIn(
                JS, api.portal.get_tool("portal_javascripts").getResourceIds()
            )
        self.assertIsNotNone(self.portal.unrestrictedTraverse(CSS))
        self.assertIsNotNone(self.portal.unrestrictedTraverse(JS))

    def test_translations(self):
        """French translations shipped by imio.annex, also for other domains."""
        self.assertEqual(
            translate(u"Annex", domain="imio.annex", target_language="fr"), u"Annexe"
        )
        self.assertEqual(
            translate(u"View element", domain="plone", target_language="fr"),
            u"Voir l'élément",
        )
        self.assertEqual(
            translate(u"View preview", domain="plone", target_language="fr"),
            u"Voir la prévisualisation",
        )
        self.assertTrue(
            translate(
                u"Server error, please contact support and/or try again.",
                domain="collective.quickupload",
                target_language="fr",
            ).startswith(u"Une erreur est survenue")
        )


@unittest.skipUnless(HAS_PLONE_6, "Uninstall profile only available on Plone 6")
class TestUninstall(unittest.TestCase):
    """Test that imio.annex is properly uninstalled."""

    layer = IMIO_ANNEX_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer = get_installer(self.portal, self.request)
        self.installer.uninstall_product("imio.annex")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        self.assertFalse(self.installer.is_product_installed("imio.annex"))

    def test_browserlayer_removed(self):
        """Test that IImioAnnexLayer is removed after uninstall."""
        self.assertNotIn(IImioAnnexLayer, browserlayer_utils.registered_layers())

    def test_types_use_view_action_cleaned(self):
        """Test that annex is removed from types_use_view_action_in_listings."""
        registry = getUtility(IRegistry)
        types = registry.get("plone.types_use_view_action_in_listings", ())
        self.assertNotIn("annex", types)
