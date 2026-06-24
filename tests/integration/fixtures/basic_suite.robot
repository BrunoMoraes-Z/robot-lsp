*** Settings ***
Documentation    Suite documentation
Metadata         Owner    Platform Team
Library          Collections    WITH NAME    Col
Resource         resource.robot
Variables        variables.py    prod
Suite Setup      Log    suite setup
Test Setup       Log    test setup
Test Tags        smoke    fast

*** Variables ***
${MESSAGE}    Hello, World!
@{ITEMS}      one    two    three
&{CONFIG}     env=dev    retries=3

*** Test Cases ***
My Test
    [Documentation]    A simple test
    [Tags]    critical
    Log    ${MESSAGE}
    My Keyword    value

*** Keywords ***
My Keyword
    [Arguments]    ${arg}=default    @{items}
    [Documentation]    Keyword documentation
    Log    ${arg}
