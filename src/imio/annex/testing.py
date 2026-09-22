# -*- coding: utf-8 -*-

from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import imio.annex


class ImioAnnexLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        z2.installProduct(app, 'Products.DateRecurringIndex')
        self.loadZCML(package=imio.annex)
        self.loadZCML('testing.zcml', package=imio.annex)

    def setUpPloneSite(self, portal):
        # brings the ContentCategoryConfiguration "config" used by annexes
        applyProfile(portal, 'collective.iconifiedcategory:testing')
        applyProfile(portal, 'imio.annex:default')


IMIO_ANNEX_FIXTURE = ImioAnnexLayer()


IMIO_ANNEX_INTEGRATION_TESTING = IntegrationTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:IntegrationTesting')


IMIO_ANNEX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:FunctionalTesting')
