# -*- coding: utf-8 -*-

from collective.dms.scanbehavior.behaviors.behaviors import IScanFields
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import alsoProvides


class IScanFieldsHiddenToSignAndSigned(IScanFields):
    """Must be removed once there is no more usage of this behavior"""


alsoProvides(IScanFieldsHiddenToSignAndSigned, IFormFieldProvider)
