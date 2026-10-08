# -*- coding: utf-8 -*-
from collective.eeafaceted.z3ctable.columns import ElementNumberColumn
from collective.iconifiedcategory.browser.tabview import AuthorColumn as IconifiedAuthorColumn
from collective.iconifiedcategory.interfaces import IIconifiedCategorySettings
from imio.annex.columns import ActionsColumn
from imio.annex.columns import AuthorColumn
from imio.annex.columns import PrettyLinkColumn
from imio.annex.testing import annex_file
from imio.annex.testing import ImioAnnexTestCase
from imio.prettylink.interfaces import IPrettyLink
from plone import api
from zope.component import getMultiAdapter


class ColumnsTestCase(ImioAnnexTestCase):
    """The categorized table of the folder, as displayed in the @@iconifiedcategory tab."""

    def table(self):
        table = getMultiAdapter((self.folder, self.request), name='iconifiedcategory_table')
        table.update()
        return table

    def column(self, table, name):
        return [column for column in table.columns if column.__name__ == name][0]


class TestPrettyLinkColumn(ColumnsTestCase):

    def test_getPrettyLink(self):
        table = self.table()
        column = self.column(table, 'title-column')
        self.assertIsInstance(column, PrettyLinkColumn)
        annex_item, annex_2_item = table.values
        # link opened in a new tab, empty description and scan_id
        pretty_link = IPrettyLink(self.annex)
        pretty_link.target = '_blank'
        self.assertEqual(
            column.renderCell(annex_item),
            pretty_link.getLink() + u'<p class="discreet"></p>'
            u'<div class="discreet"><label class="horizontal">File</label>'
            u'<div class="type-text-widget">annex.txt</div></div>')
        self.assertIn(u"target='_blank'", column.renderCell(annex_item))
        # description, filename and scan_id are escaped
        self.annex_2.description = u'Déjà <b>\nvu & co'
        self.annex_2.file = annex_file(filename=u'<annex>.txt')
        self.annex_2.scan_id = u'<IMIO>'
        pretty_link = IPrettyLink(self.annex_2)
        pretty_link.target = '_blank'
        self.assertEqual(
            column.renderCell(annex_2_item),
            pretty_link.getLink() + u'<p class="discreet"></p>'
            u'<p class="discreet">Déjà &lt;b&gt;<br/>vu &amp; co</p>'
            u'<div class="discreet"><label class="horizontal">File</label>'
            u'<div class="type-text-widget">&lt;annex&gt;.txt</div></div>'
            u'<div class="discreet"><label class="horizontal">scan_id</label>'
            u'<div class="type-textarea-widget">&lt;IMIO&gt;</div></div>')


class TestAuthorColumn(ColumnsTestCase):

    def test_renderCell(self):
        table = self.table()
        column = self.column(table, 'author-column')
        self.assertIsInstance(column, AuthorColumn)
        self.assertEqual(column.header, IconifiedAuthorColumn.header)
        self.assertEqual(column.weight, IconifiedAuthorColumn.weight)
        self.assertEqual(column.renderCell(table.values[0]), u'test_user_1_')


class TestActionsColumn(ColumnsTestCase):

    def test__showArrows(self):
        column = self.column(self.table(), 'action-column')
        # sorted alphabetically by default
        self.assertFalse(column._showArrows())
        api.portal.set_registry_record('sort_categorized_tab', False, interface=IIconifiedCategorySettings)
        self.assertTrue(column._showArrows())

    def test_renderCell(self):
        table = self.table()
        column = self.column(table, 'action-column')
        self.assertIsInstance(column, ActionsColumn)
        self.assertEqual(column.weight, 100)
        # history and arrows to move the annexes, when sorted manually
        api.portal.set_registry_record('sort_categorized_tab', False, interface=IIconifiedCategorySettings)
        rendered = column.renderCell(table.values[0])
        self.assertIn(u'http://nohost/plone/folder/annex/@@historyview', rendered)
        self.assertIn(u'arrowDown.png', rendered)
        self.assertNotIn(u'arrowUp.png', rendered)
        self.assertIn(u'arrowUp.png', column.renderCell(table.values[1]))
        # no arrows when the categorized elements are sorted
        api.portal.set_registry_record('sort_categorized_tab', True, interface=IIconifiedCategorySettings)
        rendered = column.renderCell(table.values[0])
        self.assertIn(u'http://nohost/plone/folder/annex/@@historyview', rendered)
        self.assertNotIn(u'arrowDown.png', rendered)


class TestElementNumberColumn(ColumnsTestCase):

    def test_renderCell(self):
        table = self.table()
        column = self.column(table, 'number-column')
        self.assertIsInstance(column, ElementNumberColumn)
        self.assertEqual([column.renderCell(item) for item in table.values], [1, 2])
