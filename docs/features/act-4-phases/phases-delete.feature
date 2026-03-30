Feature: FOB-PHASES-DELETE_PHASE-1 Delete Phase (OPTIONAL)
  As a methodology author (Maria)
  I want to delete phases
  So that I can reorganize activity groupings

  Background:
    Given Maria is authenticated in FOB
    And she owns workflow "Component Development"
    And the workflow has phase "Old Phase" with 2 activities

  Scenario: FOB-PHASES-DELETE_PHASE-01 Open delete confirmation
    Given Maria is on phases list
    When she clicks [Delete] for "Old Phase"
    Then the FOB-PHASES-DELETE_PHASE-1 modal appears
    And it shows "Delete Phase?"

  Scenario: FOB-PHASES-DELETE_PHASE-02 Modal shows phase details
    Given the delete modal is open
    Then it displays phase name and activity count
    And it shows "Activities will be moved to unassigned"

  Scenario: FOB-PHASES-DELETE_PHASE-03 Confirm deletion
    Given the delete modal is open
    When she clicks [Delete Phase]
    Then the phase is deleted
    And activities are moved to unassigned
    And she sees success notification

  Scenario: FOB-PHASES-DELETE_PHASE-04 Cancel deletion
    Given the delete modal is open
    When she clicks [Cancel]
    Then the modal closes
    And the phase is not deleted

  Scenario: FOB-PHASES-DELETE_PHASE-05 Reorder remaining phases after deletion
    Given workflow has 3 phases in order
    When she deletes phase #2
    Then remaining phases are renumbered to 1, 2
