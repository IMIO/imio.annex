Changelog
=========


1.7 (unreleased)
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
