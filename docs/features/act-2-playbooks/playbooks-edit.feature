Feature: FOB-PLAYBOOKS-EDIT_PLAYBOOK-1 Edit Playbook
  As a methodology author (Maria)
  I want to edit my playbook's details
  So that I can update and improve my methodology

  Background:
    Given Maria is authenticated in FOB
    And Maria owns the playbook "Product Discovery Framework" with:
      | field      | value   |
      | version    | v1.0    |
      | status     | Active  |
      | category   | Product |
      | visibility | Private |
      | workflows  |       1 |

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-01 Open edit form from playbook detail page
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 for "Product Discovery Framework"
    When she clicks the [Edit] button
    Then she is redirected to FOB-PLAYBOOKS-EDIT_PLAYBOOK-1
    And she sees the edit form
    And all fields are pre-populated with current values

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-02 Edit form shows pre-populated data
    Given Maria is on the edit form for "Product Discovery Framework"
    Then the form displays pre-populated fields:
      | field       | value                                                            |
      | Name        | Product Discovery Framework                                      |
      | Description | Comprehensive methodology for discovering and validating product |
      | Category    | Product                                                          |
      | Tags        | product management, discovery, validation                        |
      | Visibility  | Private (only me)                                                |
      | Status      | Active                                                           |
      | Version     | v1.0 (read-only)                                                 |

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-03 Edit playbook name
    Given Maria is on the edit form
    When she changes the Name to "Product Discovery Framework v2"
    And she clicks [Save Changes]
    Then the playbook is updated successfully
    And she sees success notification "Playbook updated successfully"
    And she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And the playbook name is now "Product Discovery Framework v2"

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-04 Edit playbook description
    Given Maria is on the edit form
    When she updates the Description
    And she clicks [Save Changes]
    Then the playbook description is updated
    And she sees success notification

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-05 Change playbook category
    Given Maria is on the edit form
    And the current category is "Product"
    When she selects "Research" from the Category dropdown
    And she clicks [Save Changes]
    Then the playbook category is changed to "Research"

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-06 Add new tags
    Given Maria is on the edit form
    And current tags are "product management, discovery"
    When she adds tags "user research, validation, lean startup"
    And she clicks [Save Changes]
    Then all tags are saved
    And the playbook shows all 5 tags

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-07 Remove existing tags
    Given Maria is on the edit form
    And current tags include "discovery" and "validation"
    When she removes the "discovery" tag
    And she clicks [Save Changes]
    Then "discovery" tag is removed from the playbook
    And "validation" tag remains

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-08 Change visibility from Private to Family
    Given Maria is on the edit form
    And current visibility is "Private (only me)"
    And Maria is a member of "UX" family
    When she selects "Family" for Visibility
    And she selects "UX" from the family dropdown
    And she clicks [Save Changes]
    Then the playbook visibility is changed to "Family (UX)"
    And a notice shows "Playbook will be available to UX family after syncing to Homebase"

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-09 Change visibility from Family to Private
    Given Maria is on the edit form
    And current visibility is "Family (UX)"
    When she selects "Private (only me)"
    Then she sees warning "Changing to Private will recall this playbook from family members"
    When she confirms and clicks [Save Changes]
    Then the playbook visibility is changed to Private
    And the playbook is no longer available to family members

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-10 Change status from Active to Draft
    Given Maria is on the edit form
    And current status is "Active"
    When she selects "Draft (work in progress)"
    And she clicks [Save Changes]
    Then the playbook status changes to "Draft"
    And the status badge on detail page shows "Draft" (yellow)

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-11 Change status from Draft to Active
    Given Maria is on the edit form
    And current status is "Draft"
    When she selects "Active (ready to use)"
    And she clicks [Save Changes]
    Then the playbook status changes to "Active"
    And the status badge shows "Active" (green)

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-12 Version field is read-only
    Given Maria is on the edit form
    Then the Version field shows "v1.0"
    And the Version field is read-only
    And a note explains "Version changes via PIPs only"
    And she cannot modify the version number directly

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-13 Validate required fields on edit
    Given Maria is on the edit form
    When she clears the Name field
    And she clicks [Save Changes]
    Then she sees validation error "Name is required"
    And the Name field is highlighted in red
    And the playbook is not updated

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-14 Duplicate name validation on edit
    Given Maria is on the edit form
    And another playbook named "React Frontend Development" exists
    When she changes the Name to "React Frontend Development"
    And she clicks [Save Changes]
    Then she sees validation error "A playbook with this name already exists"
    And the Name field is highlighted in red
    And the playbook is not updated

  Scenario Outline: FOB-PLAYBOOKS-EDIT_PLAYBOOK-15 Validate field lengths
    Given Maria is on the edit form
    When she enters "<value>" in the "<field>" field
    And she clicks [Save Changes]
    Then she sees validation error "<error_message>"

    Examples:
      | field       | value             | error_message                              |
      | Name        | AB                | Name must be at least 3 characters         |
      | Name        | [101 char string] | Name must not exceed 100 characters        |
      | Description | Too short         | Description must be at least 10 characters |
      | Description | [501 char string] | Description must not exceed 500 characters |

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-16 Cancel editing without confirmation
    Given Maria is on the edit form
    And she has not made any changes
    When she clicks [Cancel]
    Then she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And no changes are saved

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-17 Cancel editing with unsaved changes
    Given Maria is on the edit form
    And she has changed the Name to "New Name"
    When she clicks [Cancel]
    Then she sees confirmation modal "Discard changes?"
    And the modal shows "You have unsaved changes"
    When she clicks [Discard]
    Then the form closes
    And she returns to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And the original name is preserved

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-18 Keep editing after cancel confirmation
    Given Maria is on the edit form
    And she has unsaved changes
    When she clicks [Cancel]
    And she sees "Discard changes?" modal
    When she clicks [Keep Editing]
    Then the modal closes
    And she remains on the edit form
    And her changes are still in the form

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-19 Save and continue editing
    Given Maria is on the edit form
    When she makes changes
    And she clicks [Save & Continue Editing]
    Then the playbook is updated
    And she sees success notification
    And she remains on the edit form
    And the form is refreshed with updated values

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-20 Multiple field edits in one save
    Given Maria is on the edit form
    When she changes Name to "Updated Framework"
    And she changes Description to "Enhanced methodology for product discovery and validation"
    And she selects "Research" category
    And she adds tag "innovation"
    And she changes status to "Draft"
    And she clicks [Save Changes]
    Then all changes are saved together
    And she sees success notification
    And the playbook detail page shows all updated fields

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-21 Form validation prevents submission
    Given Maria is on the edit form
    When she enters invalid data in multiple fields
    And she clicks [Save Changes]
    Then all validation errors are displayed
    And invalid fields are highlighted in red
    And she sees "Please fix errors before saving"
    And the playbook is not updated

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-22 Breadcrumb navigation from edit form
    Given Maria is on the edit form
    And the breadcrumb shows "Playbooks > Product Discovery Framework > Edit"
    When she clicks "Product Discovery Framework" in breadcrumb
    Then she sees "Discard changes?" confirmation (if changes made)
    When she confirms
    Then she returns to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-23 Cannot edit downloaded playbooks
    Given Maria is viewing downloaded playbook "React Frontend Development"
    Then the [Edit] button is not visible
    And she cannot access the edit form

  Scenario: FOB-PLAYBOOKS-EDIT_PLAYBOOK-24 Edit form auto-save draft (optional feature)
    Given Maria is on the edit form
    When she makes changes
    And she waits 30 seconds without clicking Save
    Then she sees "Draft auto-saved" notification
    And her changes are preserved if she closes and reopens
