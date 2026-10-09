*** Settings ***
Documentation  The categories configuration, group, category and subcategory views
...            are the imio.helpers container (fields and contents) and content (fields) views.
Resource  imio_annex.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
The category containers show their fields and contents
    Enable autologin as  Manager
    Create content  type=ContentSubcategory  container=/plone/config/group/category  id=subcategory
    ...  title=Subcategory  predefined_title=Sub
    Log in as manager
    Go to  ${CONFIG_URL}
    The page lists the content  Group
    Go to  ${CONFIG_URL}/group
    The page shows the field  to_be_printed_activated  yes
    The page lists the content  Category
    The page lists the content  PDF only
    Go to  ${CONFIG_URL}/group/category
    The page shows the field  predefined_title  Category
    The page lists the content  Subcategory

The subcategory shows its fields only
    Enable autologin as  Manager
    Create content  type=ContentSubcategory  container=/plone/config/group/category  id=subcategory
    ...  title=Subcategory  predefined_title=Sub
    Log in as manager
    Go to  ${CONFIG_URL}/group/category/subcategory
    The page shows the field  predefined_title  Sub
    Page should not contain element  css=#imio-helpers-folder-listing-table
