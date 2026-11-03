# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import calculate_category_id
from imio.annex.quickupload.form import QuickUploadForm
from imio.annex.quickupload.form import QuickUploadFormView
from imio.annex.testing import ImioAnnexTestCase
from zope.component import getMultiAdapter


class TestQuickUploadForm(ImioAnnexTestCase):
    """Form loaded by helpers.js for each file added in the quick upload portlet."""

    def form(self, typeupload):
        self.request.form["typeupload"] = typeupload
        # request.get() caches the form values
        self.request.set("typeupload", typeupload)
        return QuickUploadForm(self.folder, self.request)

    def test_typeupload(self):
        self.assertEqual(self.form("annex").typeupload, "annex")
        self.assertEqual(self.form("File").typeupload, "File")

    def test_is_iconified_categorized(self):
        self.assertTrue(self.form("annex").is_iconified_categorized)
        self.assertFalse(self.form("File").is_iconified_categorized)

    def test_update(self):
        form = self.form("annex")
        form.update()
        self.assertEqual(
            list(form.widgets.keys()),
            ["title", "content_category", "default_titles", "description"],
        )
        self.assertEqual(form.widgets["default_titles"].mode, "hidden")
        # not categorized: no category
        form = self.form("File")
        form.update()
        self.assertEqual(list(form.widgets.keys()), ["title", "description"])


class TestQuickUploadFormView(ImioAnnexTestCase):
    def test_update(self):
        self.request.form["typeupload"] = "annex"
        self.request.set("typeupload", "annex")
        view = getMultiAdapter((self.folder, self.request), name="quickupload-form")
        self.assertIsInstance(view, QuickUploadFormView)
        rendered = view()
        self.assertIn('id="form-widgets-title"', rendered)
        self.assertIn('name="form.widgets.content_category"', rendered)
        self.assertIn(
            'value="{0}"'.format(calculate_category_id(self.category)), rendered
        )
        self.assertIn(
            'value="{0}"'.format(calculate_category_id(self.pdf_category)), rendered
        )
        self.assertIn('id="form-widgets-description"', rendered)
        self.request.form["typeupload"] = "File"
        self.request.set("typeupload", "File")
        rendered = getMultiAdapter(
            (self.folder, self.request), name="quickupload-form"
        )()
        self.assertIn('id="form-widgets-title"', rendered)
        self.assertNotIn("form-widgets-content_category", rendered)
