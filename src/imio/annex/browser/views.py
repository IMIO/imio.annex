# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from collective.eeafaceted.batchactions import _ as _CEBA
from collective.eeafaceted.batchactions.browser.views import BaseBatchActionForm
from collective.iconifiedcategory.config import get_sort_categorized_tab
from collective.iconifiedcategory.utils import calculate_filesize
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.annex import _
from imio.annex import logger
from imio.annex.content.annex import IAnnex
from imio.annex.widgets.checkbox import AnnexesCheckBoxFieldWidget
from io import BytesIO
from plone import api
from plone.rfc822.interfaces import IPrimaryFieldInfo
from Products.CMFPlone.utils import safe_unicode
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from PyPDF2.utils import PdfReadError
from z3c.form import button
from z3c.form import form as z3c_form
from z3c.form.browser.radio import RadioFieldWidget
from z3c.form.field import Fields
from zope import schema
from zope.i18n import translate

import zipfile


class DownloadAnnexesBatchActionForm(BaseBatchActionForm):

    label = _CEBA("download-annexes-batch-action-but")
    button_with_icon = True
    apply_button_title = _CEBA('Download')
    section = "annexes"
    # gives a human readable size of "50.0 Mb"
    MAX_TOTAL_SIZE = 52428800

    def _max_total_size(self):
        """ """
        return self.MAX_TOTAL_SIZE

    @property
    def description(self):
        """ """
        descr = super(DownloadAnnexesBatchActionForm, self).description
        descr = translate(descr, domain=descr.domain, context=self.request)
        if self.total_size > self._max_total_size():
            readable_max_size = calculate_filesize(self._max_total_size())
            descr += translate(
                '<p class="warn_filesize">The maximum size you may download at '
                'one time is ${max_size}, here your download size is ${total_size}. '
                'Please unselect some elements, especially large elements for '
                'which size is displayed in red, download it separately.<p>',
                mapping={'max_size': readable_max_size,
                         'total_size': calculate_filesize(self.total_size)},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
        elif self.annex_not_downloadable is not None:
            descr += translate(
                '<p style="color: red;">You selected some elements that are '
                'not downloadable, check for example "${annex_title}". '
                'Please unselect elements that are only previewable.</p>',
                mapping={'annex_title': self.annex_not_downloadable.Title()},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
        else:
            descr += translate(
                '<p>This will download the selected elements as a Zip file.</p>'
                '<p>The total file size is <b>${total_size}</b>, when clicking '
                'on "${button_title}", you will have a spinner, wait until the '
                'Zip file is available.</p>',
                mapping={
                    'total_size': calculate_filesize(self.total_size),
                    'button_title': translate(
                        self.apply_button_title,
                        domain="collective.eeafaceted.batchactions",
                        context=self.request)},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
        return descr

    def _check_annex_not_downloadable(self):
        """ """
        self.annex_not_downloadable = None
        for brain in self.brains:
            obj = brain.getObject()
            if not obj.show_download():
                self.annex_not_downloadable = obj
                self.do_apply = False
                return

    def _check_total_size(self):
        """ """
        self.total_size = self._total_size()
        if self.total_size > self._max_total_size():
            self.do_apply = False

    def _total_size(self):
        """ """
        total = 0
        for brain in self.brains:
            obj = brain.getObject()
            primary_field = IPrimaryFieldInfo(obj)
            size = primary_field.value.size
            total += size
        return total

    def _update(self):
        """Can not apply action if total size exceeded."""
        self._check_total_size()
        if self.do_apply:
            self._check_annex_not_downloadable()

    def available(self):
        """ """
        return True

    def zipfiles(self, content):
        """Return zipped content."""
        fstream = BytesIO()
        zipper = zipfile.ZipFile(fstream, 'w', zipfile.ZIP_DEFLATED)
        for obj in content:
            if not IAnnex.providedBy(obj):
                continue
            primary_field = IPrimaryFieldInfo(obj)
            data = primary_field.value.data
            filename = primary_field.value.filename
            # can not do without a filename...
            if not filename:
                continue
            zipper.writestr(filename, data)
            created = obj.created()
            zipper.NameToInfo[filename].date_time = (
                created.year(),
                created.month(),
                created.day(),
                created.hour(),
                created.minute(),
                int(created.second()))
        zipper.close()
        return fstream.getvalue()

    def _apply(self, **data):
        """ """
        try:
            return self.do_zip()
        except zipfile.LargeZipFile:
            message = "Too much annexes to zip, try selecting fewer annexes..."
            api.portal.show_message(message, self.request, type="error")
            return self.request.response.redirect(self.context.absolute_url())

    def do_zip(self):
        """ Zip all of the content in this location (context)"""
        self.request.response.setHeader('Content-Type', 'application/zip')
        self.request.response.setHeader(
            'Content-disposition', 'attachment;filename=%s.zip'
            % self.context.getId())
        content = [brain.getObject() for brain in self.brains]
        zipped_content = self.zipfiles(content)
        self.request.set('zip_file_content', zipped_content)
        return zipped_content

    def render(self):
        """ """
        if 'zip_file_content' in self.request:
            return self.request['zip_file_content']
        else:
            return super(DownloadAnnexesBatchActionForm, self).render()


class ConcatenateAnnexesBatchActionForm(BaseBatchActionForm):

    label = _CEBA("concatenate-annexes-batch-action-but")
    button_with_icon = True
    apply_button_title = _CEBA('Download')
    # gives a human readable size of "75.0 Mb"
    MAX_TOTAL_SIZE = 78643200

    def _max_total_size(self):
        """ """
        return self.MAX_TOTAL_SIZE

    @property
    def description(self):
        """ """
        descr = super(ConcatenateAnnexesBatchActionForm, self).description
        descr = translate(descr, domain=descr.domain, context=self.request)
        readable_max_size = calculate_filesize(self._max_total_size())
        descr += translate(
            'concatenate_annexes_batch_action_descr',
            mapping={'max_size': readable_max_size, },
            domain="collective.eeafaceted.batchactions",
            context=self.request)
        return descr

    def _annex_types_vocabulary(self):
        """The name of the vocabulary factory to use for annex_types field."""
        return "collective.iconifiedcategory.every_category_uids"

    def _update(self):
        self.fields += Fields(
            schema.List(
                __name__='annex_types',
                title=_(u'Annex types'),
                value_type=schema.Choice(
                    vocabulary=self._annex_types_vocabulary()),
                required=True),
            schema.Bool(__name__='two_sided',
                        title=_(u'Two-sided?'),
                        description=_(u'descr_two_sided'),
                        default=False,
                        required=False),
        )
        self.fields["annex_types"].widgetFactory = AnnexesCheckBoxFieldWidget
        self.fields["two_sided"].widgetFactory = RadioFieldWidget

    def _total_size(self, annexes):
        """ """
        total = 0
        for annex in annexes:
            primary_field = IPrimaryFieldInfo(annex)
            size = primary_field.value.size
            total += size
        return total

    def _error_obj_title(self, obj):
        """ """
        return obj.Title()

    def _apply(self, **data):
        """ """
        annex_type_uids = data['annex_types']
        # get annexes
        annexes = []
        sort_on = 'getObjPositionInParent' if \
            get_sort_categorized_tab() is False else None
        for brain in self.brains:
            obj = brain.getObject()
            filters = {'contentType': 'application/pdf'}
            for annex_type_uid in annex_type_uids:
                filters['category_uid'] = annex_type_uid
                annexes += get_categorized_elements(
                    obj,
                    result_type='objects',
                    sort_on=sort_on,
                    filters=filters)
        # return if nothing to produce
        if not annexes:
            api.portal.show_message(
                _("Nothing to export."),
                request=self.request)
            return
        # can not generate if total size too large
        total_size = self._total_size(annexes)
        if self._total_size(annexes) > self._max_total_size():
            api.portal.show_message(
                _("concatenate_annexes_pdf_too_large_error",
                  mapping={'total_size': calculate_filesize(total_size),
                           'max_total_size': calculate_filesize(
                           self._max_total_size())}),
                request=self.request,
                type="error")
            return
        # create unique PDF file
        output_writer = PdfFileWriter()
        for annex in annexes:
            try:
                output_writer.appendPagesFromReader(
                    PdfFileReader(BytesIO(annex.file.data), strict=False))
            except PdfReadError as exc:
                api.portal.show_message(
                    _("concatenate_annexes_pdf_read_error",
                      mapping={'annex_title': safe_unicode(annex.Title()),
                               'obj_title': safe_unicode(
                          self._error_obj_title(annex.aq_inner.aq_parent))}),
                    request=self.request,
                    type="error")
                logger.exception(exc)
                self.request.set(
                    'concatenate_annexes_item_pdf_error_url', obj.absolute_url())
                return
            if data['two_sided'] and \
               output_writer.getNumPages() % 2 != 0 and \
               annex != annexes[-1]:
                output_writer.addBlankPage()
        pdf_file_content = BytesIO()
        output_writer.write(pdf_file_content)
        self.request.set('pdf_file_content', pdf_file_content)
        return pdf_file_content

    def render(self):
        if 'pdf_file_content' in self.request:
            filename = "%s-annexes.pdf" % self.context.getId()
            self.request.response.setHeader('Content-Type', 'application/pdf')
            self.request.response.setHeader(
                'Content-disposition', 'attachment; filename=%s' % filename)
            pdf_file_content = self.request['pdf_file_content']
            pdf_file_content.seek(0)
            return pdf_file_content.read()
        elif self.request.RESPONSE.status == 204:
            # return something so the faceted is refrehsed
            return self.request.get('concatenate_annexes_pdf_error_url')
        return super(ConcatenateAnnexesBatchActionForm, self).render()


class ExportPDFForm(z3c_form.Form):
    """Concatenate selected elements of context into a single PDF."""

    # name of the vocabulary listing the selectable elements, subclasses may change it
    vocabulary = u"imio.annex.export_pdf_elements"

    ignoreContext = True  # don't use context to get widget data

    label = _(u"Export PDF")
    description = _('export_pdf_descr')
    _finished = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.fields = Fields(
            schema.List(
                __name__="elements",
                title=_(u"Elements to export in PDF"),
                description=_(u""),
                required=False,
                value_type=schema.Choice(vocabulary=self.vocabulary)),
            schema.Bool(
                __name__="two_sided",
                title=_(u'Two-sided?'),
                description=_(u'descr_two_sided'),
                default=False,
                required=False),
        )
        self.fields["elements"].widgetFactory = AnnexesCheckBoxFieldWidget
        self.fields["two_sided"].widgetFactory = RadioFieldWidget

    @button.buttonAndHandler(_('Apply'), name='apply')
    def handleApply(self, action):
        self._check_auth()
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._check_data(data)
        return self._do_export_pdf(data)

    def updateWidgets(self):
        super(ExportPDFForm, self).updateWidgets()
        self.widgets['elements'].sortable = True

    def _check_data(self, data):
        """Make sure elements are selectable.
           As some values are disabled in the UI, a user could try
           to surround this, raise Unauthorized in this case."""
        selectable = [term.token for term in self.widgets['elements'].terms
                      if not getattr(term, 'disabled', False)]
        for elt_id in data['elements']:
            if elt_id not in selectable:
                raise Unauthorized

    def _elements_content(self, data):
        """Return {element_id: PDF binary content}, by default every
           selected element is an annex contained in the context."""
        return {element_id: self.context.get(element_id).file.data
                for element_id in data['elements']}

    def _do_export_pdf(self, data):
        content = self._elements_content(data)
        # create unique PDF file
        output_writer = PdfFileWriter()
        for element_id in data['elements']:
            output_writer.appendPagesFromReader(
                PdfFileReader(BytesIO(content[element_id]), strict=False))
            # keep every element starting on a recto
            if data.get('two_sided') and \
               output_writer.getNumPages() % 2 != 0 and \
               element_id != data['elements'][-1]:
                output_writer.addBlankPage()
        pdf_file_content = BytesIO()
        output_writer.write(pdf_file_content)
        self.request.set('pdf_file_content', pdf_file_content)
        return pdf_file_content

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        self._finished = True

    def update(self):
        self._check_auth()
        super(ExportPDFForm, self).update()
        # after calling parent's update, self.actions are available
        self.actions.get('cancel').addClass('standalone')

    def _may_export(self):
        """Hook, may current user export context elements to PDF?
           View permission is already checked by the browser:page."""
        return True

    def _check_auth(self):
        """Raise Unauthorized if current user may not export to PDF."""
        if not self._may_export():
            raise Unauthorized

    def _redirect(self, url):
        """Hook, redirect to p_url."""
        self.request.response.redirect(url)

    def render(self):
        if 'pdf_file_content' in self.request:
            filename = "export_pdf_%s" % self.context.getId()
            self.request.response.setHeader('Content-Type', 'application/pdf')
            self.request.response.setHeader(
                'Content-disposition', 'attachment;filename=%s.pdf' % filename)
            pdf_file_content = self.request['pdf_file_content']
            pdf_file_content.seek(0)
            return pdf_file_content.read()

        if self._finished:
            self._redirect(self.context.absolute_url())
            return ""
        return super(ExportPDFForm, self).render()
