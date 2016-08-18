# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from zope.component.interfaces import ObjectEvent
from zope.interface import implements

from imio.annex.interfaces import IAnnexFileChangedEvent


class AnnexFileChangedEvent(ObjectEvent):
    implements(IAnnexFileChangedEvent)

    def __init__(self, object, file):
        super(AnnexFileChangedEvent, self).__init__(object)
        self.file = file
