Feature: FOB-MCP-AGENTS-1 AI Assistant Interacts with Agents via MCP
  As an AI assistant (Cascade)
  I want to create, read, update, delete, link and unlink agents via MCP tools
  So that I can help users manage AI assistant definitions within playbooks

  Status: ✅ DONE - CRUD + link/unlink operations implemented
  Branch: feature/skill-capability-metadata
  Related: act-7-agents

  Background:
    Given MCP server is running with command "python manage.py mcp_server --user=maria"
    And user context is set for "maria"
    And Cascade is connected via stdio protocol

  # ============================================================================
  # CREATE AGENT
  # ============================================================================

  Scenario: MCP-AG-01 Create agent in draft playbook
    Given draft playbook "React Frontend v1.2" exists for user "maria"
    When Cascade calls MCP tool "create_agent" with:
      | playbook_id | 1                                   |
      | name        | Code Reviewer                       |
      | description | Reviews PRs and suggests improvements |
    Then MCP returns success response with:
      | id          | 1             |
      | name        | Code Reviewer |
    And parent playbook version is incremented

  Scenario: MCP-AG-02 Create agent with empty name raises error
    Given draft playbook "React Frontend v1.2" exists for user "maria"
    When Cascade calls MCP tool "create_agent" with:
      | playbook_id | 1 |
      | name        |   |
    Then MCP returns error "ValueError: Agent name cannot be empty"

  Scenario: MCP-AG-03 Create agent in released playbook raises error
    Given released playbook "Production Guide" exists for user "maria"
    When Cascade calls MCP tool "create_agent" with:
      | playbook_id | 2             |
      | name        | Code Reviewer |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # LIST AGENTS
  # ============================================================================

  Scenario: MCP-AG-04 List agents for playbook
    Given draft playbook with 3 agents exists for user "maria"
    When Cascade calls MCP tool "list_agents" with:
      | playbook_id | 1 |
    Then MCP returns list of 3 agents with name, description, activity_count

  Scenario: MCP-AG-05 List agents with search query
    Given draft playbook with agents "Code Reviewer" and "Test Generator"
    When Cascade calls MCP tool "list_agents" with:
      | playbook_id | 1        |
      | search      | Reviewer |
    Then MCP returns only agents matching "Reviewer" in name or description

  # ============================================================================
  # GET AGENT
  # ============================================================================

  Scenario: MCP-AG-06 Get agent details with activity count
    Given draft playbook with agent "Code Reviewer" linked to 2 activities
    When Cascade calls MCP tool "get_agent" with:
      | agent_id | 1 |
    Then MCP returns agent details including:
      | name           | Code Reviewer |
      | activity_count | 2             |

  # ============================================================================
  # UPDATE AGENT
  # ============================================================================

  Scenario: MCP-AG-07 Update agent name and description
    Given draft playbook with agent "Code Reviewer" for user "maria"
    When Cascade calls MCP tool "update_agent" with:
      | agent_id    | 1                |
      | name        | Senior Reviewer  |
      | description | Updated desc     |
    Then MCP returns updated agent with new values
    And parent playbook version is incremented

  Scenario: MCP-AG-08 Update agent in released playbook raises error
    Given released playbook with agent "Code Reviewer" for user "maria"
    When Cascade calls MCP tool "update_agent" with:
      | agent_id | 1               |
      | name     | Senior Reviewer |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # DELETE AGENT
  # ============================================================================

  Scenario: MCP-AG-09 Delete agent clears activity FKs
    Given draft playbook with agent "Code Reviewer" linked to 2 activities
    When Cascade calls MCP tool "delete_agent" with:
      | agent_id | 1 |
    Then MCP returns success with deleted=True
    And parent playbook version is incremented
    And the 2 activities have agent FK set to NULL

  Scenario: MCP-AG-10 Delete agent in released playbook raises error
    Given released playbook with agent "Code Reviewer" for user "maria"
    When Cascade calls MCP tool "delete_agent" with:
      | agent_id | 1 |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # LINK / UNLINK
  # ============================================================================

  Scenario: MCP-AG-11 Link agent to activity in same playbook
    Given draft playbook with agent "Code Reviewer" and activity "Review Code"
    When Cascade calls MCP tool "link_agent_to_activity" with:
      | activity_id | 1 |
      | agent_id    | 1 |
    Then MCP returns success and activity.agent_id is set

  Scenario: MCP-AG-12 Link agent to activity in different playbook raises error
    Given draft playbook A with agent "Code Reviewer"
    And draft playbook B with activity "Review Code"
    When Cascade calls MCP tool "link_agent_to_activity" with:
      | activity_id | 2 |
      | agent_id    | 1 |
    Then MCP returns error "ValueError: must be in the same playbook"

  Scenario: MCP-AG-13 Unlink agent from activity
    Given draft playbook with activity linked to agent "Code Reviewer"
    When Cascade calls MCP tool "unlink_agent_from_activity" with:
      | activity_id | 1 |
    Then MCP returns success and activity.agent_id is NULL
