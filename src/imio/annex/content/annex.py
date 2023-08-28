# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from imio.annex import _
from plone.app.contenttypes.content import File
from plone.app.contenttypes.interfaces import IFile
from plone.app.dexterity import PloneMessageFactory as _PMF
from plone.autoform import directives as form
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from plone.uuid.interfaces import ATTRIBUTE_NAME
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope import schema
from zope.interface import implements


class IAnnex(model.Schema, IFile):
    """Schema for Annex content type"""

    title = schema.TextLine(
        title=_PMF(u'label_title', default=u'Title'),
        required=False,
    )

    description = schema.Text(
        title=_PMF(u'label_description', default=u'Summary'),
        description=_PMF(
            u'help_description',
            default=u'Used in item listings and search results.'
        ),
        required=False,
        missing_value=u'',
    )

    form.order_before(description='*')
    form.order_before(title='*')

    form.omitted('title', 'description')
    form.no_omit(IEditForm, 'title', 'description')
    form.no_omit(IAddForm, 'title', 'description')

    model.primary('file')
    file = NamedBlobFile(
        title=_(u'File'),
        required=True,
    )


class Annex(File):
    """Annex content type"""
    implements(IAnnex)

    def UID(self):
        """Speedup getting UID."""
        return getattr(self, ATTRIBUTE_NAME)

    def show_download(self):
        """Condition to show the "Download" action."""
        res = True
        parent = self.aq_parent
        element = parent.categorized_elements[self.UID()]
        # preview with protected download
        if element['show_preview'] == 2:
            infos = parent.unrestrictedTraverse('@@categorized-childs-infos')
            res = infos.show_download(element)
        return res

    def show_preview(self):
        """Condition to show the "Preview" action."""
        return self.aq_parent.categorized_elements[self.UID()]['preview_status'] == 'converted'


class AnnexSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Annex"""

    def bases(self, schema_name, tree):
        return (IAnnex, )
