# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.annex.browser.views import ConcatenateAnnexesBatchActionForm
from imio.annex.browser.views import DownloadElementsAnnexesBatchActionForm
from imio.annex.tests.base import BaseTestCase
from plone import api
from PyPDF2 import PdfFileReader

import io
import zipfile


class TestExportPDFForm(BaseTestCase):
    """Test imio.annex.browser.views.ExportPDFForm."""

    def setUp(self):
        super(TestExportPDFForm, self).setUp()
        self.annex1 = self._add_annex(title=u'Annex 1')
        self.annex2 = self._add_annex(title=u'Annex 2')
        self.txt_annex = self._add_annex(title=u'Text annex',
                                         annex_file=self.file_txt)
        self.form = self.folder.restrictedTraverse('@@export-pdf-form')

    def _num_pages(self, res):
        res.seek(0)
        return PdfFileReader(res, strict=False).getNumPages()

    def test_handleApply(self):
        """Selected annexes are concatenated in a single PDF."""
        self.request['form.widgets.elements'] = [self.annex1.getId(),
                                                 self.annex2.getId()]
        self.form.update()
        res = self.form.handleApply(self.form, None)
        # every annex is a single page PDF
        self.assertEqual(self._num_pages(res), 2)

    def test__check_data(self):
        """A disabled element may not be selected, even by forging the form."""
        self.request['form.widgets.elements'] = [self.txt_annex.getId()]
        self.form.update()
        self.assertRaises(Unauthorized, self.form.handleApply, self.form, None)

    def test__do_export_pdf(self):
        """two_sided adds a blank page after elements ending on a recto."""
        self.form.update()
        data = {'elements': [self.annex1.getId(), self.annex2.getId()],
                'two_sided': False}
        self.assertEqual(self._num_pages(self.form._do_export_pdf(data)), 2)
        data['two_sided'] = True
        # a blank page is added after annex1, none after the last element
        self.assertEqual(self._num_pages(self.form._do_export_pdf(data)), 3)

    def test__check_auth(self):
        """_may_export is the hook used to protect the form."""
        self.assertTrue(self.form._may_export())
        self.form._may_export = lambda: False
        self.assertRaises(Unauthorized, self.form.update)
        self.assertRaises(Unauthorized, self.form.handleApply, self.form, None)

    def test_render(self):
        """The generated PDF is returned as an attachment,
           cancelling redirects to the context."""
        self.form.update()
        self.assertIn('export-pdf-form', self.form.render())
        self.form.handleCancel(self.form, None)
        self.assertEqual(self.form.render(), "")
        self.assertEqual(self.request.RESPONSE.getHeader('location'),
                         self.folder.absolute_url())
        self.form._do_export_pdf({'elements': [self.annex1.getId()],
                                  'two_sided': False})
        self.assertEqual(len(self.form.render()) > 0, True)
        self.assertEqual(
            self.request.RESPONSE.getHeader('content-disposition'),
            'attachment;filename=export_pdf_folder.pdf')


class TestConcatenateAnnexesBatchActionForm(BaseTestCase):
    """Test imio.annex.browser.views.ConcatenateAnnexesBatchActionForm."""

    def test__excluded_elements(self):
        """Elements for which _check_element gives a reason are not exported."""
        annex = self._add_annex()
        folder2 = api.content.create(id='folder2', type='Folder', title='Folder 2', container=self.portal)
        form = ConcatenateAnnexesBatchActionForm(self.portal, self.request)
        form.brains = api.content.find(UID=[self.folder.UID(), folder2.UID()], sort_on='id')
        data = {'annex_types': [get_categorized_elements(self.folder)[0]['category_uid']]}
        self.assertEqual(form._excluded_elements(), [])
        self.assertEqual(form._get_annexes(data), [annex])
        form = ConcatenateAnnexesBatchActionForm(self.portal, self.request)
        form.brains = api.content.find(UID=[self.folder.UID(), folder2.UID()], sort_on='id')
        form.CHECK_ELEMENTS = True
        form._check_element = lambda obj: obj.getId() == 'folder' and u'Excluded' or None
        self.assertEqual(form._excluded_elements(), [(self.folder, u'Excluded')])
        self.assertEqual(form._get_annexes(data), [])

    def test__apply_two_sided(self):
        """two_sided adds a blank page after every element but the last, even a repeated one."""
        annex1 = self._add_annex(title=u'Annex 1')
        annex2 = self._add_annex(title=u'Annex 2')
        form = ConcatenateAnnexesBatchActionForm(self.portal, self.request)
        form._get_annexes = lambda data: [annex1, annex2, annex1, annex2]
        res = form._apply(two_sided=True)
        res.seek(0)
        # 4 single page annexes and 3 blank pages
        self.assertEqual(PdfFileReader(res, strict=False).getNumPages(), 7)


