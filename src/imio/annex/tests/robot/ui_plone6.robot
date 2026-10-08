*** Settings ***
Documentation  Plone 6 Classic UI keywords. Same keyword names and arguments as ui_plone4.robot.
...            Robot Framework 3.0 syntax: shared with the Plone 4.3 (Python 2) environment.
...            Selectors checked on Plone 6.1 (collective.contact.contactlist).
Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot
Library  Remote  ${PLONE_URL}/RobotRemote


*** Variables ***
${MODAL}  css=.modal-dialog
${ERROR_PAGE_TEXT}  there seems to be an error
${NOT_FOUND_TEXT}  This page does not seem to exist


*** Keywords ***
Log in with the login form
    [Documentation]  Real login (creates the user folder), unlike autologin
    [Arguments]  ${username}  ${password}
    Disable autologin
    Go to  ${PLONE_URL}/login
    Input text  css=#__ac_name  ${username}
    Input password  css=#__ac_password  ${password}
    Click button  css=#buttons-login
    Wait until page contains element  css=#personaltools-menulink

Click the content action
    [Documentation]  Item of the Actions menu (object_buttons), by action id
    [Arguments]  ${action_id}
    Click element  css=#plone-contentmenu-actions > a
    Wait until element is visible  css=#plone-contentmenu-actions-${action_id}
    Click element  css=#plone-contentmenu-actions-${action_id}

The content action is available
    [Arguments]  ${action_id}  ${expected}=${True}
    Click element  css=#plone-contentmenu-actions > a
    Wait until element is visible  css=#plone-contentmenu-actions ul
    Run keyword if  ${expected}
    ...  Page should contain element  css=#plone-contentmenu-actions-${action_id}
    ...  ELSE  Page should not contain element  css=#plone-contentmenu-actions-${action_id}

Open the add menu
    Click element  css=#plone-contentmenu-factories > a
    Wait until element is visible  css=#plone-contentmenu-factories ul

The personal action links to
    [Documentation]  Item of the user menu (user actions), by action id
    [Arguments]  ${action_id}  ${url}
    Element attribute value should be  css=#personaltools-${action_id}  href  ${url}

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
    Click button  css=.modal-footer #form-buttons-save

Cancel the modal
    Click button  css=.modal-footer #form-buttons-cancel

The modal is closed
    Wait until page does not contain element  ${MODAL}

The status message contains
    [Arguments]  ${text}
    Wait until element contains  css=.portalMessage  ${text}

The page is not an error
    Page should not contain  ${ERROR_PAGE_TEXT}

The page is not found
    Page should contain  ${NOT_FOUND_TEXT}

The edit link is not available
    Page should not contain element  css=#contentview-edit

# NOT CHECKED YET on Plone 6 (written in phase 3 on Plone 4.3): fix in phase 8.
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
    Execute javascript  var a = document.createElement('a'); a.id = 'robot-modal-link'; a.href = '${url}'; a.className = 'pat-plone-modal'; document.body.appendChild(a); new window.__patternslib_registry['plone-modal'](a); return true;
    Click element  css=#robot-modal-link
    Wait until element is visible  ${MODAL}

The field error is
    [Arguments]  ${field_id}  ${message}
    Element should contain  css=#formfield-${field_id} .invalid-feedback  ${message}

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
