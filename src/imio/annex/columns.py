# -*- coding: utf-8 -*-

from collective.eeafaceted.z3ctable.columns import MemberIdColumn
from collective.iconifiedcategory.interfaces import IIconifiedPreview
from collective.iconifiedcategory.browser.tabview import AuthorColumn as IconifiedAuthorColumn
from imio.dashboard.columns import ActionsColumn as DashboardActionsColumn
from imio.dashboard.columns import PrettyLinkColumn as DashboardPrettyLinkColumn
from plone import api
from zope.i18n import translate


class PrettyLinkColumn(DashboardPrettyLinkColumn):
    header = u'Title'
    weight = 20

    def renderCell(self, item):
        """Display the description just under the pretty link."""
        obj = self._getObject(item)
        pl = self.getPrettyLink(obj)
        # if preview is enabled, display a specific icon if element is converted
        preview = ''
        tool = api.portal.get_tool('portal_plonemeeting')
        if tool.auto_convert_annexes() and IIconifiedPreview(obj).converted:
            preview = self._preview_html(obj)
        # display description if any
        description = u'<p class="discreet">{0}</p>'.format(item.Description)
        return pl + preview + description

    def _preview_html(self, obj):
        """ """
        portal = api.portal.get()
        return u"""<a href="{0}"
           title="{1}"
           target="_blank">
          <img src="{2}" />
        </a>""".format(obj.absolute_url() + '/documentviewer#document/p1',
                       translate('Preview',
                                 domain='collective.iconifiedcategory',
                                 context=obj.REQUEST),
                       portal.absolute_url() + '/file_icon.png')


class AuthorColumn(MemberIdColumn):
    """ """
    weight = IconifiedAuthorColumn.weight
    header = IconifiedAuthorColumn.header


class ActionsColumn(DashboardActionsColumn):
    header = u'Actions'
    weight = 100
    params = {'showHistory': False, 'showActions': True, 'showArrows': True}
