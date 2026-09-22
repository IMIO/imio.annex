# -*- coding: utf-8 -*-

from collective.iconifiedcategory.config import get_sort_categorized_tab
from collective.iconifiedcategory.utils import get_categorized_elements
from collective.iconifiedcategory.utils import render_filesize
from imio.helpers.content import get_vocab
from plone import api
from Products.CMFPlone.utils import safe_unicode
from zope.i18n import translate
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import cgi


class ContainedAnnexesVocabulary(object):
    """Vocabulary listing the annexes contained in the context, terms may be
       disabled by overriding _check_disable_term."""

    implements(IVocabularyFactory)

    def __call__(
            self,
            context,
            portal_type='annex',
            token_value='id',
            include_portal_type=False,
            include_parent_title=False,
            filters={}):
        """ """
        portal = api.portal.get()
        portal_url = portal.absolute_url()
        terms = []
        i = 1
        sort_on = 'getObjPositionInParent' if \
            get_sort_categorized_tab() is False else None
        annex_infos = get_categorized_elements(
            context, portal_type=portal_type, sort_on=sort_on, filters=filters)
        if annex_infos:
            categories_vocab = get_vocab(
                context,
                'collective.iconifiedcategory.categories',
                use_category_uid_as_token=True)
            parent_title = u'%s<br><span class="titleVisualPadding">➔ </span>' % \
                safe_unicode(context.Title()) \
                if include_parent_title else ''
            portal_type_title = u'%s - ' % translate(
                portal.portal_types[portal_type].title,
                domain="imio.annex",
                context=context.REQUEST) if include_portal_type else ''

            for annex_info in annex_infos:
                # term title is annex icon, number and title
                term_title = u'{0}<img src="{1}/{2}" title="{3}" ' \
                    u'width="16px" height="16px"> {4}{5}. {6}'.format(
                        parent_title,
                        portal_url,
                        annex_info['icon_url'],
                        cgi.escape(safe_unicode(annex_info['category_title']), True),
                        portal_type_title,
                        str(i),
                        cgi.escape(safe_unicode(annex_info['title']), True))
                i += 1
                if annex_info['warn_filesize']:
                    term_title += u' ({0})'.format(render_filesize(annex_info['filesize']))
                term = SimpleTerm(annex_info[token_value], annex_info[token_value], term_title)
                term.description = annex_info['description'].replace('\n', '<br>')
                # check if need to disable term
                self._check_disable_term(context, annex_info, categories_vocab, term)
                terms.append(term)
        return SimpleVocabulary(terms)

    def _check_disable_term(self, context, annex_info, categories_vocab, term):
        """By default, disable if not downloadable (only previewable)."""
        term.disabled = False
        if annex_info['show_preview'] == 2 and \
           not context.get(annex_info['id']).show_download():
            term.disabled = True
            term.title += translate(' [only previewable]',
                                    domain='imio.annex',
                                    context=context.REQUEST)


ContainedAnnexesVocabularyFactory = ContainedAnnexesVocabulary()


class ExportPDFElementsVocabulary(ContainedAnnexesVocabulary):
    """Annexes that may be concatenated into a single PDF,
       every non PDF annex is disabled."""

    def _check_disable_term(self, context, annex_info, categories_vocab, term):
        super(ExportPDFElementsVocabulary, self)._check_disable_term(
            context, annex_info, categories_vocab, term)
        if term.disabled is False and \
           annex_info['contentType'] != 'application/pdf':
            term.disabled = True
            term.title += translate(' [PDF required]',
                                    domain='imio.annex',
                                    context=context.REQUEST)


ExportPDFElementsVocabularyFactory = ExportPDFElementsVocabulary()
