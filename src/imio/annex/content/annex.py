# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from plone.app.contenttypes.interfaces import IFile
from plone.dexterity.content import Item
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import implements

from imio.annex import _


class IAnnex(model.Schema, IFile):
    """Schema for Annex content type"""
    title = schema.TextLine(
        title=_(u'Title'),
        required=False
    )

    model.primary('file')
    file = NamedBlobFile(
        title=_(u'File'),
        required=True,
    )


class Annex(Item):
    """Annex content type"""
    implements(IAnnex)


class AnnexSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Annex"""

    def bases(self, schema_name, tree):
        return (IAnnex, )
