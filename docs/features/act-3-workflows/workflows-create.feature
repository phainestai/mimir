Feature: FOB-WORKFLOWS-CREATE_WORKFLOW-1 Create Workflow
  As a methodology author (Maria)
  I want to create workflows within a playbook
  So that I can organize activities into execution sequences

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend Development v1.2"
    And she is on the workflows list page

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-01 Open create workflow form
    Given Maria is on FOB-WORKFLOWS-LIST+FIND-1
    When she clicks [Create New Workflow]
    Then she is redirected to FOB-WORKFLOWS-CREATE_WORKFLOW-1
    And she sees the workflow creation form
    And the Parent Playbook field shows "React Frontend Development v1.2" (read-only)

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-02 Create workflow with required fields
    Given Maria is on the create workflow form
    When she enters "Design System Integration" in Name
    And she enters "Integrate design tokens and component library into the React application" in Description
    And she clicks [Create Workflow]
    Then the workflow is created successfully
    And she sees success notification "Workflow 'Design System Integration' created in React Frontend Development"
    And she is redirected to FOB-WORKFLOWS-VIEW_WORKFLOW-1

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-03 Validate required fields
    Given Maria is on the create workflow form
    When she leaves Name empty
    And she clicks [Create Workflow]
    Then she sees validation error "Name is required (3-100 characters)"
    And the Name field is highlighted

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-04 Duplicate name validation
    Given a workflow named "Component Development" already exists in the playbook
    When she enters "Component Development" in Name
    And she fills other required fields
    And she clicks [Create Workflow]
    Then she sees error "A workflow with this name already exists in this playbook"

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-05 Set workflow order to end (default)
    Given the playbook has 3 existing workflows
    When she checks "Add to end" checkbox (default)
    And she creates the workflow
    Then the workflow is added as order #4

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-06 Set specific workflow order
    Given the playbook has 3 existing workflows
    When she unchecks "Add to end"
    And she enters "2" in Order/Sequence field
    And she creates the workflow
    Then the workflow is inserted at position 2
    And existing workflows are reordered accordingly

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-07 Select no phases organization
    Given Maria is on the create workflow form
    When she selects "No phases (Activities directly in workflow)"
    And she creates the workflow
    Then the workflow is created without phase organization
    And activities will be added directly to the workflow

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-08 Select use phases organization
    Given Maria is on the create workflow form
    When she selects "Use phases (Group activities into phases)"
    Then she sees tooltip "Phases are optional. Use them to organize activities into logical groups or stages."
    When she creates the workflow
    Then the workflow is created with phase support enabled
    And she can add phases in the edit view

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-09 Add first activity during creation
    Given Maria is on the create workflow form
    When she checks "Add first activity now?" checkbox
    Then quick activity creation fields appear
    And she sees fields: Activity Name, Activity Description
    When she enters "Setup design tokens" in Activity Name
    And she creates the workflow
    Then the workflow is created with one activity

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-10 Skip adding activities
    Given Maria is on the create workflow form
    When she clicks [Skip - Add Activities Later]
    Then no activity fields are shown
    When she creates the workflow
    Then the workflow is created with zero activities

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-11 Cancel workflow creation
    Given Maria is on the create workflow form
    And she has entered some data
    When she clicks [Cancel]
    Then she sees confirmation "Discard changes?"
    When she confirms
    Then the form closes
    And she returns to FOB-WORKFLOWS-LIST+FIND-1
    And no workflow is created

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-12 Workflow appears in list after creation
    Given Maria has created workflow "Design System Integration"
    When she navigates to FOB-WORKFLOWS-LIST+FIND-1
    Then she sees "Design System Integration" in the workflows table
    And it shows correct order, activity count, and phase status

  Scenario: FOB-WORKFLOWS-CREATE_WORKFLOW-13 Parent playbook is scoped correctly
    Given Maria is viewing playbook "UX Research Methodology"
    When she creates a workflow
    Then the workflow belongs to "UX Research Methodology" only
    And it does not appear in other playbooks' workflow lists

  Scenario Outline: FOB-WORKFLOWS-CREATE_WORKFLOW-14 Validate field lengths
    Given Maria is on the create workflow form
    When she enters "<value>" in "<field>"
    And she clicks [Create Workflow]
    Then she sees validation error "<error>"

    Examples:
      | field       | value       | error                                      |
      | Name        | AB          | Name must be at least 3 characters         |
      | Name        | [101 chars] | Name must not exceed 100 characters        |
      | Description | Short       | Description must be at least 10 characters |
      | Description | [501 chars] | Description must not exceed 500 characters |
