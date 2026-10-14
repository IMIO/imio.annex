# -*- coding: utf-8 -*-
"""Init and utils."""

from zope.i18nmessageid import MessageFactory

import logging


_ = MessageFactory("imio.annex")
logger = logging.getLogger("imio.annex")

# collective.documentviewer is not part of the Plone 6 setup (pdf viewer not decided yet)
try:
    import collective.documentviewer  # noqa: F401
except ImportError:
    HAS_DOCUMENTVIEWER = False
else:
    HAS_DOCUMENTVIEWER = True
