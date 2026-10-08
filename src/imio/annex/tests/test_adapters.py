# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import get_category_icon_url
from imio.annex.adapters import AnnexPrettyLinkAdapter
from imio.annex.testing import ImioAnnexTestCase
from imio.prettylink.interfaces import IPrettyLink


class TestAnnexPrettyLinkAdapter(ImioAnnexTestCase):
    """The preview (documentviewer) cases are in test_documentviewer."""

    def test__get_url(self):
        adapter = IPrettyLink(self.annex)
        self.assertIsInstance(adapter, AnnexPrettyLinkAdapter)
        adapter._leadingIcons()
        self.assertFalse(adapter.is_preview)
        self.assertEqual(
            adapter._get_url(), u"http://nohost/plone/folder/annex/@@download"
        )
        # Plone 4 behaviour: is_preview is computed by _leadingIcons, a link without icons breaks
        adapter = IPrettyLink(self.annex)
        adapter.showIcons = False
        self.assertRaises(AttributeError, adapter.getLink)

    def test__leadingIcons(self):
        icon_url = get_category_icon_url(self.category)
        self.assertTrue(icon_url.startswith(u"config/group/category/@@images/"))
        self.assertEqual(
            IPrettyLink(self.annex)._leadingIcons(), [(icon_url, u"Category")]
        )
        self.assertEqual(
            IPrettyLink(self.annex).getLink(),
            u"<a class='pretty_link' title='Annex' href='http://nohost/plone/folder/annex/@@download' "
            u"target='_self'><span class='pretty_link_icons'><img title='Category' "
            u"src='http://nohost/plone/{0}' style=\"width: 16px; height: 16px;\" /></span>"
            u"<span class='pretty_link_content'>Annex</span></a>".format(icon_url),
        )
        # Plone 4 behaviour: an annex missing from the categorized elements of its parent breaks
        self.uncategorize(self.annex)
        self.assertRaises(KeyError, IPrettyLink(self.annex)._leadingIcons)
