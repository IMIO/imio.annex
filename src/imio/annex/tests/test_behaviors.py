# -*- coding: utf-8 -*-
from collective.dms.scanbehavior.behaviors.behaviors import IScanFields
from imio.annex.behaviors import IScanFieldsHiddenToSignAndSigned
from imio.annex.testing import ImioAnnexTestCase
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from zope.component import queryUtility


class TestBehaviors(ImioAnnexTestCase):

    def test_IScanFieldsHiddenToSignAndSigned(self):
        behavior = queryUtility(IBehavior, name='imio.annex.behaviors.IScanFieldsHiddenToSignAndSigned')
        self.assertEqual(behavior.interface, IScanFieldsHiddenToSignAndSigned)
        self.assertTrue(IFormFieldProvider.providedBy(IScanFieldsHiddenToSignAndSigned))
        self.assertTrue(IScanFieldsHiddenToSignAndSigned.isOrExtends(IScanFields))
        # same fields as IScanFields, to_sign/signed are not part of collective.dms.scanbehavior any more
        self.assertEqual(
            sorted(IScanFieldsHiddenToSignAndSigned.names(all=True)), sorted(IScanFields.names(all=True)))
        self.assertIn('scan_id', IScanFieldsHiddenToSignAndSigned.names(all=True))
        self.assertNotIn('to_sign', IScanFieldsHiddenToSignAndSigned.names(all=True))
