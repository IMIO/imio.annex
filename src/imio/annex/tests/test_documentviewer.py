# -*- coding: utf-8 -*-
"""Tests of everything relying on collective.documentviewer (replaced on Plone 6).

One class per tested production class or module, as in the other test modules.
"""
from collective.documentviewer.settings import GlobalSettings
from collective.documentviewer.settings import Settings
from collective.iconifiedcategory.utils import calculate_category_id
from collective.iconifiedcategory.utils import get_category_icon_url
from imio.annex import patch
from imio.annex import safe_utils
from imio.annex.content.events import annex_file_changed
from imio.annex.events import AnnexFileChangedEvent
from imio.annex.events import ConversionReallyFinishedEvent
from imio.annex.interfaces import IConversionReallyFinishedEvent
from imio.annex.interfaces import IConversionStartedEvent
from imio.annex.testing import annex_file
from imio.annex.testing import IMIO_ANNEX_FUNCTIONAL_TESTING
from imio.annex.testing import ImioAnnexTestCase
from imio.annex.utils import get_annexes_to_print
from imio.prettylink.interfaces import IPrettyLink
from plone import api
from ZODB.blob import Blob
from zope.event import notify

import os
import shutil
import tempfile
import transaction


# not a valid PDF: a conversion always fails, with or without docsplit
PDF = b"%PDF-1.4 not really a PDF"


class FakeAsyncService(object):
    """plone.app.async queue service (not installed): records the queued jobs."""

    def __init__(self):
        self.jobs = []

    def queueJobInQueue(self, queue, quota_names, func, *args):
        self.jobs.append((queue, quota_names, func, args))


class DocumentviewerTestCase(ImioAnnexTestCase):
    def setUp(self):
        super(DocumentviewerTestCase, self).setUp()
        # conversions are triggered by the tests
        GlobalSettings(self.portal).auto_convert = False

    def pdf_annex(self, annex_id, title, to_print=False):
        return api.content.create(
            container=self.folder,
            type="annex",
            id=annex_id,
            title=title,
            to_print=to_print,
            file=annex_file(
                data=PDF,
                filename=u"{0}.pdf".format(annex_id),
                content_type="application/pdf",
            ),
            content_category=calculate_category_id(self.category),
        )

    def converted(self, annex, num_pages=1):
        """Store what collective.documentviewer stores after a successful conversion (Blob storage)."""
        settings = Settings(annex)
        settings.successfully_converted = True
        settings.converting = False
        settings.num_pages = num_pages
        settings.pdf_image_format = "png"
        settings.storage_type = "Blob"
        blob_files = {}
        for number in range(1, num_pages + 1):
            blob = Blob()
            with blob.open("w") as image:
                image.write(b"page image")
            blob_files["large/dump_{0}.png".format(number)] = blob
        settings.blob_files = blob_files
        # sent by the patched Converter.__call__
        notify(ConversionReallyFinishedEvent(annex))


class TestPatch(DocumentviewerTestCase):
    def setUp(self):
        super(TestPatch, self).setUp()
        self.events = []
        # registered in the site manager of the portal: its lookup cache is not reset when the global
        # registry of the test layer changes
        sm = self.portal.getSiteManager()
        for interface in (IConversionStartedEvent, IConversionReallyFinishedEvent):
            sm.registerHandler(self.record, (interface,))
            self.addCleanup(sm.unregisterHandler, self.record, (interface,))

    def record(self, event):
        self.events.append(
            (event.__class__.__name__, event.object, Settings(event.object).converting)
        )

    def test_converter_call(self):
        annex = self.pdf_annex("pdf", u"PDF")
        uid = annex.UID()
        self.assertEqual(
            self.folder.categorized_elements[uid]["preview_status"], "not_converted"
        )
        self.assertEqual(patch.Converter(annex)(), "failure")
        # ConversionReallyFinishedEvent once "converting" is set back to False
        self.assertEqual(
            self.events,
            [
                ("ConversionStartedEvent", annex, None),
                ("ConversionReallyFinishedEvent", annex, False),
            ],
        )
        self.assertEqual(
            self.folder.categorized_elements[uid]["preview_status"], "conversion_error"
        )

    def test_jobrunner_queue_it(self):
        annex = self.pdf_annex("pdf", u"PDF")
        # JobRunner needs plone.app.async
        runner = patch.JobRunner.__new__(patch.JobRunner)
        runner.object = annex
        runner.queue = "queue"
        async_service = FakeAsyncService()
        runner.__dict__["async"] = async_service
        runner.queue_it()
        self.assertEqual(len(async_service.jobs), 1)
        self.assertEqual(self.events, [("ConversionStartedEvent", annex, True)])
        # the spinner is displayed
        self.assertEqual(
            self.folder.categorized_elements[annex.UID()]["preview_status"],
            "in_progress",
        )


class TestContentEvents(DocumentviewerTestCase):
    def test_annex_file_changed(self):
        """Does nothing, for convertible annexes or not."""
        annex = self.pdf_annex("pdf", u"PDF")
        self.assertIsNone(annex_file_changed(AnnexFileChangedEvent(annex, annex.file)))
        self.assertIsNone(
            annex_file_changed(AnnexFileChangedEvent(self.annex, self.annex.file))
        )
        self.assertEqual(Settings(annex).converting, None)


