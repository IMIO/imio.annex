# -*- coding: utf-8 -*-

from collective.iconifiedcategory import _
from collective.iconifiedcategory.utils import get_category_icon_url
from collective.iconifiedcategory.utils import get_category_object
from imio.prettylink.adapters import PrettyLinkAdapter
from zope.i18n import translate


class AnnexPrettyLinkAdapter(PrettyLinkAdapter):
    """
    """

    def _get_url(self):
        """ """
        if self.is_preview:
            url = self.context.absolute_url()
            return u"{0}/documentviewer#document/#/p1".format(url)
        else:
            return super(AnnexPrettyLinkAdapter, self)._get_url()

    def _leadingIcons(self):
        """
          Manage icons to display before the annex title.
        """
        res = []
        parent = self.context.aq_parent
        element = parent.categorized_elements[self.context.UID()]
        self.infos = parent.unrestrictedTraverse('@@categorized-childs-infos')

        # preview in progress
        if element["preview_status"] == 'in_progress':
            res.append(
                ('spinner_small.gif',
                 translate(
                     _("The document is currently under conversion, "
                       "please refresh the page in a few minutes"),
                     context=self.request)))
        # category icon
        category = get_category_object(self.context, self.context.content_category)
        category_url = get_category_icon_url(category)
        res.append((category_url,
                    category.title))

        # is a preview, store is_preview as it is reused in _get_url
        self.is_preview = self.infos.show_preview(element)
        if self.is_preview:
            res.append(('file_icon.png',
                        translate(_("Preview"), context=self.request)))
        return res
