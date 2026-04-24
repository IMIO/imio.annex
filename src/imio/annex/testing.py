# -*- coding: utf-8 -*-
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import imio.annex
from imio.annex import HAS_PLONE_6


def _fix_namespace_paths():
    """Extend pkg_resources namespace package paths to include wheel-based packages.

    When pkg_resources.declare_namespace is called for a namespace like 'zope',
    it takes over __path__ management but only discovers eggs with
    namespace_packages.txt. New-style wheel packages that rely on implicit
    namespace packages (PEP 420) are excluded, causing ImportError.

    This extends the __path__ for all registered namespace packages in sys.modules
    so both old-style and new-style packages are found. Handles multi-level
    namespaces like collective.z3cform by walking sys.modules recursively.
    """
    import os
    import sys
    # Collect all already-imported namespace packages and extend their __path__
    for mod_name, mod in list(sys.modules.items()):
        if mod is None or not hasattr(mod, '__path__'):
            continue
        parts = mod_name.split('.')
        for path_entry in sys.path:
            ns_path = os.path.join(path_entry, *parts)
            if os.path.isdir(ns_path) and ns_path not in mod.__path__:
                mod.__path__.append(ns_path)


class ImioAnnexLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if HAS_PLONE_6:
            _fix_namespace_paths()
        self.loadZCML('testing.zcml', package=imio.annex)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'imio.annex:testing')


IMIO_ANNEX_FIXTURE = ImioAnnexLayer()

IMIO_ANNEX_INTEGRATION_TESTING = IntegrationTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:IntegrationTesting',
)

IMIO_ANNEX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:FunctionalTesting',
)
