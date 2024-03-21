# -*- coding: utf-8 -*-

from collective.eeafaceted.batchactions import _ as _CEBA
from collective.eeafaceted.batchactions.browser.views import BaseBatchActionForm
from collective.iconifiedcategory.config import get_sort_categorized_tab
from collective.iconifiedcategory.utils import calculate_filesize
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.annex import _
from imio.annex.content.annex import IAnnex
from io import BytesIO
from plone import api
from plone.rfc822.interfaces import IPrimaryFieldInfo
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from z3c.form.field import Fields
from zope import schema
from zope.i18n import translate

import zipfile


class DownloadAnnexesBatchActionForm(BaseBatchActionForm):

    label = _CEBA("Download annexes")
    button_with_icon = True
    apply_button_title = _CEBA('download-annexes-batch-action-but')
    section = "annexes"
    # gives a human readable size of "25.0 Mb"
    MAX_TOTAL_SIZE = 26214400

    @property
    def description(self):
        """ """
        descr = super(DownloadAnnexesBatchActionForm, self).description
        descr = translate(descr, domain=descr.domain, context=self.request)
        readable_total_size = calculate_filesize(self.total_size)
        readable_max_size = calculate_filesize(self.MAX_TOTAL_SIZE)
        if self.total_size > self.MAX_TOTAL_SIZE:
            descr += translate(
                '<p class="warn_filesize">The maximum size you may download at one '
                'time is ${max_size}, here your download size is ${total_size}. '
                'Please unselect some elements, especially large elements for which '
                'size is displayed in red, download it separately.<p>',
                mapping={'max_size': readable_max_size,
                         'total_size': readable_total_size},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
            self.do_apply = False
        else:
            descr += translate(
                '<p>This will download the selected elements as a Zip file.</p>'
                '<p>The total file size is <b>${total_size}</b>, when clicking on '
                '"${button_title}", you will have a spinner, wait until the Zip file '
                'is available.</p>',
                mapping={
                    'total_size': readable_total_size,
                    'button_title': translate(
                        'download-annexes-batch-action-but',
                        domain="collective.eeafaceted.batchactions",
                        context=self.request)},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
        return descr

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
        self.total_size = self._total_size()
        if self.total_size > self.MAX_TOTAL_SIZE:
            self.do_apply = False

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
                created.year(), created.month(), created.day(), created.hour(), created.minute(),
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
        self.request.response.setHeader('Content-disposition', 'attachment;filename=%s.zip'
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

    label = _CEBA("Concatenate annexes for selected elements")
    button_with_icon = True
    button_with_icon = True
    apply_button_title = _CEBA('concatenate-annexes-batch-action-but')
    # gives a human readable size of "50.0 Mb"
    MAX_TOTAL_SIZE = 52428800

    @property
    def description(self):
        """ """
        descr = super(ConcatenateAnnexesBatchActionForm, self).description
        descr = translate(descr, domain=descr.domain, context=self.request)
        readable_max_size = calculate_filesize(self.MAX_TOTAL_SIZE)
        descr += translate(
            '<p>Warning, this will concatenate PDF annexes into one single PDF '
            'file with a limit of ${max_size}.  If your PDF file is not complete '
            'you will have a message, in this case select less elements and '
            'download it separately.<p>',
            mapping={'max_size': readable_max_size, },
            domain="collective.eeafaceted.batchactions",
            context=self.request)
        return descr

    def available(self):
        """ """
        return True

    def _update(self):
        self.fields += Fields(
            schema.Choice(
                __name__='annex_type',
                title=_(u'Annex type'),
                vocabulary='Products.PloneMeeting.vocabularies.item_annex_types_vocabulary',
                required=False),
            schema.Bool(__name__='two_sided',
                        title=_(u'Two-sided?'),
                        ),
        )

    def _apply(self, **data):
        """ """
        annex_type_uid = data['annex_type']
        # get annexes
        annexes = []
        sort_on = 'getObjPositionInParent' if \
            get_sort_categorized_tab() is False else None
        for brain in self.brains:
            item = brain.getObject()
            filters = {'contentType': 'application/pdf'}
            if annex_type_uid:
                filters['category_uid'] = annex_type_uid
            annexes += get_categorized_elements(
                item,
                result_type='objects',
                sort_on=sort_on,
                filters=filters)
        # create unique PDF file
        output_writer = PdfFileWriter()
        for annex in annexes:
            output_writer.appendPagesFromReader(
                PdfFileReader(BytesIO(annex.file.data)))
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
            self.request.response.setHeader('Content-disposition', 'attachment; filename=%s'
                                            % filename)
            pdf_file_content = self.request['pdf_file_content']
            pdf_file_content.seek(0)
            return pdf_file_content.read()
        return super(ConcatenateAnnexesBatchActionForm, self).render()