class TestDownloadElementsAnnexesBatchActionForm(BaseTestCase):
    """Test imio.annex.browser.views.DownloadElementsAnnexesBatchActionForm."""

    def setUp(self):
        super(TestDownloadElementsAnnexesBatchActionForm, self).setUp()
        self._add_annex(title=u'Annex 1')
        self._add_annex(title=u'Annex 2', annex_file=self.file_txt)
        self.folder2 = api.content.create(
            id='folder2', type='Folder', title='Folder 2', container=self.portal)
        api.content.create(
            type='annex',
            title=u'Annex 3',
            file=self.file_pdf,
            container=self.folder2,
            content_category='config_-_group-1_-_category-1-1',
            to_print=False,
            confidential=False,
            publishable=False)

    def _form(self, uids):
        form = DownloadElementsAnnexesBatchActionForm(self.portal, self.request)
        form.brains = api.content.find(UID=uids, sort_on='id')
        form.update()
        return form

    def _zip_names(self, data):
        return sorted(zipfile.ZipFile(io.BytesIO(data)).namelist())

    def test__apply(self):
        """By default annexes are stored at the same level in the Zip file,
           same filenames are made unique, with "annexes_by_folder",
           annexes of each element are stored in a separate folder."""
        form = self._form([self.folder.UID(), self.folder2.UID()])
        self.assertTrue(form.do_apply)
        self.assertIn('annexes_by_folder', form.fields)
        self.assertEqual(len(form.annexes), 3)
        self.assertEqual(self._zip_names(form._apply(annexes_by_folder=False)),
                         [u'file-1.pdf', u'file.pdf', u'file.txt'])
        self.assertEqual(self._zip_names(form._apply(annexes_by_folder=True)),
                         [u'folder/file.pdf', u'folder/file.txt', u'folder2/file.pdf'])
        self.assertEqual(
            self.request.RESPONSE.getHeader('content-disposition'),
            'attachment;filename=plone.zip')

    def test_annexes_field(self):
        """Field "annexes" lists annexes of selected elements, every
           downloadable annexes are selected by default, only selected
           annexes are downloaded."""
        form = self._form([self.folder.UID(), self.folder2.UID()])
        annex_uids = [annex.UID() for annex in form.annexes]
        self.assertEqual(
            [term.token for term in form.fields['annexes'].field.value_type.vocabulary],
            annex_uids)
        self.assertEqual(form.fields['annexes'].field.default, annex_uids)
        # parent title is displayed in term title
        self.assertIn(u'Folder 2', form.annexes_terms[-1].title)
        rendered = form.render()
        self.assertIn('form-widgets-annexes', rendered)
        self.assertIn('form-widgets-annexes_by_folder', rendered)
        self.assertEqual(self._zip_names(form._apply(annexes=annex_uids[1:2])),
                         [u'file.txt'])
        # a disabled (or unknown) annex may not be downloaded
        form.annexes = form.annexes[1:]
        self.assertRaises(Unauthorized, form._apply, annexes=annex_uids[0:1])

    def test__apply_max_total_size(self):
        """When total size is exceeded, the action is still available so
           the user can unselect annexes, size of selected annexes is checked
           when applying."""
        form = DownloadElementsAnnexesBatchActionForm(self.portal, self.request)
        form.brains = api.content.find(
            UID=[self.folder.UID(), self.folder2.UID()], sort_on='id')
        txt_size = [a for a in self.folder.objectValues()
                    if a.file.filename == u'file.txt'][0].file.size
        form._max_total_size = lambda: txt_size
        form.update()
        self.assertTrue(form.do_apply)
        self.assertIn('warn_filesize', form.description)
        txt_uid = [annex.UID() for annex in form.annexes
                   if annex.file.filename == u'file.txt']
        self.assertIsNone(form._apply(annexes=[annex.UID() for annex in form.annexes]))
        self.assertNotIn('zip_file_content', self.request)
        self.assertEqual(self._zip_names(form._apply(annexes=txt_uid)), [u'file.txt'])

    def test__zip_path_element_name(self):
        """_zip_folder_name and _zip_filename_prefix may be overridden,
           returned names are made safe."""
        form = self._form([self.folder.UID(), self.folder2.UID()])
        form._zip_folder_name = form._zip_filename_prefix = \
            lambda element: u'{0}: {1}/x'.format(element.getId(), element.Title())
        self.assertEqual(self._zip_names(form._apply(annexes_by_folder=False)),
                         [u'folder- Folder-x - file.pdf',
                          u'folder- Folder-x - file.txt',
                          u'folder2- Folder 2-x - file.pdf'])
        self.assertEqual(self._zip_names(form._apply(annexes_by_folder=True)),
                         [u'folder- Folder-x/file.pdf',
                          u'folder- Folder-x/file.txt',
                          u'folder2- Folder 2-x/file.pdf'])

    def test__safe_zip_name(self):
        """Characters not allowed in filenames are replaced,
           whitespaces are cleaned and length is limited."""
        form = DownloadElementsAnnexesBatchActionForm(self.portal, self.request)
        self.assertEqual(form._safe_zip_name('A/B\\C:D*E?F"G<H>I|J'),
                         u'A-B-C-D-E-F-G-H-I-J')
        self.assertEqual(form._safe_zip_name(u' A \t\n B. '), u'A B')
        self.assertEqual(form._safe_zip_name('\xc3\xa9t\xc3\xa9'), u'\xe9t\xe9')
        self.assertEqual(len(form._safe_zip_name(u'x' * 200)),
                         form.MAX_ZIP_NAME_LENGTH)

    def test__update_nothing_to_download(self):
        """Action can not be applied when selected elements have no annex."""
        folder3 = api.content.create(
            id='folder3', type='Folder', title='Folder 3', container=self.portal)
        form = self._form([folder3.UID()])
        self.assertEqual(form.annexes, [])
        self.assertFalse(form.do_apply)
