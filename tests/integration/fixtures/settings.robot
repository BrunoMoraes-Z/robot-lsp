*** Settings ***
Suite Setup       Log    suite setup
Suite Teardown    Log    suite teardown
Test Setup        Log    test setup
Test Teardown     Log    test teardown
Test Template     Template Keyword
Test Timeout      10 seconds
Force Tags        force-a    force-b
Default Tags      default-a    default-b
