Feature: FOB-PHASES-CREATE_PHASE-1 Create Phase (OPTIONAL)
  As a methodology author (Maria)
  I want to create phases within a workflow
  So that I can group activities logically

  Background:
    Given Maria is authenticated in FOB
    And she is viewing workflow "Component Development" with phase support enabled

  Scenario: FOB-PHASES-CREATE_PHASE-01 Open create phase form
    Given Maria is on phases list
    When she clicks [Create New Phase]
    Then she is redirected to FOB-PHASES-CREATE_PHASE-1
    And the Parent Workflow field shows "Component Development" (read-only)

  Scenario: FOB-PHASES-CREATE_PHASE-02 Create phase successfully
    Given Maria is on the create phase form
    When she enters "Planning" in Name
    And she enters "Initial planning and requirements" in Description
    And she clicks [Create Phase]
    Then the phase is created
    And she sees success notification

  Scenario: FOB-PHASES-CREATE_PHASE-03 Validate required fields
    Given Maria is on the create phase form
    When she leaves Name empty
    And she clicks [Create Phase]
    Then she sees validation error "Name is required"

  Scenario: FOB-PHASES-CREATE_PHASE-04 Set phase order
    Given the workflow has 2 existing phases
    When she creates a new phase with order "2"
    Then the phase is inserted at position 2
    And existing phases are reordered

  Scenario: FOB-PHASES-CREATE_PHASE-05 Cancel phase creation
    Given Maria has entered phase data
    When she clicks [Cancel]
    Then she sees "Discard changes?" confirmation
    When she confirms
    Then no phase is created
