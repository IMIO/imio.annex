# -*- coding: utf-8 -*-
from collective.iconifiedcategory.utils import calculate_category_id
from collective.iconifiedcategory.utils import remove_categorized_element
from plone import api
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from zope.event import notify
from zope.globalrequest import setRequest
from zope.traversing.interfaces import BeforeTraverseEvent

import imio.annex
import os
import sys
import unittest


PLONE_MAJOR = int(api.env.plone_version().split('.')[0])
HAS_PLONE_6 = PLONE_MAJOR >= 6

if PLONE_MAJOR >= 5:
    from plone.testing.zope import WSGI_SERVER_FIXTURE as SERVER_FIXTURE
else:
    from plone.testing.z2 import ZSERVER_FIXTURE as SERVER_FIXTURE

MANAGER_NAME = 'manager'
MANAGER_PASSWORD = 'manager123'
MEMBER_NAME = 'member'
MEMBER_PASSWORD = 'member123'

ICON_PATH = os.path.join(os.path.dirname(imio.annex.__file__), 'browser', 'static', 'view_element.png')


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
    # Collect all already-imported namespace packages and extend their __path__
    for mod_name, mod in list(sys.modules.items()):
        if mod is None or not hasattr(mod, '__path__'):
            continue
        parts = mod_name.split('.')
        for path_entry in sys.path:
            ns_path = os.path.join(path_entry, *parts)
            if os.path.isdir(ns_path) and ns_path not in mod.__path__:
                mod.__path__.append(ns_path)


def _add_sessions(app):
    """Add the session machinery of a Zope instance, missing in test apps: @@quick_upload needs a session."""
    from OFS.Folder import Folder
    from Products.Sessions.BrowserIdManager import BrowserIdManager
    from Products.Sessions.SessionDataManager import SessionDataManager
    from Products.Transience.Transience import TransientObjectContainer

    app._setObject('browser_id_manager', BrowserIdManager('browser_id_manager'))
    app._setObject('temp_folder', Folder('temp_folder'))
    app.temp_folder._setObject('session_data', TransientObjectContainer('session_data'))
    app._setObject('session_data_manager', SessionDataManager(
        'session_data_manager', path='/temp_folder/session_data', requestName='SESSION'))


def annex_file(data=b'Annex content', filename=u'annex.txt', content_type='text/plain'):
    """File to store in an annex."""
    return NamedBlobFile(data=data, filename=filename, contentType=content_type)


class ImioAnnexLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        if HAS_PLONE_6:
            _fix_namespace_paths()
        self.loadZCML('testing.zcml', package=imio.annex)
        _add_sessions(app)

    def setUpPloneSite(self, portal):
        # collective.fingerpointing logs the content creations with the global request
        setRequest(portal.REQUEST)
        applyProfile(portal, 'imio.annex:testing')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)
        # robot users: a Manager with a user folder, a plain Member without
        api.user.create(
            email='manager@example.com', username=MANAGER_NAME, password=MANAGER_PASSWORD,
            roles=('Member', 'Manager'), properties={'fullname': 'Manager'})
        api.user.create(email='member@example.com', username=MEMBER_NAME, password=MEMBER_PASSWORD)
        members = api.content.create(container=portal, type='Folder', id='Members', title='Users')
        api.content.create(container=members, type='Folder', id=MANAGER_NAME, title='Manager')
        # categories configuration, as in collective.iconifiedcategory tests
        config = api.content.create(container=portal, type='ContentCategoryConfiguration', id='config', title='Config')
        group = api.content.create(
            container=config, type='ContentCategoryGroup', id='group', title='Group', to_be_printed_activated=True)
        with open(ICON_PATH, 'rb') as icon:
            icon_data = icon.read()
        for category_id, title, only_pdf in (('category', u'Category', False), ('pdf-category', u'PDF only', True)):
            api.content.create(
                container=group, type='ContentCategory', id=category_id, title=title, predefined_title=title,
                icon=NamedBlobImage(data=icon_data, filename=u'icon.png'), only_pdf=only_pdf)
        # a folder holding 2 annexes
        folder = api.content.create(container=portal, type='Folder', id='folder', title='Folder')
        for annex_id, title in (('annex', u'Annex'), ('annex-2', u'Annex 2')):
            api.content.create(
                container=folder, type='annex', id=annex_id, title=title, file=annex_file(),
                content_category=calculate_category_id(group['category']))
        setRoles(portal, TEST_USER_ID, ['Member'])
        setRequest(None)


IMIO_ANNEX_FIXTURE = ImioAnnexLayer()

IMIO_ANNEX_INTEGRATION_TESTING = IntegrationTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:IntegrationTesting',
)

IMIO_ANNEX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(IMIO_ANNEX_FIXTURE,),
    name='ImioAnnexLayer:FunctionalTesting',
)

ACCEPTANCE = FunctionalTesting(
    bases=(IMIO_ANNEX_FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, SERVER_FIXTURE),
    name='ImioAnnexLayer:AcceptanceTesting',
)


class ImioAnnexTestCase(unittest.TestCase):
    """Manager in a request marked with the browser layers, the folder and its annexes of the layer."""

    layer = IMIO_ANNEX_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        # mark the request with the browser layers, as the publisher does
        notify(BeforeTraverseEvent(self.portal, self.request))
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder = self.portal['folder']
        self.annex = self.folder['annex']
        self.annex_2 = self.folder['annex-2']
        self.category = self.portal['config']['group']['category']
        self.pdf_category = self.portal['config']['group']['pdf-category']

    def uncategorize(self, annex):
        """Remove annex from the categorized elements of its parent, rolled back after the test."""
        remove_categorized_element(annex.aq_parent, annex)
        # categorized_elements is not persistent: mark the parent so the transaction abort reloads it
        annex.aq_parent._p_changed = True
