# -*- coding: utf-8 -*-
"""Init and utils."""

from plone import api
from zope.i18nmessageid import MessageFactory

import logging


_ = MessageFactory('imio.annex')
logger = logging.getLogger('imio.annex')

HAS_PLONE_6 = int(api.env.plone_version()[0]) >= 6
