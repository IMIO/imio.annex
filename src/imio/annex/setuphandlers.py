# -*- coding: utf-8 -*-

from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def post_install(context):
    """Post install script"""
    if context.readDataFile('imioannex_default.txt') is None:
        return


def uninstall(context):
    """Uninstall script"""
    if context.readDataFile('imioannex_uninstall.txt') is None:
        return
    registry = getUtility(IRegistry)
    key = 'plone.types_use_view_action_in_listings'
    types = list(registry.get(key, []))
    if 'annex' in types:
        types.remove('annex')
        registry[key] = tuple(types)
