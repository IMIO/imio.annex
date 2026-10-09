# -*- coding: utf-8 -*-

from imio.annex.tests.base import BaseTestCase
from imio.helpers.content import get_vocab


class TestContainedAnnexesVocabulary(BaseTestCase):
    """Test imio.annex.vocabularies.ContainedAnnexesVocabulary."""

    def test___call__(self):
        # no annex, empty vocabulary
        vocab = get_vocab(self.folder, u'imio.annex.contained_annexes')
        self.assertEqual(len(vocab), 0)
        # every contained annex gets a term, titles are HTML escaped
        self._add_annex(title=u'Annex <script>alert(1)</script>')
        self._add_annex(title=u'Annex 2', annex_file=self.file_txt)
        vocab = get_vocab(self.folder, u'imio.annex.contained_annexes')
        self.assertEqual(sorted([term.token for term in vocab._terms]),
                         ['annex-2', 'annex-script-alert-1-script'])
        titles = {term.token: term.title for term in vocab._terms}
        self.assertIn(u'Annex &lt;script&gt;alert(1)&lt;/script&gt;',
                      titles['annex-script-alert-1-script'])
        # terms are numbered
        self.assertEqual(
            sorted([title.split('. ')[0][-1] for title in titles.values()]),
            ['1', '2'])

    def test__check_disable_term(self):
        """By default every downloadable annex is enabled."""
        self._add_annex()
        self._add_annex(title=u'Annex 2', annex_file=self.file_txt)
        vocab = get_vocab(self.folder, u'imio.annex.contained_annexes')
        self.assertFalse(vocab._terms[0].disabled)
        self.assertFalse(vocab._terms[1].disabled)


class TestExportPDFElementsVocabulary(BaseTestCase):
    """Test imio.annex.vocabularies.ExportPDFElementsVocabulary."""

    def test__check_disable_term(self):
        """Only PDF annexes may be selected."""
        self._add_annex(title=u'PDF annex')
        self._add_annex(title=u'Text annex', annex_file=self.file_txt)
        vocab = get_vocab(self.folder, u'imio.annex.export_pdf_elements')
        self.assertFalse(vocab._terms[0].disabled)
        self.assertTrue(vocab._terms[1].disabled)
        self.assertIn(u'[PDF required]', vocab._terms[1].title)
