Feature: FOB-AGENTS-LIST+FIND-1 Agents List and Search
  As a methodology author (Maria)
  I want to view and search agents within a playbook
  So that I can manage AI assistants that perform activities

  Status: ✅ DONE - GUI CRUD implemented
  Branch: feature/skill-capability-metadata (merged to main)
  Related: act-13-mcp/interact-with-agents-via-mcp

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend v1.2"
    And the playbook has 8 agents defined

  Scenario: AGENT-LIST-01 Navigate to agents list from playbook
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    When she clicks the "Agents" tab
    Then she is redirected to FOB-AGENTS-LIST+FIND-1
    And she sees "Agents in React Frontend v1.2" header

  Scenario: AGENT-LIST-02 View agents table
    Given Maria is on agents list
    Then she sees all 8 agents
    And each agent shows: Name, Description, Activities, Actions

  Scenario: AGENT-LIST-03 Create new agent
    Given Maria is on agents list
    When she clicks [Create New Agent]
    Then she is redirected to FOB-AGENTS-CREATE_AGENT-1

  Scenario: AGENT-LIST-04 Search agents by name
    Given Maria is on agents list
    When she enters "Developer" in search
    Then only agents matching "Developer" are shown

  Scenario: AGENT-LIST-05 Filter by activity usage
    Given some agents are used in activities
    When she filters by "Used in Activities"
    Then only agents assigned to activities are shown

  Scenario: AGENT-LIST-06 View agent usage count
    Given Maria is on agents list
    Then each agent shows activity count
    And she can click to see which activities use each agent

  Scenario: AGENT-LIST-07 Navigate to view agent
    Given Maria is on agents list
    When she clicks [View] for an agent
    Then she is redirected to FOB-AGENTS-VIEW_AGENT-1

  Scenario: AGENT-LIST-08 Empty state display
    Given the playbook has zero agents
    Then she sees "No agents yet"
    And she sees [Create First Agent] button
