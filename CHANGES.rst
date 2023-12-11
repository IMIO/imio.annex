Changelog
=========


2.21 (2023-12-11)
-----------------

- Use our own event `ConversionReallyFinishedEvent` instead
  collective.documentviewer's `ConversionFinishedEvent` because it is called
  when `converting` information is still not set back to `False` and we need
  to have this information when an annex is updated and conversion is run again
  because in this case, `successfully_converted` is still `True`.
  [gbastien]

2.20 (2023-09-04)
-----------------

- Fixed conversion status update that was not working when using async conversion
  with `collective.documentviewer`.
  [gbastien]
- Display action `View preview` when a preview is available.
  [gbastien]

2.19 (2023-08-24)
-----------------

- Adapted code to new parameter `Category.show_preview`
  in `collective.iconifiedcategory`.
  [gbastien]

2.18 (2022-06-14)
-----------------

- Added `safe_utils.py` that will only include safe utils.
  [gbastien]
- Removed override of columns that was done to use `collective.eeafaceted.z3ctable`
  as now at is already the case.
  [gbastien]

2.17 (2022-04-26)
-----------------

- Fixed bug when adding an `annexDecision` because the `content_category`
  could not be retrieved.
  [gbastien]

2.16 (2022-04-22)
-----------------

- Check `validateFileIsPDF` before creating the annex to avoid orphan objects.
  [gbastien]

2.15 (2022-02-25)
-----------------

- Register the `ObjectAddedEvent` and `ObjectModifiedEvent` for `IAnnex`
  so it is not called for other interface.
  [gbastien]

2.14 (2022-02-03)
-----------------

- Accurate french translation for `download-annexes-batch-action-but`.
  [gbastien]

2.13 (2022-01-24)
-----------------

- Set `DownloadAnnexesBatchActionForm.MAX_TOTAL_SIZE` to 25Mb.
  [gbastien]
- Explain in Zip download message that browser may ask to accept popup window.
  [gbastien]
- Open file in new window when clicking on file title in annexes table.
  [gbastien]
- Added a `Download` object_buttons displayed in annex actions_panel.
  [gbastien]

2.12 (2022-01-21)
-----------------

- Fixed `utils.get_annexes_to_print`, use image format (`.png`, `.jpg`, ...)
  stored in annex collective.documentviewer annotation to know the path to
  traverse, this is useful in case image format changed in the global settings.
  [gbastien]

2.11 (2022-01-03)
-----------------

- Added `annex.UID` method to speed up getting the UID.
  [gbastien]

2.10 (2021-11-08)
-----------------

- Display the annex `filename` and `scan_id` in the categorized elemens table
  under the description.
  [gbastien]

2.9 (2021-07-16)
----------------

- Override `collective.iconifiedcategory` columns `category-column`,
  `creation-date-column`, `last-modification-column` and `filesize-column` to
  use `collective.eeafaceted.z3ctable` based columns instead the original
  `z3c.table` columns so we have custom CSS classes.
  [gbastien]
- Added `DownloadAnnexesBatchActionForm`, a batch action to download several
  annexes as a Zip file :
  - download is handled by an ajax request;
  - max download size is 50Mb by default.
  [gbastien]

2.8 (2021-04-23)
----------------

- Fixed `quickupload.ImioAnnexQuickUploadCapableFileFactory` to make sure that
  thread lock is released like it is the case by default in
  `uploadcapable.QuickUploadCapableFileFactory`.
  This should avoid rare cases where instance is stuck while adding an annex.
  [gbastien]

2.7 (2020-05-08)
----------------

- Test if current obj provides `IAnnex` instead `IIconifiedCategorization` as
  it is no longer provided to fix a bug in `collective.iconifiedcategory`.
  [gbastien]

2.6 (2020-04-23)
----------------

- Avoid orphan annex left without a content_category when a `ConflictError`
  occurs during file upload because upload is done by a separate `XHR request`.
  [gbastien]

2.5 (2020-03-12)
----------------

- Override `collective.quickupload` `QuickUploadCapableFileFactory` to avoid
  calling object added/created/modified events more than one time.
  [gbastien]
- While adding an annex, call `validateFileIsPDF` to manage the `pdf_only`
  parameter as `invariants` are not called by default.
  [gbastien]

2.4 (2019-05-16)
----------------

