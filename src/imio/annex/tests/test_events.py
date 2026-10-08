# -*- coding: utf-8 -*-
from imio.annex.events import AnnexFileChangedEvent
from imio.annex.events import ConversionReallyFinishedEvent
from imio.annex.events import ConversionStartedEvent
from imio.annex.interfaces import IAnnexFileChangedEvent
from imio.annex.interfaces import IConversionReallyFinishedEvent
from imio.annex.interfaces import IConversionStartedEvent
from imio.annex.testing import ImioAnnexTestCase


try:
    from zope.interface.interfaces import IObjectEvent
except ImportError:  # Plone 4 (zope.interface 3.6)
    from zope.component.interfaces import IObjectEvent


class TestEvents(ImioAnnexTestCase):

    def test_AnnexFileChangedEvent(self):
        event = AnnexFileChangedEvent(self.annex, self.annex.file)
        self.assertTrue(IAnnexFileChangedEvent.providedBy(event))
        self.assertTrue(IObjectEvent.providedBy(event))
        self.assertEqual(event.object, self.annex)
        self.assertEqual(event.file, self.annex.file)
        self.assertIsNone(event.called_by)
        self.assertEqual(AnnexFileChangedEvent(self.annex, None, called_by='me').called_by, 'me')

    def test_ConversionStartedEvent(self):
        event = ConversionStartedEvent(self.annex)
        self.assertTrue(IConversionStartedEvent.providedBy(event))
        self.assertTrue(IObjectEvent.providedBy(event))
        self.assertEqual(event.object, self.annex)

    def test_ConversionReallyFinishedEvent(self):
        event = ConversionReallyFinishedEvent(self.annex)
        self.assertTrue(IConversionReallyFinishedEvent.providedBy(event))
        self.assertTrue(IObjectEvent.providedBy(event))
        self.assertEqual(event.object, self.annex)
