Feature: FOB-WORKFLOWS-EDIT_WORKFLOW-1 Edit Workflow
  As a methodology author (Maria)
  I want to edit workflow details
  So that I can update and improve execution sequences

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend Development"
    And the playbook has workflow "Component Development"

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-01 Open edit form
    Given Maria is viewing workflow "Component Development"
    When she clicks [Edit Workflow]
    Then she is redirected to FOB-WORKFLOWS-EDIT_WORKFLOW-1
    And all fields are pre-populated

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-02 Edit workflow name
    Given Maria is on the edit form
    When she changes Name to "Advanced Component Development"
    And she clicks [Save Changes]
    Then the workflow is updated
    And she sees success notification

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-03 Edit workflow description
    Given Maria is on the edit form
    When she updates the Description
    And she clicks [Save Changes]
    Then the description is updated

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-04 Change workflow order
    Given the workflow is at order #1
    When she changes Order to "3"
    And she clicks [Save Changes]
    Then the workflow moves to position 3
    And other workflows are reordered

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-05 Toggle phase organization
    Given the workflow has no phases
    When she selects "Use phases"
    And she saves
    Then phase support is enabled

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-06 Validate required fields
    Given Maria is on the edit form
    When she clears the Name field
    And she clicks [Save Changes]
    Then she sees validation error "Name is required"

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-07 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then she sees "Discard changes?" confirmation
    When she confirms
    Then changes are discarded

  Scenario: FOB-WORKFLOWS-EDIT_WORKFLOW-08 Save and continue editing
    Given Maria makes changes
    When she clicks [Save & Continue]
    Then changes are saved
    And she remains on edit form
