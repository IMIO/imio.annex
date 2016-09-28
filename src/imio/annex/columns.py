# -*- coding: utf-8 -*-
from collective.iconifiedcategory.interfaces import IIconifiedPreview
from imio.dashboard.columns import ActionsColumn as DashboardActionsColumn
from imio.dashboard.columns import PrettyLinkColumn as DashboardPrettyLinkColumn


class ActionsColumn(DashboardActionsColumn):
    header = u'Actions'
    weight = 100
    params = {'showHistory': False, 'showActions': True, 'showArrows': True}


class PrettyLinkColumn(DashboardPrettyLinkColumn):
    header = u'Title'
    weight = 20

    def renderCell(self, obj):
        if IIconifiedPreview(obj.getObject()).converted is True:
            self.params['target'] = '_blank'
            self.params['appendToUrl'] = '/documentviewer#document/p1'
        return super(PrettyLinkColumn, self).renderCell(obj)
