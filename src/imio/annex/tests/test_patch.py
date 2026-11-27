# -*- coding: utf-8 -*-

from imio.annex.tests.base import BaseTestCase
from imio.helpers.testing import testing_logger
from plone import api
from plone.namedfile.file import NamedBlobImage
from Products.CMFCore.WorkflowTool import WorkflowTool
from Products.CMFPlone.CatalogTool import CatalogTool
from timeit import default_timer


logger = testing_logger('imio.annex: testing')

# a 1x1 pixel GIF image
GIF = ('GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
       '\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


class TestPatch(BaseTestCase):

    def _create_elements(self, portal_type, number):
        """Create p_number elements of p_portal_type, return the time spent, the number
        of times an element was (re)catalogued and the time spent to catalog."""
        # create elements in a new folder as adding an element to a folder
        # takes longer when the folder already holds many categorized elements
        self.folder = api.content.create(
            container=self.portal, type='Folder', title=u'Folder {0}'.format(portal_type))
        # durations of every catalog_object call
        catalogued = []
        catalog_object = CatalogTool.__dict__['catalog_object']

        def counted_catalog_object(catalog, *args, **kwargs):
            start = default_timer()
            try:
                return catalog_object(catalog, *args, **kwargs)
            finally:
                catalogued.append(default_timer() - start)
        CatalogTool.catalog_object = counted_catalog_object
        try:
            start = default_timer()
            for i in range(number):
                title = u'{0} {1}'.format(portal_type, i)
                # use a txt file so the measure is not spoiled by the PDF preview conversion
                if portal_type == 'annex':
                    self._add_annex(title=title, annex_file=self.file_txt)
                    continue
                # File and Image are categorized in the test profile
                kwargs = {'content_category': 'config_-_group-1_-_category-1-1'}
                if portal_type == 'File':
                    kwargs['file'] = self.file_txt
                else:
                    kwargs['image'] = NamedBlobImage(GIF, filename=u'image.gif')
                api.content.create(container=self.folder, type=portal_type, title=title, **kwargs)
            duration = default_timer() - start
        finally:
            CatalogTool.catalog_object = catalog_object
        return duration, len(catalogued), sum(catalogued)

    def test_reindex_workflow_variables(self):
        """WorkflowTool._reindexWorkflowVariables does nothing for an element without
        workflow as when it is added, it is completely indexed right after."""
        wf_tool = api.portal.get_tool('portal_workflow')
        catalog = api.portal.get_tool('portal_catalog')
        # an element without workflow is correctly indexed when added
        annex = self._add_annex()
        self.assertEqual(wf_tool.getWorkflowsFor(annex), [])
        self.assertEqual(catalog(UID=annex.UID())[0].Title, 'Annex')
        # but it is not reindexed
        annex.title = u'New title'
        wf_tool._reindexWorkflowVariables(annex)
        self.assertEqual(catalog(UID=annex.UID())[0].Title, 'Annex')
        # an element with a workflow is still reindexed
        wf_tool.setChainForPortalTypes(('Folder', ), ('simple_publication_workflow', ))
        self.folder.setTitle(u'New title')
        wf_tool._reindexWorkflowVariables(self.folder)
        self.assertEqual(catalog(UID=self.folder.UID())[0].Title, 'New title')

        # without the patch, an element without workflow was completely
        # catalogued 2 times when added, compare with and without the patch
        patched = WorkflowTool.__dict__['_reindexWorkflowVariables']
        for portal_type in ('annex', 'File', 'Image'):
            self.assertEqual(wf_tool.getChainForPortalType(portal_type), ())
            # warm up so the first measure is not penalized
            self._create_elements(portal_type, 5)
            WorkflowTool._reindexWorkflowVariables = WorkflowTool._old__reindexWorkflowVariables
            try:
                without = self._create_elements(portal_type, 50)
            finally:
                WorkflowTool._reindexWorkflowVariables = patched
            with_patch = self._create_elements(portal_type, 50)
            logger.info(
                'Created 50 {0}: '
                'without the patch {1[0]:.2f}s and catalogued {1[1]} times in {1[2]:.2f}s, '
                'with the patch {2[0]:.2f}s and catalogued {2[1]} times in {2[2]:.2f}s'.format(
                    portal_type, without, with_patch))
            self.assertLess(with_patch[1], without[1])
