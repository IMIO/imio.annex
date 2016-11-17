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

    def renderCell(self, item):
        """Display the description just under the pretty link."""
        pl = self.getPrettyLink(self._getObject(item))
        description = '<p class="discreet">{0}</p>'.format(item.Description)
        return pl + description
