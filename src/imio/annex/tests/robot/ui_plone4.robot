*** Settings ***
Documentation  Plone 4.3 keywords. Same keyword names and arguments as ui_plone6.robot.
...            Robot Framework 3.0 syntax (Python 2 environment).
...            NOT CHECKED YET on a Plone 4.3 site: fix the selectors on the first run
...            and report the fixes in the Feedback section of MIGRATION.md.
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote


*** Variables ***
${MODAL}  css=div.overlay-ajax
${ERROR_PAGE_TEXT}  there seems to be an error
${NOT_FOUND_TEXT}  This page does not seem to exist


*** Keywords ***
Log in with the login form
    [Documentation]  Real login (creates the user folder), unlike autologin
    [Arguments]  ${username}  ${password}
    Disable autologin
    Go to  ${PLONE_URL}/login_form
    Input text  css=#__ac_name  ${username}
    Input password  css=#__ac_password  ${password}
    Click button  css=input[name="submit"]
    # #portal-personaltools is also shown to anonymous users
    Wait until page contains element  css=#user-name

Click the content action
    [Documentation]  Item of the Actions menu (object_buttons), by action id
    [Arguments]  ${action_id}
    Click element  css=#plone-contentmenu-actions dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-actions-${action_id}
    Click element  css=#plone-contentmenu-actions-${action_id}

The content action is available
    [Arguments]  ${action_id}  ${expected}=${True}
    Click element  css=#plone-contentmenu-actions dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-actions dd.actionMenuContent
    Run keyword if  ${expected}
    ...  Page should contain element  css=#plone-contentmenu-actions-${action_id}
    ...  ELSE  Page should not contain element  css=#plone-contentmenu-actions-${action_id}

Open the add menu
    Click element  css=#plone-contentmenu-factories dt.actionMenuHeader a
    Wait until element is visible  css=#plone-contentmenu-factories dd.actionMenuContent

The personal action links to
    [Documentation]  Item of the user menu (user actions), by action id
    [Arguments]  ${action_id}  ${url}
    Element attribute value should be  css=#personaltools-${action_id} a  href  ${url}

The personal action is not available
    [Arguments]  ${action_id}
    Page should not contain element  css=#personaltools-${action_id}

The modal is open
    [Documentation]  Overlay (Plone 4) or modal (Plone 6) showing a form
    Wait until element is visible  ${MODAL} form

Modal element
    [Documentation]  Locator of the element with this id inside the modal
    ...              (an argument starting with # would be a robot comment)
    [Arguments]  ${id}
    [Return]  ${MODAL} [id="${id}"]

Save the modal
    Click button  ${MODAL} #form-buttons-save

Cancel the modal
    Click button  ${MODAL} #form-buttons-cancel

The modal is closed
    Wait until element is not visible  ${MODAL}

The status message contains
    [Arguments]  ${text}
    # skip the hidden #kssPortalMessage
    Wait until element contains  css=dl.portalMessage:not([style*="display:none"])  ${text}

The page is not an error
    Page should not contain  ${ERROR_PAGE_TEXT}

The page is not found
    Page should contain  ${NOT_FOUND_TEXT}

The edit link is not available
    Page should not contain element  css=#contentview-edit

Click the content view
    [Documentation]  Tab of the content views (object actions), by action id
    [Arguments]  ${action_id}
    Click link  css=#contentview-${action_id} a

The content action links to
    [Documentation]  Item of the Actions menu (object_buttons), by action id
    [Arguments]  ${action_id}  ${url}
    Element attribute value should be  css=#plone-contentmenu-actions-${action_id}  href  ${url}

Click the add menu item
    [Documentation]  Item of the add menu, by portal type
    [Arguments]  ${portal_type}
    Open the add menu
    Click link  css=#plone-contentmenu-factories a#${portal_type}

Open in a modal
    [Documentation]  Load the URL in an ajax overlay (Plone 4) or a modal (Plone 6), as a page link would
    [Arguments]  ${url}
    Execute javascript  jQuery('<a id="robot-modal-link"></a>').attr('href', '${url}').appendTo('body').prepOverlay({subtype: 'ajax'}).click(); return true;
    Wait until element is visible  ${MODAL}

The field error is
    [Arguments]  ${field_id}  ${message}
    Element should contain  css=#formfield-${field_id} .fieldErrorBox  ${message}

Select in the select2 widget
    [Documentation]  Pick an option in the select2 widget inside this css locator
    [Arguments]  ${locator}  ${label}
    Click element  ${locator} .select2-choice
    Wait until element is visible  css=#select2-drop .select2-results
    Click element  xpath=//div[@id="select2-drop"]//div[contains(@class, "select2-result-label")][contains(., "${label}")]
    Wait until element is not visible  css=#select2-drop

The select2 widget shows
    [Arguments]  ${locator}  ${label}
    Element should contain  ${locator} .select2-chosen  ${label}
