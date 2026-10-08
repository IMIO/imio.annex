*** Settings ***
Documentation  imio.annex keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Fixture (testing.py): categories config/group/category and config/group/pdf-category (PDF only),
...            folder holding the annexes annex and annex-2 (annex.txt, category Category, by test_user_1_).
Resource  ui_plone${PLONE_MAJOR}.robot
Library  OperatingSystem


*** Variables ***
${MANAGER}  manager
${MANAGER_PASSWORD}  manager123
${CONFIG_URL}  ${PLONE_URL}/config
${FOLDER_URL}  ${PLONE_URL}/folder
${ANNEX_URL}  ${FOLDER_URL}/annex
${ANNEXES_TABLE}  //table[contains(@class, "iconified-listing")]


*** Keywords ***
Log in as manager
    Log in with the login form  ${MANAGER}  ${MANAGER_PASSWORD}

A file to upload
    [Documentation]  Path of a new file of the robot output directory
    [Arguments]  ${filename}  ${content}=%PDF-1.4
    Create file  ${OUTPUT DIR}${/}${filename}  ${content}
    [Return]  ${OUTPUT DIR}${/}${filename}

Open the annexes tab
    [Arguments]  ${url}
    Go to  ${url}
    Click the content view  iconifiedcategory
    Wait until page contains element  xpath=${ANNEXES_TABLE}

The annex row
    [Documentation]  Locator of the row of the annexes tab showing this title
    [Arguments]  ${title}
    [Return]  xpath=${ANNEXES_TABLE}//tr[.//span[@class="pretty_link_content"][normalize-space()="${title}"]]

# Quick upload

Open the quick upload
    [Documentation]  On the annexes tab, @@quick_upload opened in an overlay, as imio.dms.mail and Products.PloneMeeting do
    [Arguments]  ${url}
    Open the annexes tab  ${url}
    Open in a modal  ${url}/@@quick_upload?typeupload=annex
    Wait until element is visible  css=.quick-uploader .qq-upload-button

Choose the file to upload
    [Arguments]  ${path}
    Choose file  css=.quick-uploader .qq-upload-button input[type="file"]  ${path}

The uploaded file form
    [Documentation]  Css locator of the form loaded for the uploaded file at this position (from 1)
    [Arguments]  ${position}
    [Return]  css=.quick-uploader .qq-upload-list li:nth-child(${position}) form

The uploaded file form is loaded
    [Arguments]  ${position}  ${filename}
    ${form} =  The uploaded file form  ${position}
    Wait until element is visible  ${form} .select2-container
    Element should contain  css=.quick-uploader .qq-upload-list li:nth-child(${position}) .qq-upload-file  ${filename}
    Element should be visible  ${form} input[name="form.widgets.title"]
    Element should be visible  ${form} textarea[name="form.widgets.description"]

Fill the uploaded file form
    [Arguments]  ${position}  ${title}  ${description}=${EMPTY}
    ${form} =  The uploaded file form  ${position}
    Input text  ${form} input[name="form.widgets.title"]  ${title}
    Input text  ${form} textarea[name="form.widgets.description"]  ${description}

Copy the first category to all files
    Click link  css=.quick-uploader a#copy_categories

Upload the files
    Click button  css=.quick-uploader #uploadify-upload
    # the page is reloaded once all files are uploaded
    Wait until page does not contain element  css=.quick-uploader
    Wait until page contains element  xpath=${ANNEXES_TABLE}

# Annexes tab

The annex row shows the pretty link
    [Documentation]  Category icon and title, opening the file download in a new tab
    [Arguments]  ${title}  ${category}  ${url}
    ${row} =  The annex row  ${title}
    Page should contain element  ${row}//a[@class="pretty_link"][@href="${url}/@@download"][@target="_blank"]//span[@class="pretty_link_icons"]/img[@title="${category}"]

The annex row shows the details
    [Documentation]  Texts under the pretty link: description, file name, scan id
    [Arguments]  ${title}  @{texts}
    ${row} =  The annex row  ${title}
    FOR  ${text}  IN  @{texts}
        Element should contain  ${row}//td[@class="pretty_link"]  ${text}
    END

The annex row shows the category
    [Arguments]  ${title}  ${category}
    ${row} =  The annex row  ${title}
    Page should contain element  ${row}//span[@class="pretty_link_icons"]/img[@title="${category}"]
    Element should contain  ${row}//td[@class="td_cell_category-column"]  ${category}

The annex row shows the author
    [Arguments]  ${title}  ${author}
    ${row} =  The annex row  ${title}
    Element should contain  ${row}//td[@class="td_cell_author-column"]  ${author}

The annex row shows the actions
    [Documentation]  History, view element and download actions
    [Arguments]  ${title}  ${url}
    ${row} =  The annex row  ${title}
    ${actions} =  Set variable  ${row}//td[@class="td_cell_action-column"]
    Page should contain element  ${actions}//a[contains(@class, "overlay-history")][@href="${url}/@@historyview"]
    Page should contain element  ${actions}//a[@href="${url}/view"]/img[@title="View element"]
    Page should contain element  ${actions}//a[@href="${url}/@@download"][@target="_blank"]/img[@title="Download"]

# Category configuration

The page lists the content
    [Documentation]  Contents listing of the imio.helpers container view
    [Arguments]  ${title}
    Element should contain  css=#imio-helpers-folder-listing-table  ${title}

The page shows the field
    [Documentation]  Field of the imio.helpers container/content view
    [Arguments]  ${field_name}  ${value}
    Element should contain  css=#row-form-widgets-${field_name} .table_widget_value  ${value}
