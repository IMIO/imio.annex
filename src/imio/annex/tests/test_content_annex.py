# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import update_categorized_elements
from imio.annex.content.annex import AnnexSchemaPolicy
from imio.annex.content.annex import IAnnex
from imio.annex.testing import ImioAnnexTestCase
from plone import api
from plone.rfc822.interfaces import IPrimaryFieldInfo
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUID


class TestAnnex(ImioAnnexTestCase):

    def test_UID(self):
        self.assertEqual(self.annex.UID(), IUUID(self.annex))
        self.assertEqual(self.annex.UID(), getattr(self.annex, ATTRIBUTE_NAME))
        self.assertNotEqual(self.annex.UID(), self.annex_2.UID())

    def test_show_download(self):
        self.assertEqual(self.folder.categorized_elements[self.annex.UID()]['show_preview'], 0)
        self.assertTrue(self.annex.show_download())
        # preview with protected download: the categorized-childs-infos view decides (True by default)
        self.category.show_preview = 2
        update_categorized_elements(self.folder, self.annex, self.category)
        self.assertEqual(self.folder.categorized_elements[self.annex.UID()]['show_preview'], 2)
        self.assertTrue(self.annex.show_download())
        # Plone 4 behaviour: an annex missing from the categorized elements of its parent breaks
        self.uncategorize(self.annex)
        self.assertRaises(KeyError, self.annex.show_download)

    def test_show_preview(self):
        # a text file is never converted (converted annexes: test_documentviewer)
        self.assertEqual(self.folder.categorized_elements[self.annex.UID()]['preview_status'], 'not_convertable')
        self.assertFalse(self.annex.show_preview())
        # Plone 4 behaviour: an annex missing from the categorized elements of its parent breaks
        self.uncategorize(self.annex)
        self.assertRaises(KeyError, self.annex.show_preview)


class TestAnnexSchemaPolicy(ImioAnnexTestCase):

    def test_bases(self):
        self.assertEqual(AnnexSchemaPolicy().bases('annex', None), (IAnnex, ))
        fti = api.portal.get_tool('portal_types')['annex']
        self.assertTrue(fti.lookupSchema().isOrExtends(IAnnex))
        self.assertTrue(IAnnex.providedBy(self.annex))


class TestIAnnex(ImioAnnexTestCase):

    def test_fields(self):
        """title and description only in the add and edit forms, file is the required primary field."""
        self.assertTrue(IAnnex['file'].required)
        self.assertFalse(IAnnex['title'].required)
        self.assertEqual(IPrimaryFieldInfo(self.annex).fieldname, 'file')
        add_form = self.folder.restrictedTraverse('++add++annex').form_instance
        add_form.update()
        self.assertEqual(list(add_form.widgets.keys())[:2], ['title', 'description'])
        self.assertIn('file', add_form.widgets)
        edit_form = self.annex.restrictedTraverse('@@edit').form_instance
        edit_form.update()
        self.assertEqual(list(edit_form.widgets.keys())[:2], ['title', 'description'])
        self.assertIn('file', edit_form.widgets)
        view = self.annex.restrictedTraverse('@@view')
        view.update()
        self.assertNotIn('title', view.w)
        self.assertNotIn('description', view.w)
        self.assertIn('file', view.w)
