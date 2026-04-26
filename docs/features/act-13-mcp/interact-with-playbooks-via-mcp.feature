Feature: FOB-MCP-PLAYBOOKS-1 AI Assistant Interacts with Playbooks via MCP
  As an AI assistant (Cascade)
  I want to create, read, update, and delete playbooks via MCP tools
  So that I can help users build and refine methodologies through conversation

  Status: ✅ DONE - Core CRUD operations implemented
  Branch: feature/mcp-integration
  Related: act-2-playbooks
  Tests: 250 passed (100% pass rate)
  Commit: c049341

  Background:
    Given MCP server is running with command "python manage.py mcp_server --user=maria"
    And user context is set for "maria"
    And Cascade is connected via stdio protocol
  # ============================================================================
  # CREATE PLAYBOOK
  # ============================================================================

  Scenario: ✅ MCP-PLAYBOOKS-CREATE_PLAYBOOK
    Given Cascade receives user request "Help me create a React component development methodology"
    When Cascade calls MCP tool "create_playbook" with:
      | name        | React Component Development                           |
      | description | Best practices for building reusable React components |
      | category    | frontend                                              |
    Then MCP returns success response with:
      | id      |                           1 |
      | name    | React Component Development |
      | version |                         0.1 |
      | status  | draft                       |
    And playbook is saved in database with author "maria"
    And playbook has initial version "0.1"

  Scenario: ✅ MCP-PLAYBOOKS-CREATE_PLAYBOOK-1 Duplicate name raises error
    Given draft playbook "React Component Development" exists for user "maria"
    When Cascade calls MCP tool "create_playbook" with:
      | name        | React Component Development |
      | description | Different description       |
      | category    | frontend                    |
    Then MCP returns error "ValueError: Playbook 'React Component Development' already exists"
    And no new playbook is created

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-CREATE_PLAYBOOK-2 Empty name raises error
    When Cascade calls MCP tool "create_playbook" with:
      | name        |           |
      | description | Test desc |
      | category    | test      |
    Then MCP returns error "ValueError: Playbook name cannot be empty"
  # ============================================================================
  # LIST PLAYBOOKS
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-LIST+FIND
    Given user "maria" has 3 playbooks:
      | name            | status   | version |
      | React Dev       | draft    |     0.3 |
      | UX Research     | released |     1.0 |
      | Design Patterns | draft    |     0.1 |
    When Cascade calls MCP tool "list_playbooks" with:
      | status | all |
    Then MCP returns list of 3 playbooks
    And each playbook includes: id, name, description, category, status, version

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-LIST+FIND-1 Filter by draft status
    Given user "maria" has playbooks with different statuses
    When Cascade calls MCP tool "list_playbooks" with:
      | status | draft |
    Then MCP returns only playbooks with status "draft"
    And released playbooks are excluded

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-LIST+FIND-2 Filter by released status
    Given user "maria" has playbooks with different statuses
    When Cascade calls MCP tool "list_playbooks" with:
      | status | released |
    Then MCP returns only playbooks with status "released"
    And draft playbooks are excluded
  # ============================================================================
  # GET PLAYBOOK DETAIL
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-GET_PLAYBOOK
    Given draft playbook "React Dev" (id=1) exists with 2 workflows:
      | name         | description      | order |
      | Design Phase | Component design |     1 |
      | Build Phase  | Implementation   |     2 |
    When Cascade calls MCP tool "get_playbook" with:
      | playbook_id | 1 |
    Then MCP returns playbook details including:
      | id        |                      1 |
      | name      | React Dev              |
      | status    | draft                  |
      | version   |                    0.1 |
      | workflows | [array of 2 workflows] |
    And workflows array contains workflow names "Design Phase" and "Build Phase"

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-GET_PLAYBOOK-1 Non-existent playbook raises error
    When Cascade calls MCP tool "get_playbook" with:
      | playbook_id | 999 |
    Then MCP returns error "ValueError: Playbook 999 not found"

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-GET_PLAYBOOK-2 Wrong user raises error
    Given playbook id=1 is owned by user "alice"
    And current user context is "maria"
    When Cascade calls MCP tool "get_playbook" with:
      | playbook_id | 1 |
    Then MCP returns error "ValueError: Playbook 1 not found"
  # ============================================================================
  # UPDATE PLAYBOOK (DRAFT ONLY)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK
    Given draft playbook "Old Name" (id=1, version=0.1) exists
    When Cascade calls MCP tool "update_playbook" with:
      | playbook_id |        1 |
      | name        | New Name |
    Then MCP returns success with updated playbook:
      | id      |        1 |
      | name    | New Name |
      | version |      0.2 |
    And playbook version is auto-incremented from "0.1" to "0.2"
    And updated_at timestamp is updated

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK-1 Update description
    Given draft playbook (id=1, version=0.2) exists
    When Cascade calls MCP tool "update_playbook" with:
      | playbook_id |                      1 |
      | description | Updated best practices |
    Then playbook description is updated
    And version is incremented to "0.3"

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK-2 Update category
    Given draft playbook (id=1, version=0.1) exists
    When Cascade calls MCP tool "update_playbook" with:
      | playbook_id |       1 |
      | category    | backend |
    Then playbook category is updated to "backend"
    And version is incremented to "0.2"

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK-3 Released playbook raises error
    Given released playbook (id=1, status=released, version=1.0) exists
    When Cascade calls MCP tool "update_playbook" with:
      | playbook_id |        1 |
      | name        | New Name |
    Then MCP returns error "PermissionError: Cannot modify released playbook \"[name]\". Use create_pip instead."
    And playbook is not modified
    And version remains "1.0"

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK-4 Duplicate name raises error
    Given draft playbooks exist:
      | id | name      | version |
      |  1 | React Dev |     0.1 |
      |  2 | UX Flow   |     0.1 |
    When Cascade calls MCP tool "update_playbook" with:
      | playbook_id |         2 |
      | name        | React Dev |
    Then MCP returns error "ValueError: Playbook 'React Dev' already exists"
    And playbook id=2 is not modified
  # ============================================================================
  # DELETE PLAYBOOK (DRAFT ONLY)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-DELETE_PLAYBOOK
    Given draft playbook (id=1) exists with:
      | workflows  | 2 |
      | activities | 5 |
    When Cascade calls MCP tool "delete_playbook" with:
      | playbook_id | 1 |
    Then MCP returns success:
      | deleted     | true |
      | playbook_id |    1 |
    And playbook is removed from database
    And all 2 workflows are deleted (cascade)
    And all 5 activities are deleted (cascade)

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-DELETE_PLAYBOOK-1 Released playbook raises error
    Given released playbook (id=1, status=released) exists
    When Cascade calls MCP tool "delete_playbook" with:
      | playbook_id | 1 |
    Then MCP returns error "PermissionError: Cannot delete released playbook \"[name]\""
    And playbook is not deleted

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-DELETE_PLAYBOOK-2 Non-existent playbook raises error
    When Cascade calls MCP tool "delete_playbook" with:
      | playbook_id | 999 |
    Then MCP returns error "ValueError: Playbook 999 not found"
  # ============================================================================
  # ITERATIVE REFINEMENT
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-PLAYBOOKS-UPDATE_PLAYBOOK-5 Iterative refinement
    Given Cascade created draft playbook (id=1, version=0.1)
    When user says "Actually, change the name to 'Advanced React Patterns'"
    And Cascade calls "update_playbook" with new name
    Then playbook version increments to "0.2"
    When user says "Add more detail to the description"
    And Cascade calls "update_playbook" with enhanced description
    Then playbook version increments to "0.3"
    And all changes are tracked with version history
