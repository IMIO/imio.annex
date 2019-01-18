# -*- coding: utf-8 -*-
"""
imio.annex
----------

Created by mpeeters
:license: GPL, see LICENCE.txt for more details.
"""

from Acquisition import aq_inner
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ZODB.POSException import ConflictError
from collective.quickupload import logger
from collective.quickupload.browser.quick_upload import QuickUploadFile
from collective.quickupload.browser.quick_upload import QuickUploadView
from collective.quickupload.browser.quick_upload import getDataFromAllRequests
from collective.quickupload.browser.quick_upload import get_content_type
from collective.quickupload.browser.uploadcapable import MissingExtension
from collective.quickupload.browser.uploadcapable import get_id_from_filename
from collective.quickupload.interfaces import IQuickUploadFileFactory
from collective.quickupload.interfaces import IQuickUploadFileUpdater
from plone.i18n.normalizer.interfaces import IUserPreferredFileNameNormalizer
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent

import json
import urllib

import pkg_resources
try:
    pkg_resources.get_distribution('plone.uuid')
    from plone.uuid.interfaces import IUUID
    HAS_UUID = True
except pkg_resources.DistributionNotFound:
    HAS_UUID = False

from imio.annex.quickupload import utils


class QuickUploadPortletView(QuickUploadView):
    template = ViewPageTemplateFile("templates/quick_upload.pt")

    @property
    def typeupload(self):
        context = aq_inner(self.context)
        config = context.restrictedTraverse('@@quick_upload_init')
        config.uploader_id = self.uploader_id
        return config.upload_settings().get('typeupload')

    @property
    def is_iconified_categorized(self):
        return utils.is_iconified_categorized(self.typeupload)

    def script_content(self):
        result = super(QuickUploadPortletView, self).script_content()
        return u"""
{0}
jQuery('a#copy_categories').click(PloneQuickUpload.extendCategories);
        """.format(result)


