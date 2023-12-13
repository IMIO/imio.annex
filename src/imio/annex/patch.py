# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from collective.documentviewer.async import JobRunner
from collective.documentviewer.convert import Converter
from imio.annex.events import ConversionStartedEvent
from imio.annex.events import ConversionReallyFinishedEvent
from zope.event import notify


def converter_call(self, *args, **kwargs):
    notify(ConversionStartedEvent(self.context))
    res = Converter._old___call__(self, *args, **kwargs)
    # in collective.documentviewer, ConversionFinishedEvent is called before
    # information "converting" is set back to "False", we need to have it
    # to update the preview_status
    notify(ConversionReallyFinishedEvent(self.context))
    return res


def jobrunner_queue_it(self):
    JobRunner._old_queue_it(self)
    notify(ConversionStartedEvent(self.object))
