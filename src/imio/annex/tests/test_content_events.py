# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import calculate_category_id
from imio.annex.events import ConversionReallyFinishedEvent
from imio.annex.events import ConversionStartedEvent
from imio.annex.interfaces import IAnnexFileChangedEvent
from imio.annex.testing import annex_file
from imio.annex.testing import ImioAnnexTestCase
from plone import api
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


class TestContentEvents(ImioAnnexTestCase):
    """annex_file_changed reads the documentviewer settings: test_documentviewer."""

    def setUp(self):
        super(TestContentEvents, self).setUp()
        self.file_changed_events = []
        # registered in the site manager of the portal: its lookup cache is not reset when the global
        # registry of the test layer changes
        sm = self.portal.getSiteManager()
        sm.registerHandler(self.file_changed_events.append, (IAnnexFileChangedEvent,))
        self.addCleanup(
            sm.unregisterHandler,
            self.file_changed_events.append,
            (IAnnexFileChangedEvent,),
        )

    def test_annex_content_created(self):
        annex = api.content.create(
            container=self.folder,
            type="annex",
            id="annex-3",
            title=u"Annex 3",
            file=annex_file(),
            content_category=calculate_category_id(self.category),
        )
        self.assertEqual(len(self.file_changed_events), 1)
        self.assertEqual(self.file_changed_events[0].object, annex)
        self.assertEqual(self.file_changed_events[0].file, annex.file)

    def test_annex_content_updated(self):
        # the file stored when the layer was set up is committed: no event
        notify(ObjectModifiedEvent(self.annex))
        self.assertEqual(self.file_changed_events, [])
        # a new file (blob not committed yet)
        self.annex.file = annex_file(data=b"New content", filename=u"new.txt")
        notify(ObjectModifiedEvent(self.annex))
        self.assertEqual(len(self.file_changed_events), 1)
        self.assertEqual(self.file_changed_events[0].file.filename, u"new.txt")

    def test_annex_conversion_started(self):
        uid = self.annex.UID()
        self.annex.title = u"Changed without event"
        self.assertEqual(self.folder.categorized_elements[uid]["title"], u"Annex")
        notify(ConversionStartedEvent(self.annex))
        self.assertEqual(
            self.folder.categorized_elements[uid]["title"], u"Changed without event"
        )
        # not categorized: nothing done
        self.uncategorize(self.annex)
        notify(ConversionStartedEvent(self.annex))
        self.assertNotIn(uid, self.folder.categorized_elements)

    def test_annex_conversion_really_finished(self):
        uid = self.annex.UID()
        self.annex.title = u"Changed without event"
        notify(ConversionReallyFinishedEvent(self.annex))
        self.assertEqual(
            self.folder.categorized_elements[uid]["title"], u"Changed without event"
        )
        # not categorized: nothing done
        self.uncategorize(self.annex)
        notify(ConversionReallyFinishedEvent(self.annex))
        self.assertNotIn(uid, self.folder.categorized_elements)
