Feature: FOB-MCP-WORKFLOWS-1 AI Assistant Interacts with Workflows via MCP
  As an AI assistant (Cascade)
  I want to create, read, update, and delete workflows via MCP tools
  So that I can help users structure their methodologies

  Status: ✅ DONE - All 5 CRUD tools implemented
  Branch: feature/mcp-integration (merged to main)
  Related: act-3-workflows
  Tests: 250 passed (100% pass rate)
  Commit: 0969327

  Background:
    Given MCP server is running for user "maria"
    And user context is set for "maria"
    And Cascade is connected via stdio
  # ============================================================================
  # CREATE WORKFLOW (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW
    Given draft playbook "React Dev" (id=1, version=0.1) exists
    When Cascade calls MCP tool "create_workflow" with:
      | playbook_id |                                   1 |
      | name        | Design Phase                        |
      | description | Component architecture and planning |
    Then MCP returns success with workflow:
      | id          |            1 |
      | name        | Design Phase |
      | order       |            1 |
      | playbook_id |            1 |
    And parent playbook version is incremented from "0.1" to "0.2"
    And workflow is assigned auto-incremented order number

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW-1 Second workflow gets order=2
    Given draft playbook (id=1) has 1 workflow with order=1
    When Cascade calls "create_workflow" with:
      | playbook_id |              1 |
      | name        | Build Phase    |
      | description | Implementation |
    Then workflow is created with order=2
    And parent playbook version increments to "0.3"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW-2 Released playbook raises error
    Given released playbook (id=1, status=released, version=1.0) exists
    When Cascade calls "create_workflow" with:
      | playbook_id |            1 |
      | name        | New Workflow |
      | description | Test         |
    Then MCP returns error "PermissionError: Cannot modify released playbook \"[name]\". Use create_pip instead."
    And no workflow is created
    And playbook version remains "1.0"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW-3 Duplicate name raises error
    Given draft playbook (id=1) has workflow "Design Phase"
    When Cascade calls "create_workflow" with:
      | playbook_id |            1 |
      | name        | Design Phase |
      | description | Duplicate    |
    Then MCP returns error "ValueError: Workflow 'Design Phase' already exists in this playbook"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW-4 Non-existent playbook raises error
    When Cascade calls "create_workflow" with:
      | playbook_id |       999 |
      | name        | Test      |
      | description | Test desc |
    Then MCP returns error "ValueError: Playbook 999 not found"
  # ============================================================================
  # LIST WORKFLOWS
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-LIST+FIND
    Given draft playbook (id=1) has 3 workflows:
      | name         | description       | order |
      | Design Phase | Planning          |     1 |
      | Build Phase  | Implementation    |     2 |
      | Test Phase   | Quality assurance |     3 |
    When Cascade calls "list_workflows" with:
      | playbook_id | 1 |
    Then MCP returns list of 3 workflows ordered by order number
    And each workflow includes: id, name, description, order, playbook_id

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-LIST+FIND-1 Non-existent playbook raises error
    When Cascade calls "list_workflows" with:
      | playbook_id | 999 |
    Then MCP returns error "ValueError: Playbook 999 not found"
  # ============================================================================
  # GET WORKFLOW DETAIL
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-GET_WORKFLOW
    Given workflow (id=1) exists with 3 activities:
      | name            | order |
      | Define Props    |     1 |
      | Create Mockup   |     2 |
      | Write Component |     3 |
    When Cascade calls "get_workflow" with:
      | workflow_id | 1 |
    Then MCP returns workflow details including:
      | id         |            1 |
      | name       | Design Phase |
      | activities | [array of 3] |
    And activities array contains activity names

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-GET_WORKFLOW-1 Non-existent workflow raises error
    When Cascade calls "get_workflow" with:
      | workflow_id | 999 |
    Then MCP returns error "ValueError: Workflow 999 not found"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-GET_WORKFLOW-2 Wrong user raises error
    Given workflow (id=1) belongs to playbook owned by "alice"
    And current user context is "maria"
    When Cascade calls "get_workflow" with:
      | workflow_id | 1 |
    Then MCP returns error "ValueError: Workflow 1 not found"
  # ============================================================================
  # UPDATE WORKFLOW (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-UPDATE_WORKFLOW
    Given draft playbook (id=1, version=0.2) has workflow (id=1, name="Old Name")
    When Cascade calls "update_workflow" with:
      | workflow_id |        1 |
      | name        | New Name |
    Then workflow name is updated to "New Name"
    And parent playbook version is incremented to "0.3"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-UPDATE_WORKFLOW-1 Update description
    Given draft playbook (id=1, version=0.1) has workflow (id=1)
    When Cascade calls "update_workflow" with:
      | workflow_id |                   1 |
      | description | Updated description |
    Then workflow description is updated
    And parent playbook version increments to "0.2"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-UPDATE_WORKFLOW-2 Update order
    Given draft playbook (id=1) has workflows with orders 1, 2, 3
    When Cascade calls "update_workflow" with:
      | workflow_id | 2 |
      | order       | 1 |
    Then workflow order is updated to 1
    And parent playbook version increments

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-UPDATE_WORKFLOW-3 Released playbook raises error
    Given released playbook (id=1, status=released) has workflow (id=1)
    When Cascade calls "update_workflow" with:
      | workflow_id |        1 |
      | name        | New Name |
    Then MCP returns error "PermissionError: Cannot modify released playbook \"[name]\". Use create_pip instead."
    And workflow is not modified

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-UPDATE_WORKFLOW-4 Duplicate name raises error
    Given draft playbook (id=1) has workflows:
      | id | name         |
      |  1 | Design Phase |
      |  2 | Build Phase  |
    When Cascade calls "update_workflow" with:
      | workflow_id |            2 |
      | name        | Design Phase |
    Then MCP returns error "ValueError: Workflow 'Design Phase' already exists in this playbook"
  # ============================================================================
  # DELETE WORKFLOW (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-DELETE_WORKFLOW
    Given draft playbook (id=1, version=0.5) has workflow (id=1) with 4 activities
    When Cascade calls "delete_workflow" with:
      | workflow_id | 1 |
    Then MCP returns success:
      | deleted     | true |
      | workflow_id |    1 |
    And workflow is removed from database
    And all 4 activities are deleted (cascade)
    And parent playbook version is incremented to "0.6"

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-DELETE_WORKFLOW-1 Released playbook raises error
    Given released playbook (id=1, status=released) has workflow (id=1)
    When Cascade calls "delete_workflow" with:
      | workflow_id | 1 |
    Then MCP returns error "PermissionError: Cannot modify released playbook \"[name]\". Use create_pip instead."
    And workflow is not deleted

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-DELETE_WORKFLOW-2 Non-existent workflow raises error
    When Cascade calls "delete_workflow" with:
      | workflow_id | 999 |
    Then MCP returns error "ValueError: Workflow 999 not found"
  # ============================================================================
  # END-TO-END WORKFLOW
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-WORKFLOWS-CREATE_WORKFLOW-5 Build complete methodology
    Given user requests "Create a React methodology with 3 phases"
    When Cascade creates playbook (version=0.1)
    And Cascade creates workflow "Design Phase" (version=0.2)
    And Cascade creates workflow "Build Phase" (version=0.3)
    And Cascade creates workflow "Test Phase" (version=0.4)
    Then playbook has 3 workflows in correct order
    And final playbook version is "0.4"
    And all workflows belong to same playbook