class TestAnnex(DocumentviewerTestCase):
    def test_show_preview(self):
        annex = self.pdf_annex("pdf", u"PDF")
        self.assertFalse(annex.show_preview())
        self.converted(annex)
        self.assertEqual(
            self.folder.categorized_elements[annex.UID()]["preview_status"], "converted"
        )
        self.assertTrue(annex.show_preview())
        # the 'View preview' action
        actions = dict(
            (action["id"], action)
            for action in api.portal.get_tool("portal_actions").listFilteredActionsFor(
                annex
            )["object_buttons"]
        )
        self.assertEqual(
            actions["view_preview"]["url"],
            "http://nohost/plone/folder/pdf/documentviewer#document/#/p1",
        )
        self.assertEqual(actions["view_preview"]["link_target"], "_blank")


class TestAnnexPrettyLinkAdapter(DocumentviewerTestCase):
    def setUp(self):
        super(TestAnnexPrettyLinkAdapter, self).setUp()
        self.pdf = self.pdf_annex("pdf", u"PDF")
        self.category.show_preview = 1

    def test__get_url(self):
        self.converted(self.pdf)
        adapter = IPrettyLink(self.pdf)
        adapter._leadingIcons()
        self.assertTrue(adapter.is_preview)
        self.assertEqual(
            adapter._get_url(),
            u"http://nohost/plone/folder/pdf/documentviewer#document/#/p1",
        )
        self.assertIn(
            u"href='http://nohost/plone/folder/pdf/documentviewer#document/#/p1'",
            IPrettyLink(self.pdf).getLink(),
        )

    def test__leadingIcons(self):
        icon = (get_category_icon_url(self.category), u"Category")
        # conversion in progress
        Settings(self.pdf).converting = True
        notify(ConversionReallyFinishedEvent(self.pdf))
        self.assertEqual(
            IPrettyLink(self.pdf)._leadingIcons(),
            [
                (
                    "spinner_small.gif",
                    u"The document is currently under conversion, please refresh the page in a few minutes",
                ),
                icon,
                ("file_icon.png", u"Preview"),
            ],
        )
        # converted
        self.converted(self.pdf)
        self.assertEqual(
            IPrettyLink(self.pdf)._leadingIcons(), [icon, ("file_icon.png", u"Preview")]
        )
        # the category doesn't show the preview
        self.category.show_preview = 0
        notify(ConversionReallyFinishedEvent(self.pdf))
        self.assertEqual(IPrettyLink(self.pdf)._leadingIcons(), [icon])


class TestUtils(DocumentviewerTestCase):

    layer = IMIO_ANNEX_FUNCTIONAL_TESTING

    def test_get_annexes_to_print(self):
        self.assertIs(safe_utils.get_annexes_to_print, get_annexes_to_print)
        pdf_1 = self.pdf_annex("pdf-1", u"PDF 1", to_print=True)
        pdf_2 = self.pdf_annex("pdf-2", u"PDF 2", to_print=True)
        not_to_print = self.pdf_annex("pdf-3", u"PDF 3")
        not_converted = self.pdf_annex("pdf-4", u"PDF 4", to_print=True)
        self.converted(pdf_1, num_pages=2)
        self.converted(pdf_2)
        self.converted(not_to_print)
        self.assertTrue(not_converted.to_print)
        # text annexes can not be printed
        self.assertIsNone(self.annex.to_print)
        transaction.commit()

        def blob_path(annex, number):
            return (
                Settings(annex)
                .blob_files["large/dump_{0}.png".format(number)]
                .committed()
            )

        expected = [
            {
                "title": "PDF 1",
                "UID": pdf_1.UID(),
                "number": 1,
                "number_of_images": 2,
                "images": [
                    {"number": 1, "path": blob_path(pdf_1, 1)},
                    {"number": 2, "path": blob_path(pdf_1, 2)},
                ],
            },
            {
                "title": "PDF 2",
                "UID": pdf_2.UID(),
                "number": 2,
                "number_of_images": 1,
                "images": [{"number": 1, "path": blob_path(pdf_2, 1)}],
            },
        ]
        annexes = get_annexes_to_print(self.folder)
        self.assertEqual(annexes, expected)
        self.assertTrue(os.path.exists(annexes[0]["images"][0]["path"]))
        # cached in the request
        self.assertIs(get_annexes_to_print(self.folder), annexes)
        self.assertIsNot(get_annexes_to_print(self.folder, caching=False), annexes)
        self.assertEqual(
            [
                a["title"]
                for a in get_annexes_to_print(
                    self.folder, filters={"to_print": False}, caching=False
                )
            ],
            ["PDF 3"],
        )
        # 'File' storage: images in the documentviewer storage directory
        storage_location = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, storage_location)
        global_settings = GlobalSettings(self.portal)
        global_settings.storage_type = "File"
        global_settings.storage_location = storage_location
        uid = pdf_2.UID()
        Settings(pdf_2).storage_type = "File"
        large = os.path.join(storage_location, uid[0], uid[1], uid, "large")
        os.makedirs(large)
        with open(os.path.join(large, "dump_1.png"), "wb") as image:
            image.write(b"page image")
        Settings(pdf_1).storage_type = "File"
        uid = pdf_1.UID()
        large_1 = os.path.join(storage_location, uid[0], uid[1], uid, "large")
        os.makedirs(large_1)
        for number in (1, 2):
            with open(
                os.path.join(large_1, "dump_{0}.png".format(number)), "wb"
            ) as image:
                image.write(b"page image")
        annexes = get_annexes_to_print(self.folder, caching=False)
        self.assertEqual(
            [[page["path"] for page in annex["images"]] for annex in annexes],
            [
                [
                    os.path.join(large_1, "dump_1.png"),
                    os.path.join(large_1, "dump_2.png"),
                ],
                [os.path.join(large, "dump_1.png")],
            ],
        )
