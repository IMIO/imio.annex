# -*- coding: utf-8 -*-

from collective.dms.scanbehavior.behaviors.behaviors import IScanFields
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import alsoProvides


class IScanFieldsHiddenToSignAndSigned(IScanFields):

    form.omitted('to_sign')
    form.omitted('signed')

alsoProvides(IScanFieldsHiddenToSignAndSigned, IFormFieldProvider)