- Use `imio.helpers` default dexterity container view override on
  `ContentCategoryConfiguration` elements so contained `ContentCategoryGroup`
  objects are displayed on the view.
  [gbastien]
- Fixed bug when adding an annex after CKeditor was used to add an image, the
  mediaupload type is stored in the SESSION and reused when another
  quick_upload is displayed (bug in collective.ckeditor?).
  When displaying the quick_upload to add annexes, we make sure
  mediaupload/typeupload attributes are removed from SESSION.
  [gbastien]

2.3 (2019-01-31)
----------------

- Adapted `collective.quickupload` override so it work both with portlet
  and viewlet, manage `content_category` correctly and updated styles using
  `FontAwesome` to be compatible with `FontAwesome 5 Free`.
  `Quickupload` is displayed in an overlay.
  [gbastien]

2.2 (2018-11-20)
----------------

- `ActionsColumn` was moved from `imio.dashboard`
  to `collective.eeafaceted.z3ctable.columns`.
  [gbastien]

2.1 (2018-09-04)
----------------

- `PrettyLinkColumn` was moved from `collective.eeafaceted.dashboard`
  to `collective.eeafaceted.z3ctable.columns`.
  [gbastien]

2.0 (2018-06-20)
----------------

- Rely on `collective.eeafaceted.dashboard`.
  [gbastien]

1.9 (2018-01-23)
----------------

- Display icon of the `@@historyview` in the `ActionsColumn`.
  [gbastien]
- Added parameter `called_by` to the `AnnexFileChangedEvent` so it can be used
  to specify where it was called from and so the registered event handler may
  use it if necessary.
  [gbastien]
- Added `Scan metadata (fields to_sign/signed hidden)` behavior that inherits
  from `collective.dms.scanbehavior.behaviors.behaviors.IScanFields` behavior
  and hides fields `to_sign` and `signed`.
  [gbastien]
- Apply relevant behaviors using `purge=True` so we are sure what behaviors
  are enabled.
  [gbastien]
- Profile `zamqp` does not depend on `imio.annex:default` profile anymore so it
  is possible to reapply it without reapplying every `imio.annex:default`
  dependencies.
  [gbastien]

1.8 (2017-12-07)
----------------

- Translate columns `Title` and `Actions`.
  [gbastien]


1.7 (2017-09-15)
----------------

- Removed `collective.dms.scanbehavior` from behaviors added by the default
  profile.
  [gbastien]


1.6 (2017-08-29)
----------------

- Enable `Scan metadata` behavior from `collective.dms.scanbehavior` for the
  `annex` type.  We use it together with the `Signed?` functionnality available
  in `collective.iconifiedcategory` if `[zamqp]` is enabled.
  [gbastien]
- Make sure an `undefined` `content_category` is not added when uploading
  elements using the quickupload portlet and content_category is not enabled
  on the portlet.
  [gbastien]


1.5 (2017-07-19)
----------------

- In `utils.get_annexes_to_print` do not fail to get annex if a folder in the
  path to the annex is private.
  [gbastien]


1.4 (2017-03-08)
----------------

- Added helper method `utils.get_annexes_to_print` to ease printings of annexes
  set `to_print`.
  [gbastien]
- Make the title optional and get the filename if no title is specified
  [mpeeters]
- As `view` is already overrided in `collective.iconifiedcategory`, we need to
  override it in `overrides.zcml` and override the one from
  `collective.iconifiedcategory` not the one from `plone.dexterity`.
  [gbastien]


1.3 (2017-01-25)
----------------

- In `annex_conversion_started`/`annex_conversion_finished`, do not trigger
  `ObjectModifiedEvent` to avoid circular calls when another
  `ObjectModifiedEvent` event handler is managing conversion too.  Just call
  `update_categorized_elements` that will update relevant informations in
  `categorized_elements` dict
  [gbastien]


1.2 (2017-01-12)
----------------

- Extend collective.quickupload portlet to add content categories : #12556
  [mpeeters]
- Remove 'description' of portal_type 'annex' or it is displayed
  when adding/editing an annex
  [gbastien]
- Take parameter sort_categorized_tab into account for the showArrows parameter :
  only show arrows if sort_categorized_tab is False
  [gbastien]


1.1 (2016-12-08)
----------------

- Do not fail to display annex description in prettyLink column if it contains
  special characters.
  [gbastien]


1.0 (2016-12-02)
----------------

- Initial release.
  [mpeeters]
