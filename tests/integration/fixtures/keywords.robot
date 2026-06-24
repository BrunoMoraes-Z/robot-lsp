*** Keywords ***
Keyword With Args
    [Arguments]    ${required}    ${optional}=default    @{items}    &{options}
    [Documentation]    Keyword docs
    Log    ${required}
    Log    ${optional}
