# -*- coding: utf-8 -*-

from imio.annex.tests.base import BaseTestCase
from imio.helpers.content import get_vocab
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory


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

    def test___call___include_parent_title(self):
        """Element title and annex title (with arrow) are rendered in separate
           tags with a CSS class so it may be styled separately."""
        self._add_annex(title=u'Annex 1')
        factory = getUtility(IVocabularyFactory, u'imio.annex.contained_annexes')
        title = factory(self.folder)._terms[0].title
        self.assertTrue(title.startswith(u'<span class="contained_annex_title"><img '))
        self.assertTrue(title.endswith(u'1. Annex 1</span>'))
        self.assertNotIn(u'contained_annex_parent_title', title)
        title = factory(self.folder, include_parent_title=True)._terms[0].title
        self.assertTrue(title.startswith(
            u'<span class="contained_annex_parent_title">Folder</span><br>'
            u'<span class="contained_annex_title">'
            u'<span class="titleVisualPadding">\u2794 </span><img '))
        self.assertTrue(title.endswith(u'1. Annex 1</span>'))
        # title_kwargs are passed to context Title
        self.folder.Title = lambda with_prefix=False: \
            with_prefix and 'Prefix - Folder' or 'Folder'
        title = factory(self.folder, include_parent_title=True,
                        title_kwargs={'with_prefix': True})._terms[0].title
        self.assertTrue(title.startswith(
            u'<span class="contained_annex_parent_title">Prefix - Folder</span>'))

    def test__check_disable_term_suffix_in_annex_title(self):
        """What _check_disable_term adds to the term title is part of the annex title."""
        self._add_annex(title=u'Text annex', annex_file=self.file_txt)
        vocab = get_vocab(self.folder, u'imio.annex.export_pdf_elements')
        self.assertTrue(vocab._terms[0].title.endswith(u'[PDF required]</span>'))

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
