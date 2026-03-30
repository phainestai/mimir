Feature: FOB-AGENTS-DELETE_AGENT-1 Delete Agent
  As a methodology author (Maria)
  I want to delete agents
  So that I can remove obsolete AI assistant definitions

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has agent "Old Agent"

  Scenario: AGENT-DELETE-01 Open delete confirmation
    Given Maria is on agents list
    When she clicks [Delete] for "Old Agent"
    Then the FOB-AGENTS-DELETE_AGENT-1 modal appears
    And it shows "Delete Agent?"

  Scenario: AGENT-DELETE-02 Modal shows agent details
    Given the delete modal is open
    Then it displays agent name
    And it shows warning about activity assignments

  Scenario: AGENT-DELETE-03 Warning about assigned activities
    Given the agent is assigned to 4 activities
    Then the modal shows "Used in 4 activities"
    And it lists the activities
    And it shows "Agent assignments will be removed"

  Scenario: AGENT-DELETE-04 Confirm deletion
    Given the delete modal is open
    When she clicks [Delete Agent]
    Then the agent is deleted
    And activity assignments are removed
    And she sees success notification

  Scenario: AGENT-DELETE-05 Cancel deletion
    Given the delete modal is open
    When she clicks [Cancel]
    Then the modal closes
    And the agent is not deleted
