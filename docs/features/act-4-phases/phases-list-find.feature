Feature: FOB-PHASES-LIST+FIND-1 Phases List and Search (OPTIONAL)
  As a methodology author (Maria)
  I want to view and search phases within a workflow
  So that I can organize activities into logical groups

  Background:
    Given Maria is authenticated in FOB
    And she is viewing workflow "Component Development" in playbook "React Frontend v1.2"
    And the workflow has phase organization enabled
    And the workflow has 3 phases:
      | name           | activities | order |
      | Planning       |          3 |     1 |
      | Implementation |          5 |     2 |
      | Testing        |          2 |     3 |

  Scenario: FOB-PHASES-LIST+FIND-01 Navigate to phases list from workflow
    Given Maria is on FOB-WORKFLOWS-VIEW_WORKFLOW-1
    When she clicks the "Phases" tab
    Then she is redirected to FOB-PHASES-LIST+FIND-1
    And she sees "Phases in Component Development" header

  Scenario: FOB-PHASES-LIST+FIND-02 View phases table
    Given Maria is on the phases list page
    Then she sees all 3 phases in order
    And each phase shows: Name, Description, Activities, Order, Actions

  Scenario: FOB-PHASES-LIST+FIND-03 Create new phase
    Given Maria is on the phases list page
    When she clicks [Create New Phase]
    Then she is redirected to FOB-PHASES-CREATE_PHASE-1

  Scenario: FOB-PHASES-LIST+FIND-04 View phase details
    Given Maria is on the phases list page
    When she clicks [View] for "Planning"
    Then she is redirected to FOB-PHASES-VIEW_PHASE-1

  Scenario: FOB-PHASES-LIST+FIND-05 Reorder phases
    Given Maria is on the phases list page
    When she clicks [Reorder Phases]
    Then drag-and-drop mode is enabled

  Scenario: FOB-PHASES-LIST+FIND-06 Empty state when no phases
    Given the workflow has no phases
    Then she sees "No phases yet"
    And she sees [Create First Phase] button

  Scenario: FOB-PHASES-LIST+FIND-07 Phases scoped to workflow
    Given Maria is viewing workflow "Component Development"
    Then she sees only phases belonging to this workflow
    And phases from other workflows are not visible
