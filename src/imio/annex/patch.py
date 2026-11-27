# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from collective.documentviewer.convert import Converter
from imio.annex.events import ConversionReallyFinishedEvent
from imio.annex.events import ConversionStartedEvent
from Products.CMFCore.WorkflowTool import WorkflowTool
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
    self._old_queue_it()
    notify(ConversionStartedEvent(self.object))


def reindex_workflow_variables(self, ob):
    """Do nothing for an element without workflow variables, so without workflow
    (annexes, File, Image, ...).  When an element is added, it is called by
    WorkflowTool.notifyCreated and was doing a complete reindex
    (reindexObject(idxs=[]) reindexes every indexes and metadata) right before
    the complete index done by CMFCatalogAware.handleContentishEvent."""
    if not self.getCatalogVariablesFor(ob):
        return
    return WorkflowTool._old__reindexWorkflowVariables(self, ob)
