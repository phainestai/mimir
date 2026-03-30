Feature: FOB-PHASES-VIEW_PHASE-1 View Phase Details (OPTIONAL)
  As a methodology author (Maria)
  I want to view phase details
  So that I can understand its structure and activities

  Background:
    Given Maria is authenticated in FOB
    And she is viewing phase "Planning" in workflow "Component Development"
    And the phase has 3 activities

  Scenario: FOB-PHASES-VIEW_PHASE-01 Open phase detail page
    Given Maria is on phases list
    When she clicks [View] for "Planning"
    Then she is redirected to FOB-PHASES-VIEW_PHASE-1
    And she sees breadcrumb with workflow and phase name

  Scenario: FOB-PHASES-VIEW_PHASE-02 View phase header
    Given Maria is on the phase detail page
    Then she sees phase name "Planning"
    And she sees parent workflow badge
    And she sees order badge "#1 of 3"

  Scenario: FOB-PHASES-VIEW_PHASE-03 View activities in phase
    Given Maria is on the phase detail page
    Then she sees all 3 activities assigned to this phase
    And each activity shows name, description, and dependencies

  Scenario: FOB-PHASES-VIEW_PHASE-04 Edit phase button
    Given Maria is viewing the phase
    When she clicks [Edit Phase]
    Then she is redirected to FOB-PHASES-EDIT_PHASE-1

  Scenario: FOB-PHASES-VIEW_PHASE-05 Delete phase button
    Given Maria is viewing the phase
    When she clicks [Delete Phase]
    Then the FOB-PHASES-DELETE_PHASE-1 modal appears
