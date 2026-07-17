Feature: FOB-MCP-1 MCP Integration and Tools
  As a methodology author (Maria)
  I want to use MCP tools with playbooks
  So that I can enhance methodology with AI assistance

  Status: 🔮 FUTURE - GUI integration not yet implemented (MCP tools work via Windsurf only)

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

  # ---------------------------------------------------------------------------
  # FOB-MCP-VH — Playbook version history via get_playbook
  # ---------------------------------------------------------------------------

  Scenario: FOB-MCP-VH-01 View playbook version history
    Given a released playbook with at least two accepted PIPs
    When an MCP agent calls get_playbook with include_history=True
    Then the response includes the current playbook fields
    And a "versions" list is returned with one entry per recorded version
    And each entry contains version_number, source, pip_id, change_summary, created_at, and is_major

  Scenario: FOB-MCP-VH-02 Retrieve playbook snapshot at a specific version
    Given a released playbook that has a version "1.0" recorded
    When an MCP agent calls get_playbook with version="1.0"
    Then the response contains the snapshot_data recorded at version 1.0
    And the snapshot includes the playbook structure as it was at that version

  Scenario: FOB-MCP-VH-03 Unknown version returns error
    Given a playbook with versions 1.0 and 2.0
    When an MCP agent calls get_playbook with version="99.9"
    Then the response is an error indicating version 99.9 was not found
