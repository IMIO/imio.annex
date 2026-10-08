# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import calculate_category_id
from collective.quickupload.interfaces import IQuickUploadFileFactory
from imio.annex.quickupload.quickupload import _check_validateFileIsPDF
from imio.annex.quickupload.quickupload import ImioAnnexQuickUploadCapableFileFactory
from imio.annex.quickupload.quickupload import QuickUploadFileInit
from imio.annex.quickupload.quickupload import QuickUploadFileView
from imio.annex.quickupload.quickupload import QuickUploadPortletView
from imio.annex.testing import ImioAnnexTestCase
from io import BytesIO
from plone.app.testing import logout
from zope.component import getMultiAdapter
from zope.interface import Invalid

import json


FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"


class TestQuickUploadPortletView(ImioAnnexTestCase):
    """@@quick_upload, loaded in the quick upload portlet."""

    def setUp(self):
        super(TestQuickUploadPortletView, self).setUp()
        # a browser request has a session and a user agent
        self.request.set("SESSION", {})
        self.request.environ["HTTP_USER_AGENT"] = FIREFOX

    def view(self, typeupload):
        self.request.form["typeupload"] = typeupload
        # request.get() caches the form values
        self.request.set("typeupload", typeupload)
        view = getMultiAdapter((self.folder, self.request), name="quick_upload")
        self.request["PUBLISHED"] = view
        return view

    def test_typeupload(self):
        view = self.view("annex")
        self.assertIsInstance(view, QuickUploadPortletView)
        self.assertEqual(view.typeupload, "annex")
        self.assertEqual(self.view("File").typeupload, "File")

    def test_is_iconified_categorized(self):
        self.assertTrue(self.view("annex").is_iconified_categorized)
        self.assertFalse(self.view("File").is_iconified_categorized)

    def test_script_content(self):
        view = self.view("annex")
        script = view.script_content()
        self.assertIn(
            "sendDataAndUpload_{0} = function()".format(view.uploader_id), script
        )
        self.assertTrue(
            script.strip().endswith(
                "jQuery('a#copy_categories').click(PloneQuickUpload.extendCategories);"
            )
        )

    def test_template(self):
        """The 'Apply the first category on all elements' button."""
        rendered = self.view("annex")()
        self.assertIn('id="copy_categories"', rendered)
        self.assertIn('title="Apply the first category on all elements"', rendered)
        self.assertIn(
            '<input type="hidden" class="uploadify_typeupload" value="annex" />',
            rendered,
        )
        self.assertNotIn('id="copy_categories"', self.view("File")())


class TestQuickUploadFileInit(ImioAnnexTestCase):
    """@@quick_upload_init, the javascript settings of the uploader."""

    def test_upload_settings(self):
        # an image upload done before in the same session (CKeditor)
        self.request.set("SESSION", {"mediaupload": "image", "typeupload": "Image"})
        self.request.form["typeupload"] = "annex"
        init = getMultiAdapter((self.folder, self.request), name="quick_upload_init")
        self.assertIsInstance(init, QuickUploadFileInit)
        init.uploader_id = "uploader"
        # published elsewhere (@@finder_upload): the session is used
        self.request["PUBLISHED"] = self.folder
        settings = init.upload_settings()
        self.assertEqual(settings["typeupload"], "Image")
        self.assertEqual(settings["ul_file_extensions"], "*.jpg;*.jpeg;*.gif;*.png;")
        # loaded by the quick upload portlet: the session is cleaned
        self.request["PUBLISHED"] = getMultiAdapter(
            (self.folder, self.request), name="quick_upload"
        )
        settings = init.upload_settings()
        self.assertEqual(settings["typeupload"], "annex")
        self.assertEqual(settings["ul_file_extensions"], "*.*;")
        self.assertEqual(self.request.get("SESSION"), {})


