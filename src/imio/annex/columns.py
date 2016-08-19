# -*- coding: utf-8 -*-
from imio.dashboard.columns import ActionsColumn as DashboardActionsColumn


class ActionsColumn(DashboardActionsColumn):
    header = u'Actions'
    weight = 100
    params = {'showHistory': False, 'showActions': True}
