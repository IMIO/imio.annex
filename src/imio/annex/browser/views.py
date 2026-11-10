# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from cgi import escape
from collective.eeafaceted.batchactions import _ as _CEBA
from collective.eeafaceted.batchactions.browser.views import BaseBatchActionForm
from collective.iconifiedcategory.config import get_sort_categorized_tab
from collective.iconifiedcategory.utils import calculate_filesize
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.annex import _
from imio.annex import logger
from imio.annex.content.annex import IAnnex
from imio.annex.widgets.checkbox import OrderableCheckBoxFieldWidget
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
from zope.component import getUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

import os
import re
import zipfile


class DownloadAnnexesBatchActionForm(BaseBatchActionForm):
    """Download selected annexes as a Zip file.
       This is meant to be used on the "annexes" tab of an element,
       selected elements (brains) are annexes."""

    label = _CEBA("download-annexes-batch-action-but")
    button_with_icon = True
    apply_button_title = _CEBA('Download')
    section = "annexes"
    # gives a human readable size of "250.0 Mb"
    MAX_TOTAL_SIZE = 262144000
    annexes = []
    annex_not_downloadable = None

    def _max_total_size(self):
        """ """
        return self.MAX_TOTAL_SIZE

    @property
    def description(self):
        """ """
        descr = super(DownloadAnnexesBatchActionForm, self).description
        descr = translate(descr, domain=descr.domain, context=self.request)
        if self.total_size > self._max_total_size():
            descr += self._max_size_message(self.total_size)
        elif self.annex_not_downloadable is not None:
            descr += translate(
                '<p style="color: red;">You selected some elements that are '
                'not downloadable, check for example "${annex_title}". '
                'Please unselect elements that are only previewable.</p>',
                mapping={'annex_title': self.annex_not_downloadable.Title()},
                domain="collective.eeafaceted.batchactions",
                context=self.request)
        elif not self.annexes:
            descr += translate(
                '<p style="color: red;">There is no downloadable annex '
                'in the selected elements.</p>',
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

    def _max_size_message(self, total_size):
        """Message displayed when p_total_size exceeds the max total size."""
        return translate(
            '<p class="warn_filesize">The maximum size you may download at '
            'one time is ${max_size}, here your download size is ${total_size}. '
            'Please unselect some elements, especially large elements for '
            'which size is displayed in red, download it separately.<p>',
            mapping={'max_size': calculate_filesize(self._max_total_size()),
                     'total_size': calculate_filesize(total_size)},
            domain="collective.eeafaceted.batchactions",
            context=self.request)

    def _get_annexes(self):
        """Return the annexes to download.
           Here, selected elements are the annexes."""
        return [brain.getObject() for brain in self.brains]

    def _check_annex_not_downloadable(self):
        """ """
        self.annex_not_downloadable = None
        for annex in self.annexes:
            if not annex.show_download():
                self.annex_not_downloadable = annex
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
        for annex in self.annexes:
            primary_field = IPrimaryFieldInfo(annex)
            size = primary_field.value.size
            total += size
        return total

    def _update(self):
        """Can not apply action if total size exceeded,
           if an annex is not downloadable or if there is nothing to download."""
        self.annexes = self._get_annexes()
        self.annex_not_downloadable = None
        self._check_total_size()
        if self.do_apply:
            self._check_annex_not_downloadable()
        if not self.annexes:
            self.do_apply = False

    def available(self):
        """ """
        return True

    def _zip_filename(self):
        """The name of the generated Zip file."""
        return '%s.zip' % self.context.getId()

    def _zip_path(self, annex):
        """The path of p_annex in the Zip file."""
        return safe_unicode(IPrimaryFieldInfo(annex).value.filename)

    def _unique_zip_path(self, path, used_paths):
        """Make sure p_path is unique in the Zip file,
           if it already exists, add a suffix "-1", "-2", ..."""
        unique_path = path
        base, ext = os.path.splitext(path)
        i = 1
        while unique_path in used_paths:
            unique_path = u'{0}-{1}{2}'.format(base, i, ext)
            i += 1
        used_paths.add(unique_path)
        return unique_path

    def zipfiles(self, content):
        """Return zipped content."""
        fstream = BytesIO()
        zipper = zipfile.ZipFile(fstream, 'w', zipfile.ZIP_DEFLATED)
        used_paths = set()
        for obj in content:
            if not IAnnex.providedBy(obj):
                continue
            primary_field = IPrimaryFieldInfo(obj)
            # can not do without a filename...
            if not primary_field.value.filename:
                continue
            path = self._unique_zip_path(self._zip_path(obj), used_paths)
            created = obj.created()
            zinfo = zipfile.ZipInfo(
                path,
                date_time=(created.year(),
                           created.month(),
                           created.day(),
                           created.hour(),
                           created.minute(),
                           int(created.second())))
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            zinfo.external_attr = 0o600 << 16
            zipper.writestr(zinfo, primary_field.value.data)
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
        """ Zip annexes returned by self._get_annexes"""
        self.request.response.setHeader('Content-Type', 'application/zip')
        self.request.response.setHeader(
            'Content-disposition', 'attachment;filename=%s'
            % self._zip_filename())
        zipped_content = self.zipfiles(self.annexes)
        self.request.set('zip_file_content', zipped_content)
        return zipped_content

    def render(self):
        """ """
        if 'zip_file_content' in self.request:
            return self.request['zip_file_content']
        else:
            return super(DownloadAnnexesBatchActionForm, self).render()


class DownloadElementsAnnexesBatchActionForm(DownloadAnnexesBatchActionForm):
    """Download annexes of selected elements as a Zip file.
       This is meant to be used on a dashboard of elements containing annexes,
       selected elements (brains) are the elements containing the annexes.
       Field "annexes" lists the annexes of selected elements, using the
       "annexes_vocabulary", the user selects the annexes to download,
       annexes the current user may not download (only previewable)
       are disabled.
       By default every annexes are stored at the root of the Zip file,
       when "annexes_by_folder" is selected, annexes of each element are
       stored in a separate folder of the Zip file."""

    label = _CEBA("download-elements-annexes-batch-action-but")
    section = "default"
    # vocabulary used to list the annexes of every selected element
    annexes_vocabulary = u"imio.annex.contained_annexes"
    annexes_terms = []
    annexes_by_folder = False
    # max length of a folder name or filename prefix in the Zip file
    MAX_ZIP_NAME_LENGTH = 80

    def _update(self):
        """Add the "annexes" and "annexes_by_folder" fields.
           Fields are computed from the class fields so calling update
           several times does not add the fields several times."""
        super(DownloadElementsAnnexesBatchActionForm, self)._update()
        self.fields = type(self).fields + Fields(
            schema.List(
                __name__='annexes',
                title=_(u'Annexes to download'),
                value_type=schema.Choice(
                    vocabulary=SimpleVocabulary(self.annexes_terms)),
                default=[annex.UID() for annex in self.annexes],
                required=True),
            schema.Bool(__name__='annexes_by_folder',
                        title=_(u'Annexes by folder?'),
                        description=_(u'descr_annexes_by_folder'),
                        default=False,
                        required=False),
        )
        self.fields["annexes"].widgetFactory = OrderableCheckBoxFieldWidget
        self.fields["annexes_by_folder"].widgetFactory = RadioFieldWidget

    def _check_total_size(self):
        """Do not disable the action when total size is exceeded so the user
           can unselect some annexes, size of selected annexes is checked
           in _apply."""
        self.total_size = self._total_size()

    def _selected_annexes(self, annex_uids):
        """Return selected annexes, make sure every selected annex is
           selectable (disabled terms are not)."""
        annexes_by_uid = {annex.UID(): annex for annex in self.annexes}
        if set(annex_uids).difference(annexes_by_uid):
            raise Unauthorized
        return [annexes_by_uid[annex_uid] for annex_uid in annex_uids]

    def _apply(self, **data):
        """Only download selected annexes, if "annexes" not given,
           every downloadable annexes are downloaded."""
        if data.get('annexes') is not None:
            self.annexes = self._selected_annexes(data['annexes'])
        total_size = self._total_size()
        if total_size > self._max_total_size():
            api.portal.show_message(
                _("download_annexes_zip_too_large_error",
                  mapping={'total_size': calculate_filesize(total_size),
                           'max_total_size': calculate_filesize(
                               self._max_total_size())}),
                request=self.request,
                type="error")
            return
        self.annexes_by_folder = bool(data.get('annexes_by_folder'))
        return super(DownloadElementsAnnexesBatchActionForm, self)._apply(**data)

    def _annexes_filters(self):
        """Filters passed to the annexes vocabulary to select annexes."""
        return {}

    def _element_terms(self, element, **kwargs):
        """Terms of the annexes of p_element, term token is the annex UID,
           p_kwargs are passed to the annexes vocabulary."""
        factory = getUtility(IVocabularyFactory, self.annexes_vocabulary)
        kwargs.setdefault('filters', self._annexes_filters())
        return list(factory(element,
                            token_value='UID',
                            include_parent_title=True,
                            **kwargs))

    def _get_annexes(self):
        """Return the downloadable annexes of every selected elements,
           store the annexes vocabulary terms in self.annexes_terms."""
        self.annexes_terms = []
        annexes = []
        for brain in self.brains:
            obj = brain.getObject()
            categorized_elements = getattr(obj, 'categorized_elements', {})
            for term in self._element_terms(obj):
                self.annexes_terms.append(term)
                if getattr(term, 'disabled', False):
                    continue
                annex = obj.get(categorized_elements[term.token]['id'])
                if IAnnex.providedBy(annex):
                    annexes.append(annex)
        return annexes

    def _check_annex_not_downloadable(self):
        """Not downloadable annexes are disabled in the annexes vocabulary."""
        self.annex_not_downloadable = None

    def _zip_folder_name(self, element):
        """The name of the folder in which annexes of p_element are stored
           when "annexes_by_folder"."""
        return element.getId()

    def _zip_filename_prefix(self, element):
        """A prefix added to the filename of annexes of p_element
           when not "annexes_by_folder", None means no prefix."""
        return None

    def _safe_zip_name(self, name):
        """Make p_name usable as a folder name or filename prefix:
           remove characters not allowed in filenames (like "/" that would
           create a sub folder) and limit the length."""
        name = u' '.join(safe_unicode(name).split())
        name = re.sub(u'[\\x00-\\x1f/\\\\:*?"<>|]', u'-', name)
        return name[:self.MAX_ZIP_NAME_LENGTH].strip().rstrip(u'.')

    def _zip_path(self, annex):
        """Store annexes in a folder by element if "annexes_by_folder",
           otherwise prefix the filename if _zip_filename_prefix."""
        path = super(DownloadElementsAnnexesBatchActionForm, self)._zip_path(annex)
        element = annex.aq_inner.aq_parent
        if self.annexes_by_folder:
            path = u'{0}/{1}'.format(
                self._safe_zip_name(self._zip_folder_name(element)), path)
        else:
            prefix = self._zip_filename_prefix(element)
            if prefix:
                path = u'{0} - {1}'.format(self._safe_zip_name(prefix), path)
        return path


class ConcatenateAnnexesBatchActionForm(BaseBatchActionForm):

    label = _CEBA("concatenate-annexes-batch-action-but")
    button_with_icon = True
    apply_button_title = _CEBA('Download')
    # gives a human readable size of "75.0 Mb"
    MAX_TOTAL_SIZE = 78643200
    # set to True to exclude selected elements with _check_element and display it
    CHECK_ELEMENTS = False

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
        excluded = self._excluded_elements()
        if not excluded:
            return descr
        items = u"".join(
            u'<li><a href="%s" target="_blank">%s</a> : %s</li>'
            % (obj.absolute_url(), escape(safe_unicode(obj.Title())), translate(reason, context=self.request))
            for obj, reason in excluded)
        return u'%s<div class="portalMessage warning"><p>%s</p><ul>%s</ul></div>' % (
            descr,
            translate(_(u"These elements will not be exported:"), context=self.request),
            items)

    def _check_element(self, obj):
        """Return the reason why selected p_obj is excluded from the export, None if it is exported."""
        return None

    def _excluded_elements(self):
        """Return [(obj, reason)] of the selected elements excluded from the export, computed once."""
        if not self.CHECK_ELEMENTS:
            return []
        if getattr(self, "_excluded", None) is None:
            self._excluded = []
            for brain in self.brains:
                obj = brain.getObject()
                reason = self._check_element(obj)
                if reason:
                    self._excluded.append((obj, reason))
        return self._excluded

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
        self.fields["annex_types"].widgetFactory = OrderableCheckBoxFieldWidget
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

    def _element_annexes(self, obj, data):
        """Return the annexes of p_obj to concatenate, by default the PDF annexes
           of the selected annex types."""
        annexes = []
        sort_on = 'getObjPositionInParent' if \
            get_sort_categorized_tab() is False else None
        filters = {'contentType': 'application/pdf'}
        for annex_type_uid in data['annex_types']:
            filters['category_uid'] = annex_type_uid
            annexes += get_categorized_elements(
                obj,
                result_type='objects',
                sort_on=sort_on,
                filters=filters)
        return annexes

    def _get_annexes(self, data):
        """Return the annexes to concatenate of the selected elements not excluded."""
        excluded = [obj for obj, reason in self._excluded_elements()]
        annexes = []
        for brain in self.brains:
            obj = brain.getObject()
            if obj not in excluded:
                annexes += self._element_annexes(obj, data)
        return annexes

    def _annex_content(self, annex):
        """Return the PDF binary content of p_annex."""
        return annex.file.data

    def _apply(self, **data):
        """ """
        annexes = self._get_annexes(data)
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
        for i, annex in enumerate(annexes, start=1):
            try:
                output_writer.appendPagesFromReader(
                    PdfFileReader(BytesIO(self._annex_content(annex)), strict=False))
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
                    'concatenate_annexes_item_pdf_error_url', annex.aq_inner.aq_parent.absolute_url())
                return
            if data['two_sided'] and \
               output_writer.getNumPages() % 2 != 0 and \
               i < len(annexes):  # by position, an annex may be repeated
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
                description=u"",
                required=False,
                value_type=schema.Choice(vocabulary=self.vocabulary)),
            schema.Bool(
                __name__="two_sided",
                title=_(u'Two-sided?'),
                description=_(u'descr_two_sided'),
                default=False,
                required=False),
        )
        self.fields["elements"].widgetFactory = OrderableCheckBoxFieldWidget
        self.fields["two_sided"].widgetFactory = RadioFieldWidget

    @button.buttonAndHandler(_('Apply'), name='apply_export_pdf')
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
