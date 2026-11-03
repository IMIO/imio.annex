*** Settings ***
Documentation  Adding an annex with its add form: title and description are only in the forms, the file is required.
Resource  imio_annex.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Add an annex
    ${contract} =  A file to upload  contract.txt  Contract content
    Log in as manager
    Go to  ${FOLDER_URL}
    Click the add menu item  annex
    Location should be  ${FOLDER_URL}/++add++annex
    Input text  css=#form-widgets-title  Contract
    Input text  css=#form-widgets-description  Signed contract
    Click button  css=#form-buttons-save
    The field error is  form-widgets-file  Required input is missing.
    Choose file  css=#form-widgets-file-input  ${contract}
    Click button  css=#form-buttons-save
    The status message contains  Item created
    Location should be  ${FOLDER_URL}/contract.txt/view
    Page should contain  contract.txt
    # title and description are not displayed as fields in the view
    Page should not contain element  css=#formfield-form-widgets-title
    Page should not contain element  css=#formfield-form-widgets-description
    Open the annexes tab  ${FOLDER_URL}
    The annex row shows the details  Contract  Signed contract  contract.txt
    The annex row shows the category  Contract  Category
