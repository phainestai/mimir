Feature: FOB-MCP-ACTIVITIES-1 AI Assistant Interacts with Activities via MCP
  As an AI assistant (Cascade)
  I want to create, read, update, and delete activities via MCP tools
  So that I can help users define detailed methodology steps with dependencies

  Status: ✅ DONE - All 6 CRUD tools implemented
  Branch: feature/mcp-integration (merged to main)
  Related: act-5-activities
  Tests: 250 passed (100% pass rate)
  Commit: 0969327

  Background:
    Given MCP server is running for user "maria"
    And user context is set for "maria"
    And Cascade is connected via stdio
  # ============================================================================
  # CREATE ACTIVITY (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY
    Given draft playbook (id=1, version=0.2) has workflow (id=1)
    And playbook has phase (id=3, name="Planning")
    When Cascade calls MCP tool "create_activity" with:
      | workflow_id |                                       1 |
      | name        | Define Props Interface                  |
      | guidance    | Document component props and prop types |
      | phase_id    |                                       3 |
    Then MCP returns success with activity:
      | id          |                      1 |
      | name        | Define Props Interface |
      | order       |                      1 |
      | workflow_id |                      1 |
      | phase_id    |                      3 |
    And grandparent playbook version is incremented from "0.2" to "0.3"
    And activity is assigned auto-incremented order number

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY-1 Create with predecessor
    Given workflow (id=1) has activity "Define Props" (id=1)
    And grandparent playbook version is "0.3"
    When Cascade calls "create_activity" with:
      | workflow_id    |              1 |
      | name           | Create Mockup  |
      | guidance       | Design visuals |
      | predecessor_id |              1 |
    Then activity is created with predecessor linked to activity id=1
    And grandparent playbook version increments to "0.4"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY-2 Released playbook raises error
    Given released playbook (id=1, status=released) has workflow (id=1)
    When Cascade calls "create_activity" with:
      | workflow_id |            1 |
      | name        | New Activity |
      | guidance    | Test         |
    Then MCP returns error "PermissionError: Cannot modify released playbook \"[name]\". Use create_pip instead."
    And no activity is created

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY-3 Predecessor in different workflow raises error
    Given workflow (id=1) has activity (id=1)
    And workflow (id=2) exists in same playbook
    When Cascade calls "create_activity" with:
      | workflow_id    |    2 |
      | name           | Test |
      | guidance       | Test |
      | predecessor_id |    1 |
    Then MCP returns error "ValueError: Predecessor activity 1 not found in workflow"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY-4 Duplicate name raises error
    Given workflow (id=1) has activity "Define Props"
    When Cascade calls "create_activity" with:
      | workflow_id |            1 |
      | name        | Define Props |
      | guidance    | Duplicate    |
    Then MCP returns error "ValueError: Activity with name 'Define Props' already exists in this workflow"
  # ============================================================================
  # LIST ACTIVITIES
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-LIST+FIND
    Given workflow (id=1) has 3 activities:
      | name            | order | predecessor_id | successor_id |
      | Define Props    |     1 | null           |            2 |
      | Create Mockup   |     2 |              1 |            3 |
      | Write Component |     3 |              2 | null         |
    When Cascade calls "list_activities" with:
      | workflow_id | 1 |
    Then MCP returns list of 3 activities ordered by order number
    And each activity includes: id, name, guidance, phase, order, workflow_id, predecessor_id, successor_id

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-LIST+FIND-1 Non-existent workflow raises error
    When Cascade calls "list_activities" with:
      | workflow_id | 999 |
    Then MCP returns error "ValueError: Workflow 999 not found"
  # ============================================================================
  # GET ACTIVITY DETAIL
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-GET_ACTIVITY
    Given activity (id=2) has:
      | predecessor | Activity id=1, name="Define Props"    |
      | successor   | Activity id=3, name="Write Component" |
    When Cascade calls "get_activity" with:
      | activity_id | 2 |
    Then MCP returns activity details including:
      | id          |                                2 |
      | name        | Create Mockup                    |
      | predecessor | {id: 1, name: "Define Props"}    |
      | successor   | {id: 3, name: "Write Component"} |

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-GET_ACTIVITY-2 Rules array
    Given activity (id=2) links playbook rules "pytest-first" and "ruff-format"
    When Cascade calls "get_activity" with:
      | activity_id | 2 |
    Then MCP returns field "rules" as a list of rule objects with id title slug always_apply

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-GET_ACTIVITY-1 Non-existent activity raises error
    When Cascade calls "get_activity" with:
      | activity_id | 999 |
    Then MCP returns error "ValueError: Activity 999 not found"
  # ============================================================================
  # UPDATE ACTIVITY (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY
    Given draft playbook (id=1, version=0.5) has workflow with activity (id=1, name="Old Name")
    When Cascade calls "update_activity" with:
      | activity_id |        1 |
      | name        | New Name |
    Then activity name is updated to "New Name"
    And grandparent playbook version is incremented to "0.6"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-1 Update guidance
    Given draft playbook (version=0.3) has workflow with activity (id=1)
    When Cascade calls "update_activity" with:
      | activity_id |                                   1 |
      | guidance    | ## Updated\n\nNew detailed guidance |
    Then activity guidance is updated
    And grandparent playbook version increments to "0.4"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-2 Update phase
    Given draft playbook has workflow with activity (id=1, phase="Planning")
    When Cascade calls "update_activity" with:
      | activity_id |         1 |
      | phase       | Execution |
    Then activity phase is updated to "Execution"
    And grandparent playbook version increments

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-3 Update order
    Given workflow has activities with orders 1, 2, 3
    When Cascade calls "update_activity" with:
      | activity_id | 3 |
      | order       | 1 |
    Then activity order is updated to 1
    And grandparent playbook version increments

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-4 Released playbook raises error
    Given released playbook (status=released) has workflow with activity (id=1)
    When Cascade calls "update_activity" with:
      | activity_id |        1 |
      | name        | New Name |
    Then MCP returns error "PermissionError: Cannot modify released playbook. Use create_pip instead."
    And activity is not modified
  # ============================================================================
  # DELETE ACTIVITY (IN DRAFT PLAYBOOK)
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-DELETE_ACTIVITY
    Given draft playbook (id=1, version=0.7) has workflow with activity (id=1)
    When Cascade calls "delete_activity" with:
      | activity_id | 1 |
    Then MCP returns success:
      | deleted     | true |
      | activity_id |    1 |
    And activity is removed from database
    And grandparent playbook version is incremented to "0.8"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-DELETE_ACTIVITY-1 Released playbook raises error
    Given released playbook (status=released) has workflow with activity (id=1)
    When Cascade calls "delete_activity" with:
      | activity_id | 1 |
    Then MCP returns error "PermissionError: Cannot modify released playbook. Use create_pip instead."
    And activity is not deleted

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-DELETE_ACTIVITY-2 Non-existent activity raises error
    When Cascade calls "delete_activity" with:
      | activity_id | 999 |
    Then MCP returns error "ValueError: Activity 999 not found"
  # ============================================================================
  # DEPENDENCY MANAGEMENT
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-5 Set predecessor
    Given draft playbook (version=0.5) has workflow with activities:
      | id | name          | order |
      |  1 | Define Props  |     1 |
      |  2 | Create Mockup |     2 |
    When Cascade calls "set_activity_predecessor" with:
      | activity_id    | 2 |
      | predecessor_id | 1 |
    Then activity id=2 has predecessor id=1
    And activity id=1 has successor id=2
    And grandparent playbook version increments to "0.6"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-6 Circular dependency raises error
    Given workflow has activities with chain: 1 → 2 → 3
    When Cascade calls "set_activity_predecessor" with:
      | activity_id    | 1 |
      | predecessor_id | 3 |
    Then MCP returns error "ValueError: Circular dependency detected"
    And no dependency is created

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-7 Predecessor in different workflow raises error
    Given workflow (id=1) has activity (id=1)
    And workflow (id=2) has activity (id=2)
    When Cascade calls "set_activity_predecessor" with:
      | activity_id    | 2 |
      | predecessor_id | 1 |
    Then MCP returns error "ValueError: Activity or predecessor not found"

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-UPDATE_ACTIVITY-8 Set predecessor in released playbook raises error
    Given released playbook has workflow with activities (id=1, id=2)
    When Cascade calls "set_activity_predecessor" with:
      | activity_id    | 2 |
      | predecessor_id | 1 |
    Then MCP returns error "PermissionError: Cannot modify released playbook. Use create_pip instead."
  # ============================================================================
  # END-TO-END WORKFLOW
  # ============================================================================

  Scenario: FOB-MCP-CONFIG-ACTIVITIES-CREATE_ACTIVITY-5 Build complete methodology with dependencies
    Given user requests "Create React methodology with component workflow"
    When Cascade creates playbook (version=0.1)
    And Cascade creates workflow "Component Development" (version=0.2)
    And Cascade creates activity "Define Props" (version=0.3)
    And Cascade creates activity "Create Mockup" (version=0.4)
    And Cascade creates activity "Write Component" (version=0.5)
    And Cascade creates activity "Write Tests" (version=0.6)
    And Cascade sets "Create Mockup" predecessor to "Define Props" (version=0.7)
    And Cascade sets "Write Component" predecessor to "Create Mockup" (version=0.8)
    And Cascade sets "Write Tests" predecessor to "Write Component" (version=0.9)
    Then playbook has dependency chain: Define Props → Create Mockup → Write Component → Write Tests
    And final playbook version is "0.9"
    And dependency graph has no circular dependencies

  Scenario: FOB-MCP-CONFIG-ACT-23 AI refines activity guidance iteratively
    Given draft playbook has workflow with activity "Define Props" (version=0.3)
    When user says "Add more detail about TypeScript types"
    And Cascade updates activity guidance with TypeScript examples (version=0.4)
    And user says "Also mention PropTypes for non-TS projects"
    And Cascade updates activity guidance again (version=0.5)
    Then activity guidance includes both TypeScript and PropTypes examples
    And all version increments are tracked