class TestQuickUploadFileView(ImioAnnexTestCase):
    """@@quick_upload_file, called by the uploader (XHR) for each file."""

    def upload(self, content_category, filename="upload.txt", data=b"Uploaded content"):
        self.request.environ["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        self.request.environ["HTTP_X_FILE_NAME"] = filename
        self.request.set("BODYFILE", BytesIO(data))
        self.request.form.update(
            {
                "typeupload": "annex",
                "title": "Uploaded",
                "description": "Uploaded description",
                "content_category": content_category,
            }
        )
        view = getMultiAdapter((self.folder, self.request), name="quick_upload_file")
        self.assertIsInstance(view, QuickUploadFileView)
        return json.loads(view.quick_upload_file())

    def test__manage_extra_parameters(self):
        view = getMultiAdapter((self.folder, self.request), name="quick_upload_file")
        self.annex.content_category = None
        # no content_category in the request
        view._manage_extra_parameters(self.request, {"success": self.annex})
        self.assertIsNone(self.annex.content_category)
        # failed upload
        self.request.form["content_category"] = calculate_category_id(self.pdf_category)
        view._manage_extra_parameters(self.request, {"success": None})
        self.assertIsNone(self.annex.content_category)
        # the category is set and the annex is categorized
        view._manage_extra_parameters(self.request, {"success": self.annex})
        self.assertEqual(
            self.annex.content_category, calculate_category_id(self.pdf_category)
        )
        self.assertEqual(
            self.folder.categorized_elements[self.annex.UID()]["category_title"],
            u"PDF only",
        )

    def test_quick_upload_file(self):
        result = self.upload(calculate_category_id(self.category))
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "upload.txt")
        self.assertEqual(result["title"], "Uploaded")
        annex = self.folder["upload.txt"]
        self.assertEqual(result["uid"], annex.UID())
        self.assertEqual(annex.portal_type, "annex")
        self.assertEqual(annex.Description(), "Uploaded description")
        self.assertEqual(annex.file.data, b"Uploaded content")
        self.assertEqual(annex.content_category, calculate_category_id(self.category))
        self.assertEqual(
            self.folder.categorized_elements[annex.UID()]["category_title"], u"Category"
        )
        # the category only accepts PDF files
        self.assertEqual(
            self.upload(calculate_category_id(self.pdf_category), filename="other.txt"),
            {u"error": u"serverError"},
        )
        self.assertNotIn("other.txt", self.folder)
        result = self.upload(
            calculate_category_id(self.pdf_category),
            filename="other.pdf",
            data=b"%PDF-1.4",
        )
        self.assertTrue(result["success"])
        self.assertEqual(
            self.folder["other.pdf"].content_category,
            calculate_category_id(self.pdf_category),
        )
        # same file name
        self.assertEqual(
            self.upload(calculate_category_id(self.category)),
            {u"error": u"serverErrorAlreadyExists"},
        )


class TestQuickupload(ImioAnnexTestCase):
    def test__check_validateFileIsPDF(self):
        self.request.form["content_category"] = calculate_category_id(self.pdf_category)
        self.assertRaises(
            Invalid,
            _check_validateFileIsPDF,
            self.folder,
            self.request,
            "annex",
            "text/plain",
        )
        _check_validateFileIsPDF(self.folder, self.request, "annex", "application/pdf")
        _check_validateFileIsPDF(self.folder, self.request, "File", "text/plain")
        self.request.form["content_category"] = calculate_category_id(self.category)
        _check_validateFileIsPDF(self.folder, self.request, "annex", "text/plain")
        # annexDecision (Products.PloneMeeting) flags the request while validating
        _check_validateFileIsPDF(
            self.folder, self.request, "annexDecision", "text/plain"
        )
        self.assertFalse(self.request.get("force_use_item_decision_annexes_group"))
        # Plone 4 behaviour: the flag is not reset when the validation fails
        self.request.form["content_category"] = calculate_category_id(self.pdf_category)
        self.assertRaises(
            Invalid,
            _check_validateFileIsPDF,
            self.folder,
            self.request,
            "annexDecision",
            "text/plain",
        )
        self.assertTrue(self.request.get("force_use_item_decision_annexes_group"))


class TestImioAnnexQuickUploadCapableFileFactory(ImioAnnexTestCase):
    def test___call__(self):
        factory = IQuickUploadFileFactory(self.folder)
        self.assertIsInstance(factory, ImioAnnexQuickUploadCapableFileFactory)
        # title computed from the file name
        result = factory(
            "my_new-file.txt", u"", u"Description", "text/plain", b"Data", "annex"
        )
        self.assertEqual(result["error"], u"")
        annex = result["success"]
        self.assertEqual(annex.getId(), "my-new-file.txt")
        self.assertEqual(annex.Title(), "my new file")
        self.assertEqual(annex.Description(), "Description")
        self.assertEqual(annex.file.data, b"Data")
        self.assertEqual(annex.file.filename, u"my_new-file.txt")
        # same file name: new id
        result = factory(
            "my_new-file.txt", u"Title", u"", "text/plain", b"Data", "annex"
        )
        self.assertNotEqual(result["success"].getId(), "my-new-file.txt")
        self.assertEqual(result["success"].Title(), "Title")
        # errors
        self.assertEqual(
            factory("file.txt", u"", u"", "text/plain", b"Data", "unknown"),
            {"success": None, "error": u"serverErrorDisallowedType"},
        )
        # no permission: CMF invokeFactory raises ValueError, not Unauthorized
        logout()
        self.assertEqual(
            factory("file.txt", u"", u"", "text/plain", b"Data", "annex"),
            {"success": None, "error": u"serverErrorDisallowedType"},
        )
