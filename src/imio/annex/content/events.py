# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from collective.documentviewer.settings import GlobalSettings
from collective.documentviewer.utils import allowedDocumentType
from plone import api
from zope.event import notify

from imio.annex.events import AnnexFileChangedEvent
from imio.annex.content.annex import IAnnex


def annex_content_created(event):
    obj = event.object
    if not IAnnex.providedBy(obj):
        return
    notify(AnnexFileChangedEvent(obj, obj.file))


def annex_content_updated(event):
    obj = event.object
    if not IAnnex.providedBy(obj):
        return
    if obj.file._blob._p_blob_uncommitted is not None:
        notify(AnnexFileChangedEvent(obj, obj.file))


def annex_file_changed(event):
    obj = event.object
    settings = GlobalSettings(api.portal.get())
    if not allowedDocumentType(obj, settings.auto_layout_file_types):
        return
    # do something?
