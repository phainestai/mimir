Feature: FOB-MCP-1 MCP Integration and Tools
  As a methodology author (Maria)
  I want to use MCP tools with playbooks
  So that I can enhance methodology with AI assistance

  Background:
    Given Maria is authenticated in FOB
    And she has MCP server configured

  Scenario: FOB-MCP-CONFIG-01 Configure MCP connection
    Given Maria is in settings
    When she navigates to MCP Configuration
    And she enters server URL and credentials
    Then MCP connection is established

  Scenario: FOB-MCP-CONFIG-02 Use MCP tool on activity
    Given Maria is viewing an activity
    When she clicks [Use MCP Tool]
    Then she sees available MCP tools
    And she can select and execute a tool

  Scenario: FOB-MCP-CONFIG-03 AI-generated content
    Given Maria creates a new activity
    When she clicks [Generate with AI]
    Then MCP suggests activity details
    And she can accept or modify suggestions

  Scenario: FOB-MCP-CONFIG-04 MCP tool results
    Given Maria executes an MCP tool
    Then she sees tool output
    And she can save output to activity/artifact

  Scenario: FOB-MCP-CONFIG-05 MCP history
    Given Maria used MCP tools
    When she views MCP History
    Then she sees all tool executions with results

  Scenario: FOB-MCP-CONFIG-06 Disconnect MCP
    Given MCP is connected
    When Maria disables MCP
    Then connection is terminated
    And MCP features are hidden
