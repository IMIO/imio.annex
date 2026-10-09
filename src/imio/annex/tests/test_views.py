# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from collective.iconifiedcategory.utils import get_categorized_elements
from imio.annex.browser.views import ConcatenateAnnexesBatchActionForm
from imio.annex.tests.base import BaseTestCase
from plone import api
from PyPDF2 import PdfFileReader


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
