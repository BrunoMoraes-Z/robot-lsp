# Test Fixtures

## Stage

Stage 04 — Robot Framework Model

## Robot Files

### basic_suite.robot

```robot
*** Settings ***
Library    Collections
Resource   resource.robot

*** Variables ***
${MESSAGE}    Hello, World!
@{ITEMS}      item1    item2    item3

*** Test Cases ***
My Test
    [Documentation]    A simple test
    [Tags]    smoke
    Given Setup Complete
    When Do Something    ${MESSAGE}
    Then Check Result    ${ITEMS}[0]

*** Keywords ***
Do Something
    [Arguments]    ${msg}
    Log    ${msg}
    Should Be Equal    ${msg}    Hello, World!
```

### syntax_error.robot

```robot
*** Settings ***
Library    Collections

*** Test Cases ***
Broken Test
    Invalid Syntax

*** Keywords ***
Keyword With Error
    [Arguments
    Log    missing bracket
```

## Purpose

- `basic_suite.robot`: standard full parser test
- `syntax_error.robot`: teste de diagnostics
- `resource.robot`: teste de imports e workspace
- `group_rf72.robot`: teste de feature detection (RF 7.2+)
