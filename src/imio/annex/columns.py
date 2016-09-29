# -*- coding: utf-8 -*-
from imio.dashboard.columns import ActionsColumn as DashboardActionsColumn
from imio.dashboard.columns import PrettyLinkColumn as DashboardPrettyLinkColumn


class ActionsColumn(DashboardActionsColumn):
    header = u'Actions'
    weight = 100
    params = {'showHistory': False, 'showActions': True, 'showArrows': True}


class PrettyLinkColumn(DashboardPrettyLinkColumn):
    header = u'Title'
    weight = 20
