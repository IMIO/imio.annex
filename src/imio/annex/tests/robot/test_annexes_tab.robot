*** Settings ***
Documentation  The annexes tab (Categorized elements) of a folder lists its annexes
...            with the imio.annex title, author and actions columns.
Resource  imio_annex.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
The annexes tab lists an annex with its details, author and actions
    Enable autologin as  Manager
    ${uid} =  Path to uid  /plone/folder/annex
    Set field value  ${uid}  description  Signed contract  str
    Set field value  ${uid}  scan_id  IMIO000123  str
    Log in as manager
    Open the annexes tab  ${FOLDER_URL}
    The annex row shows the pretty link  Annex  Category  ${ANNEX_URL}
    The annex row shows the details  Annex  Signed contract  annex.txt  IMIO000123
    The annex row shows the category  Annex  Category
    The annex row shows the author  Annex  test_user_1_
    The annex row shows the actions  Annex  ${ANNEX_URL}
    The annex row shows the pretty link  Annex 2  Category  ${FOLDER_URL}/annex-2
