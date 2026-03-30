Feature: FOB-WORKFLOWS-LIST+FIND-1 Workflows List and Search
  As a methodology author (Maria)
  I want to view, search, and filter workflows within a playbook
  So that I can manage execution sequences effectively

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend Development v1.2"
    And the playbook has 3 workflows:
      | name                    | activities | phases | order |
      | Component Development   |          8 |      2 |     1 |
      | State Management Setup  |          6 |      0 |     2 |
      | Testing & Documentation |         10 |      3 |     3 |

  Scenario: FOB-WORKFLOWS-LIST+FIND-01 Navigate to workflows list from playbook
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    When she clicks the "Workflows" tab
    Then she is redirected to FOB-WORKFLOWS-LIST+FIND-1
    And she sees "Workflows in React Frontend Development" header
    And the header shows workflow count "(3 workflows)"

  Scenario: FOB-WORKFLOWS-LIST+FIND-02 View workflows list layout
    Given Maria is on the workflows list page
    Then she sees breadcrumb "Playbooks > React Frontend Development > Workflows"
    And she sees Context Banner showing:
      | field   | value                      |
      | Name    | React Frontend Development |
      | Version | v1.2                       |
      | Author  | Mike Chen                  |
    And she sees all 3 workflows in the table

  Scenario: FOB-WORKFLOWS-LIST+FIND-03 Workflows table shows correct columns
    Given Maria is on the workflows list page
    Then the workflows table has columns: Name, Description, Activities, Phases, Order, Actions
    And each row has a drag handle for reordering
    And workflows are ordered by their Order field (1, 2, 3)

  Scenario: FOB-WORKFLOWS-LIST+FIND-04 View workflow row data
    Given Maria is on the workflows list page
    Then the "Component Development" row shows:
      | field      | value                 |
      | Name       | Component Development |
      | Activities |                     8 |
      | Phases     |                     2 |
      | Order      |                     1 |
    And it has row actions: View, Edit, Delete, Duplicate, More

  Scenario: FOB-WORKFLOWS-LIST+FIND-05 Create new workflow button
    Given Maria is on the workflows list page
    When she clicks [Create New Workflow] button
    Then she is redirected to FOB-WORKFLOWS-CREATE_WORKFLOW-1
    And the parent playbook is pre-set to "React Frontend Development"

  Scenario: FOB-WORKFLOWS-LIST+FIND-06 Search workflows by name
    Given Maria is on the workflows list page
    When she enters "Component" in the search box
    Then she sees only "Component Development" workflow
    And other workflows are hidden

  Scenario: FOB-WORKFLOWS-LIST+FIND-07 Filter by has phases
    Given Maria is on the workflows list page
    When she selects "Has Phases: Yes" from the filter
    Then she sees workflows with Phases > 0
    And "State Management Setup" (0 phases) is hidden
    And "Component Development" (2 phases) is visible

  Scenario: FOB-WORKFLOWS-LIST+FIND-08 Filter by activity count range
    Given Maria is on the workflows list page
    When she sets activity count filter to "5-8"
    Then she sees "Component Development" (8 activities)
    And she sees "State Management Setup" (6 activities)
    And "Testing & Documentation" (10 activities) is hidden

  Scenario: FOB-WORKFLOWS-LIST+FIND-09 Clear all filters
    Given Maria has applied filters
    When she clicks [Clear Filters]
    Then all filters are removed
    And all 3 workflows are visible

  Scenario: FOB-WORKFLOWS-LIST+FIND-10 Navigate to view workflow
    Given Maria is on the workflows list page
    When she clicks [View] for "Component Development"
    Then she is redirected to FOB-WORKFLOWS-VIEW_WORKFLOW-1
    And she sees workflow detail page

  Scenario: FOB-WORKFLOWS-LIST+FIND-11 Navigate to edit workflow
    Given Maria is on the workflows list page
    When she clicks [Edit] for "State Management Setup"
    Then she is redirected to FOB-WORKFLOWS-EDIT_WORKFLOW-1
    And the edit form is pre-populated

  Scenario: FOB-WORKFLOWS-LIST+FIND-12 Open delete confirmation
    Given Maria is on the workflows list page
    When she clicks [Delete] for "Testing & Documentation"
    Then the FOB-WORKFLOWS-DELETE_WORKFLOW-1 modal appears
    And it shows workflow details

  Scenario: FOB-WORKFLOWS-LIST+FIND-13 Duplicate workflow
    Given Maria is on the workflows list page
    When she clicks [Duplicate] for "Component Development"
    Then a modal appears "Duplicate workflow?"
    And she can enter a new name
    When she enters "Component Development (Copy)" and confirms
    Then a new workflow is created
    And it appears in the list as order #4

  Scenario: FOB-WORKFLOWS-LIST+FIND-14 Toggle to Flow View
    Given Maria is on the workflows list page in List View
    When she clicks [Flow View] toggle
    Then the display changes to Flow View
    And workflows are shown as connected boxes
    And each box shows workflow name and activity count
    And boxes are connected showing execution order

  Scenario: FOB-WORKFLOWS-LIST+FIND-15 Toggle back to List View
    Given Maria is in Flow View
    When she clicks [List View] toggle
    Then the display returns to table view

  Scenario: FOB-WORKFLOWS-LIST+FIND-16 Import workflow from template
    Given Maria is on the workflows list page
    When she clicks [Import Workflow from Template]
    Then a template selection modal appears
    And she sees available workflow templates
    When she selects a template and confirms
    Then a new workflow is created from template

  Scenario: FOB-WORKFLOWS-LIST+FIND-17 Enter reorder mode
    Given Maria is on the workflows list page
    When she clicks [Reorder Workflows]
    Then the list enters drag-and-drop mode
    And drag handles become prominent
    And a notice shows "Drag workflows to reorder"
    And action buttons change to [Cancel] [Save Order]

  Scenario: FOB-WORKFLOWS-LIST+FIND-18 Reorder workflows via drag-and-drop
    Given Maria is in reorder mode
    When she drags "Testing & Documentation" to position #1
    Then the visual order updates:
      | position | workflow                |
      |        1 | Testing & Documentation |
      |        2 | Component Development   |
      |        3 | State Management Setup  |
    When she clicks [Save Order]
    Then the new order is saved
    And success notification appears
    And reorder mode exits

  Scenario: FOB-WORKFLOWS-LIST+FIND-19 Cancel reordering
    Given Maria is in reorder mode
    And she has made changes
    When she clicks [Cancel]
    Then changes are discarded
    And original order is restored
    And reorder mode exits

  Scenario: FOB-WORKFLOWS-LIST+FIND-20 Empty state display
    Given Maria is viewing a playbook with zero workflows
    Then she sees empty state illustration
    And she sees "No workflows yet"
    And she sees "Create your first workflow to organize activities"
    And she sees [Create Workflow] button

  Scenario: FOB-WORKFLOWS-LIST+FIND-21 Workflows scoped to playbook
    Given Maria is viewing "React Frontend Development" playbook
    Then she sees only workflows belonging to this playbook
    And workflows from other playbooks are not visible
    And the Context Banner always shows current playbook

  Scenario: FOB-WORKFLOWS-LIST+FIND-22 Navigate back to playbook
    Given Maria is on the workflows list page
    When she clicks "React Frontend Development" in the breadcrumb
    Then she returns to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And she is on the Workflows tab

  Scenario: FOB-WORKFLOWS-LIST+FIND-23 Workflows show phase count correctly
    Given Maria is on the workflows list page
    Then "Component Development" shows "2" in Phases column
    And "State Management Setup" shows "0" in Phases column
    And "Testing & Documentation" shows "3" in Phases column

  Scenario: FOB-WORKFLOWS-LIST+FIND-24 Row hover shows actions
    Given Maria is on the workflows list page
    When she hovers over "Component Development" row
    Then the row is highlighted
    And the Actions dropdown becomes visible
    When she clicks the Actions dropdown
    Then she sees: View, Edit, Delete, Duplicate, More
