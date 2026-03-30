Feature: FOB-WORKFLOWS-VIEW_WORKFLOW-1 View Workflow Details
  As a methodology author (Maria)
  I want to view complete workflow details
  So that I can understand its structure and activities

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend Development v1.2"
    And the workflow "Component Development" exists with 8 activities and 2 phases

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-01 Open workflow detail page
    Given Maria is on FOB-WORKFLOWS-LIST+FIND-1
    When she clicks [View] for "Component Development"
    Then she is redirected to FOB-WORKFLOWS-VIEW_WORKFLOW-1
    And she sees breadcrumb "Playbooks > React Frontend Development > Workflows > Component Development"

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-02 View workflow header
    Given Maria is on the workflow detail page
    Then she sees workflow name "Component Development"
    And she sees parent playbook badge with link to "React Frontend Development"
    And she sees order badge "#1 of 3"

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-03 View activities list
    Given Maria is on the workflow detail page
    Then she sees "Activities" section
    And she sees all 8 activities in order
    And each activity shows: Name, Description, Dependencies, Status

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-04 View phases (if workflow has phases)
    Given the workflow has 2 phases
    When Maria views the workflow
    Then she sees "Phases" section showing 2 phases
    And activities are grouped under their respective phases

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-05 Navigate to activity detail
    Given Maria is viewing the workflow
    When she clicks on an activity
    Then she navigates to FOB-ACTIVITIES-VIEW_ACTIVITY-1

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-06 Edit workflow button
    Given Maria is viewing the workflow
    When she clicks [Edit Workflow]
    Then she is redirected to FOB-WORKFLOWS-EDIT_WORKFLOW-1

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-07 Delete workflow button
    Given Maria is viewing the workflow
    When she clicks [Delete Workflow]
    Then the FOB-WORKFLOWS-DELETE_WORKFLOW-1 modal appears

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-08 Duplicate workflow
    Given Maria is viewing the workflow
    When she clicks [Duplicate Workflow]
    Then a modal appears for duplication

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-09 Navigate back to workflows list
    Given Maria is viewing the workflow
    When she clicks "Workflows" in breadcrumb
    Then she returns to FOB-WORKFLOWS-LIST+FIND-1

  Scenario: FOB-WORKFLOWS-VIEW_WORKFLOW-10 Add activity button (for editable workflows)
    Given Maria is viewing her own playbook's workflow
    Then she sees [Add Activity] button
    When she clicks it
    Then activity creation form appears
