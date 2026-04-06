Feature: FOB-AGENTS-EDIT_AGENT-1 Edit Agent
  As a methodology author (Maria)
  I want to edit agent details
  So that I can update agent capabilities and guidelines

  Status: ✅ DONE - GUI CRUD implemented
  Branch: feature/skill-capability-metadata (merged to main)
  Related: act-13-mcp/interact-with-agents-via-mcp

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has agent "Cautious Developer (drdobbs-v2)"

  Scenario: AGENT-EDIT-01 Open edit form
    Given Maria is viewing the agent
    When she clicks [Edit Agent]
    Then she is redirected to FOB-AGENTS-EDIT_AGENT-1
    And all fields are pre-populated

  Scenario: AGENT-EDIT-02 Edit agent name
    Given Maria is on the edit form
    When she changes Name to "Cautious Developer v2 (drdobbs-v2)"
    And she clicks [Save Changes]
    Then the agent is updated

  Scenario: AGENT-EDIT-03 Edit agent description
    Given Maria is on the edit form
    When she updates the Description
    And she saves
    Then the description is updated

  Scenario: AGENT-EDIT-04 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then changes are discarded
