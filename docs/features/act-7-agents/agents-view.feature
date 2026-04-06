Feature: FOB-AGENTS-VIEW_AGENT-1 View Agent Details
  As a methodology author (Maria)
  I want to view agent details
  So that I can understand agent capabilities and guidelines

  Status: ✅ DONE - GUI CRUD implemented
  Branch: feature/skill-capability-metadata (merged to main)
  Related: act-13-mcp/interact-with-agents-via-mcp

  Background:
    Given Maria is authenticated in FOB
    And she is viewing agent "Cautious Developer (drdobbs-v2)"
    And the agent belongs to playbook "React Frontend v1.2"

  Scenario: AGENT-VIEW-01 Open agent detail page
    Given Maria is on agents list
    When she clicks [View] for "Cautious Developer (drdobbs-v2)"
    Then she is redirected to FOB-AGENTS-VIEW_AGENT-1
    And she sees breadcrumb with playbook and agent name

  Scenario: AGENT-VIEW-02 View agent header
    Given Maria is on the agent detail page
    Then she sees agent name "Cautious Developer (drdobbs-v2)"
    And she sees parent playbook badge

  Scenario: AGENT-VIEW-03 View agent description
    Given Maria is on the agent detail page
    Then she sees the full description
    And she sees creation and modification timestamps

  Scenario: AGENT-VIEW-04 View activities using this agent
    Given the agent is assigned to 5 activities
    Then she sees "Used in Activities" section
    And she sees list of activities with this agent
    And each activity link is clickable

  Scenario: AGENT-VIEW-05 Edit agent button
    Given Maria is viewing the agent
    When she clicks [Edit Agent]
    Then she is redirected to FOB-AGENTS-EDIT_AGENT-1

  Scenario: AGENT-VIEW-06 Delete agent button
    Given Maria is viewing the agent
    When she clicks [Delete Agent]
    Then the FOB-AGENTS-DELETE_AGENT-1 modal appears