class QuickUploadFileView(QuickUploadFile):

    def _manage_extra_parameters(self, request, f):
        """Manage extra parameters, particularly content_category."""
        # Extra parameters
        content_category = getDataFromAllRequests(request, 'content_category') or ''
        # Add an extra parameter
        if f['success'] and content_category:
            f['success'].content_category = content_category
            # elements using content_category are initialized in the object created event
            notify(ObjectAddedEvent(f['success']))

    def quick_upload_file(self):
        """Copied from collective.quickupload"""
        context = aq_inner(self.context)
        request = self.request
        response = request.RESPONSE

        response.setHeader('Expires', 'Sat, 1 Jan 2000 00:00:00 GMT')
        response.setHeader('Cache-control', 'no-cache')
        # application/json is not supported by old IEs but text/html fails in
        # every browser with plone.protect 3.0.11
        response.setHeader('Content-Type', 'application/json; charset=utf-8')
        # disable diazo themes and csrf protection
        request.response.setHeader('X-Theme-Disabled', 'True')

        if request.HTTP_X_REQUESTED_WITH:
            # using ajax upload
            file_name = urllib.unquote(request.HTTP_X_FILE_NAME)
            upload_with = "XHR"
            try:
                file = request.BODYFILE
                file_data = file.read()
                file.seek(0)
            except AttributeError:
                # in case of cancel during xhr upload
                logger.error("Upload of %s has been aborted", file_name)
                # not really useful here since the upload block
                # is removed by "cancel" action, but
                # could be useful if someone change the js behavior
                return json.dumps({u'error': u'emptyError'})
            except:
                logger.error(
                    "Error when trying to read the file %s in request",
                    file_name
                )
                return json.dumps({u'error': u'serverError'})
        else:
            # using classic form post method (MSIE<=8)
            file = request.get("qqfile", None)
            file_data = file.read()
            file.seek(0)
            filename = getattr(file, 'filename', '')
            file_name = filename.split("\\")[-1]
            try:
                file_name = file_name.decode('utf-8')
            except UnicodeDecodeError:
                pass

            file_name = IUserPreferredFileNameNormalizer(
                self.request
            ).normalize(file_name)
            upload_with = "CLASSIC FORM POST"
            # we must test the file size in this case (no client test)
            if not self._check_file_size(file):
                logger.info("Test file size: the file %s is too big, upload "
                            "rejected" % filename)
                return json.dumps({u'error': u'sizeError'})

        # overwrite file
        try:
            newid = get_id_from_filename(
                file_name, context, unique=self.qup_prefs.object_unique_id)
        except MissingExtension:
            return json.dumps({u'error': u'missingExtension'})

        if (newid in context or file_name in context) and \
                not self.qup_prefs.object_unique_id:
            updated_object = context.get(newid, False) or context[file_name]
            mtool = getToolByName(context, 'portal_membership')
            override_setting = self.qup_prefs.object_override
            if override_setting and\
                    mtool.checkPermission(ModifyPortalContent, updated_object):
                can_overwrite = True
            else:
                can_overwrite = False

            if not can_overwrite:
                logger.debug(
                    "The file id for %s already exists, upload rejected"
                    % file_name
                )
                return json.dumps({u'error': u'serverErrorAlreadyExists'})

            overwritten_file = updated_object
        else:
            overwritten_file = None

        content_type = get_content_type(context, file_data, file_name)

        portal_type = getDataFromAllRequests(request, 'typeupload') or ''
        title = getDataFromAllRequests(request, 'title') or ''
        description = getDataFromAllRequests(request, 'description') or ''
        if not title.strip() and self.qup_prefs.id_as_title:
            title = newid

        if not portal_type:
            ctr = getToolByName(context, 'content_type_registry')
            portal_type = ctr.findTypeName(
                file_name.lower(), content_type, ''
            ) or 'File'

        if file_data:
            if overwritten_file is not None:
                updater = IQuickUploadFileUpdater(context)
                logger.info(
                    "reuploading %s file with %s: title=%s, description=%s, "
                    "content_type=%s"
                    % (overwritten_file.absolute_url(), upload_with, title,
                       description, content_type))
                try:
                    f = updater(overwritten_file, file_name, title,
                                description, content_type, file_data)
                    # manage extra parameters
                    self._manage_extra_parameters(request, f)
                except ConflictError:
                    # Allow Zope to retry up to three times, and if that still
                    # fails, handle ConflictErrors on client side if necessary
                    raise
                except Exception as e:
                    logger.error(
                        "Error updating %s file: %s", file_name, str(e)
                    )
                    return json.dumps({u'error': u'serverError'})

            else:
                factory = IQuickUploadFileFactory(context)
                logger.info(
                    "uploading file with %s: filename=%s, title=%s, "
                    "description=%s, content_type=%s, portal_type=%s"
                    % (upload_with, file_name, title,
                       description, content_type, portal_type))
                try:
                    f = factory(file_name, title, description, content_type,
                                file_data, portal_type)
                    # manage extra parameters
                    self._manage_extra_parameters(request, f)
                except ConflictError:
                    # Allow Zope to retry up to three times, and if that still
                    # fails, handle ConflictErrors on client side if necessary
                    raise
                except Exception as e:
                    logger.error(
                        "Error creating %s file: %s", file_name, str(e)
                    )
                    return json.dumps({u'error': u'serverError'})

            if f['success'] is not None:
                o = f['success']
                logger.info("file url: %s" % o.absolute_url())
                if HAS_UUID:
                    uid = IUUID(o)
                else:
                    uid = o.UID()

                msg = {
                    u'success': True,
                    u'uid': uid,
                    u'name': o.getId(),
                    u'title': o.pretty_title_or_id()
                }
            else:
                msg = {u'error': f['error']}
        else:
            msg = {u'error': u'emptyError'}

        return json.dumps(msg)
