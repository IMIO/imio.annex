*** Settings ***
Documentation  Adding annexes with the quick upload opened from the annexes tab:
...            a form per file (title, category, description), the "copy the first category" button.
Resource  imio_annex.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Upload annexes with the quick upload
    ${contract} =  A file to upload  contract.pdf
    ${invoice} =  A file to upload  invoice.pdf
    Log in as manager
    Open the quick upload  ${FOLDER_URL}
    Choose the file to upload  ${contract}
    The uploaded file form is loaded  1  contract.pdf
    Choose the file to upload  ${invoice}
    The uploaded file form is loaded  2  invoice.pdf
    ${first} =  The uploaded file form  1
    ${second} =  The uploaded file form  2
    The select2 widget shows  ${second}  Category
    Select in the select2 widget  ${first}  PDF only
    # the category fills the title with its predefined title
    Textfield value should be  ${first} input[name="form.widgets.title"]  PDF only
    Copy the first category to all files
    The select2 widget shows  ${second}  PDF only
    Fill the uploaded file form  1  Contract  Signed contract
    Fill the uploaded file form  2  Invoice
    Upload the files
    The annex row shows the category  Contract  PDF only
    The annex row shows the details  Contract  Signed contract  contract.pdf
    The annex row shows the author  Contract  Manager
    The annex row shows the category  Invoice  PDF only
    The annex row shows the details  Invoice  invoice.pdf
