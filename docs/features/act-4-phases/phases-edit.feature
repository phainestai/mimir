Feature: FOB-PHASES-EDIT_PHASE-1 Edit Phase (OPTIONAL)
  As a methodology author (Maria)
  I want to edit phase details
  So that I can update logical groupings

  Background:
    Given Maria is authenticated in FOB
    And she owns workflow "Component Development"
    And the workflow has phase "Planning"

  Scenario: FOB-PHASES-EDIT_PHASE-01 Open edit form
    Given Maria is viewing phase "Planning"
    When she clicks [Edit Phase]
    Then she is redirected to FOB-PHASES-EDIT_PHASE-1
    And all fields are pre-populated

  Scenario: FOB-PHASES-EDIT_PHASE-02 Edit phase name
    Given Maria is on the edit form
    When she changes Name to "Requirements & Planning"
    And she clicks [Save Changes]
    Then the phase is updated

  Scenario: FOB-PHASES-EDIT_PHASE-03 Edit phase description
    Given Maria is on the edit form
    When she updates the Description
    And she saves
    Then the description is updated

  Scenario: FOB-PHASES-EDIT_PHASE-04 Change phase order
    Given the phase is at order #1
    When she changes Order to "3"
    And she saves
    Then the phase moves to position 3

  Scenario: FOB-PHASES-EDIT_PHASE-05 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then changes are discarded
