Feature: FOB-AGENTS-CREATE_AGENT-1 Create Agent
  As a methodology author (Maria)
  I want to create agents within a playbook
  So that I can define AI assistants that perform activities

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend v1.2"

  Scenario: AGENT-CREATE-01 Open create agent form
    Given Maria is on agents list
    When she clicks [Create New Agent]
    Then she is redirected to FOB-AGENTS-CREATE_AGENT-1

  Scenario: AGENT-CREATE-02 Create agent successfully
    Given Maria is on the create agent form
    When she enters "Cautious Developer (drdobbs-v2)" in Name
    And she enters "AI agent with defensive programming and test-first principles" in Description
    And she clicks [Create Agent]
    Then the agent is created
    And she sees success notification

  Scenario: AGENT-CREATE-03 Validate required fields
    Given Maria is on the create agent form
    When she leaves Name empty
    And she clicks [Create Agent]
    Then she sees validation error "Name is required"

  Scenario: AGENT-CREATE-04 Cancel agent creation
    Given Maria has entered agent data
    When she clicks [Cancel]
    Then she sees "Discard changes?" confirmation
    When she confirms
    Then no agent is created
