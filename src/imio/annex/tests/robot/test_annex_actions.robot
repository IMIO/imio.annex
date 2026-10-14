*** Settings ***
Documentation  Annex actions: "View element" (managers) opens the annex view, "Download" downloads its file.
Resource  imio_annex.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
The Download action downloads the annex file
    Log in as manager
    Go to  ${ANNEX_URL}/view
    The content action is available  download
    The content action links to  download  ${ANNEX_URL}/@@download

The View element action opens the annex view
    Log in as manager
    Go to  ${ANNEX_URL}/view
    Click the content action  view_element
    Location should be  ${ANNEX_URL}/view
    Page should contain  annex.txt
    The page is not an error
