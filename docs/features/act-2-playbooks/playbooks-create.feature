Feature: FOB-PLAYBOOKS-CREATE_PLAYBOOK-1 Create New Playbook ✅
  As a methodology author (Maria)
  I want to create a new playbook using a wizard
  So that I can define and organize my methodology

  # Access control (MVP simplified):
  # - Visibility: Private (owner-only view) or Public (any authenticated user can view).
  # - Write (draft edit, delete) always owner-only regardless of visibility.
  # - Draft: editable by owner; Released: read-only except PIP.
  # - PIP finalize: owner or staff admin. Public viewers cannot finalize.
  # - Family, Local only, Homebase sync: deferred (not in MVP).
  # - MCP always author-scoped even for public playbooks (GUI-only public read).

  Status: ✅ COMPLETE - core wizard scenarios implemented
  Branch: feature/playbooks-crudv
  Issue: #28

  Background:
    Given Maria is authenticated in FOB
    And she is on the playbooks list page

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-01 Open create playbook wizard
    Given Maria is on FOB-PLAYBOOKS-LIST+FIND-1
    When she clicks the [Create New Playbook] button
    Then she sees the playbook creation wizard
    And she is on "Step 1: Basic Information"
    And all required fields are marked with asterisk (*)

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-02 Complete Step 1 with valid data
    Given Maria is on the playbook creation wizard Step 1
    When she enters "Product Discovery Framework" in the Name field
    And she enters "Comprehensive methodology for discovering and validating product opportunities" in the Description field
    And she selects "Product" from the Category dropdown
    And she enters tags: "product management, discovery, validation, user research"
    And she selects "Private" for Visibility
    And she clicks [Next: Add Workflows →]
    Then she proceeds to "Step 2: Add Workflows"
    And her input is saved

  Scenario Outline: FOB-PLAYBOOKS-CREATE_PLAYBOOK-03 Validate required fields on Step 1
    Given Maria is on the playbook creation wizard Step 1
    When she leaves the "<field>" field empty
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "<error_message>"
    And the "<field>" field is highlighted in red
    And she remains on Step 1

    Examples:
      | field       | error_message                                       |
      | Name        | Name is required. Must be 3-100 characters.         |
      | Description | Description is required. Must be 10-500 characters. |
      | Category    | Please select a category.                           |

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-04 Duplicate playbook name validation
    Given Maria is on the playbook creation wizard Step 1
    And a playbook named "React Frontend Development" already exists
    When she enters "React Frontend Development" in the Name field
    And she fills all other required fields
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "A playbook with this name already exists. Please choose a different name."
    And the Name field is highlighted in red
    And she remains on Step 1

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-05 Name length validation
    Given Maria is on the playbook creation wizard Step 1
    When she enters "AB" in the Name field (too short)
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "Name must be at least 3 characters."
    When she enters a name with 101 characters (too long)
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "Name must not exceed 100 characters."

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-06 Description length validation
    Given Maria is on the playbook creation wizard Step 1
    When she enters "Too short" in the Description field (9 characters)
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "Description must be at least 10 characters."
    When she enters a description with 501 characters (too long)
    And she clicks [Next: Add Workflows →]
    Then she sees validation error "Description must not exceed 500 characters."

  # MVP simplified: visibility is Private (default) or Public.
  # Family and Local only are deferred (Homebase). See playbooks-access-control.md.
  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-07a Create private playbook (default)
    Given Maria is on the playbook creation wizard Step 1
    Then the Visibility field shows "Private" selected by default
    And she sees help text "Only you can view and edit this playbook"
    When she keeps "Private" selected and completes the wizard
    Then the playbook is created with visibility private
    And only Maria can list and open the playbook in FOB

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-07b Create public playbook
    Given Maria is on the playbook creation wizard Step 1
    When she selects "Public" for Visibility
    And she sees help text "Any authenticated user can view this playbook; only you can edit or delete it"
    And she completes all required fields and proceeds through Steps 2 and 3
    Then the playbook is created with visibility public
    And any authenticated user can open and read the playbook in FOB
    And only Maria can edit or delete it

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-08 Add optional tags
    Given Maria is on the playbook creation wizard Step 1
    When she enters "product management" in the Tags field
    And she presses Enter
    Then "product management" is added as a tag token
    When she enters "discovery, validation" and presses Enter
    Then "discovery" and "validation" are added as separate tag tokens
    And she can remove any tag by clicking the X icon

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-09 Skip adding workflows in Step 2
    Given Maria has completed Step 1 successfully
    And she is on "Step 2: Add Workflows"
    Then she sees "You can add workflows now or later"
    And she sees [Skip for Now] and [Add First Workflow] buttons
    When she clicks [Skip for Now]
    Then she proceeds to "Step 3: Publishing Settings"

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-10 Add first workflow inline in Step 2
    Given Maria has completed Step 1 successfully
    And she is on "Step 2: Add Workflows"
    When she clicks [Add First Workflow]
    Then she sees inline workflow creation form
    And she sees fields: Workflow name (required), Workflow description (required)
    When she enters "Discovery Phase" in workflow name
    And she enters "Initial research and validation activities" in workflow description
    And she clicks [Add Workflow]
    Then the workflow "Discovery Phase" is added to the playbook
    And she proceeds to "Step 3: Publishing Settings"

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-11 Cancel adding workflow in Step 2
    Given Maria has completed Step 1 successfully
    And she is on "Step 2: Add Workflows" with inline form open
    When she clicks [Cancel] on the workflow form
    Then the inline form closes
    And she is back to the Step 2 main view
    And she can choose [Skip for Now] or [Add First Workflow] again

  @implemented
  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-12 Complete Step 3 with Released status
    Given Maria has completed Steps 1 and 2
    And she is on "Step 3: Publishing Settings"
    Then she sees a summary of the playbook being created
    And she sees Status options: Draft and Released
    When she selects "Released" with note v1.0 controlled via PIP
    And she clicks [Create Playbook]
    Then the playbook is created with Released status at v1.0
    And she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 for the new playbook
    And direct edit is blocked until a PIP is applied

  @implemented
  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-13 Complete Step 3 with Draft status
    Given Maria has completed Steps 1 and 2
    And she is on "Step 3: Publishing Settings"
    When she selects "Draft" with note v0.1 fully editable
    And she clicks [Create Playbook]
    Then the playbook is created with Draft status at v0.1
    And she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 for the new playbook
    And the playbook status badge shows "Draft" (yellow)

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-14 Review summary in Step 3
    Given Maria has completed Steps 1 and 2
    And she is on "Step 3: Publishing Settings"
    Then she sees a summary card displaying:
      | field       | value                                                               |
      | Name        | Product Discovery Framework                                         |
      | Description | Comprehensive methodology for discovering and validating product... |
      | Category    | Product                                                             |
      | Tags        | product management, discovery, validation, user research            |
      | Visibility  | Private                                                             |
      | Workflows   |                             1 (Discovery Phase) OR "None added yet" |

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-15 Cancel wizard at any step
    Given Maria is on playbook creation wizard Step 1
    When she clicks [Cancel]
    Then she sees confirmation modal "Discard changes?"
    And the modal shows "Your progress will be lost."
    When she clicks [Discard] on the modal
    Then the wizard closes
    And she returns to FOB-PLAYBOOKS-LIST+FIND-1
    And no playbook is created

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-16 Cancel wizard confirmation - keep editing
    Given Maria is on playbook creation wizard Step 2
    And she has entered data in Step 1
    When she clicks [Cancel]
    And she sees confirmation modal "Discard changes?"
    When she clicks [Keep Editing] on the modal
    Then the modal closes
    And she remains on Step 2 with her data intact

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-17 Navigate back to previous step
    Given Maria is on "Step 2: Add Workflows"
    When she clicks [← Back] or the Step 1 breadcrumb
    Then she returns to "Step 1: Basic Information"
    And all her previously entered data is preserved
    When she clicks [Next: Add Workflows →]
    Then she returns to "Step 2: Add Workflows"

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-18 Playbook appears in list after creation
    Given Maria has successfully created "Product Discovery Framework"
    When she navigates to FOB-PLAYBOOKS-LIST+FIND-1
    Then she sees "Product Discovery Framework" in the playbooks table
    And the playbook shows:
      | field         | value                       |
      | Name          | Product Discovery Framework |
      | Author        | Maria Rodriguez             |
      | Version       | v1.0                        |
      | Status        | Active OR Draft             |
      | Source        | Owned                       |
      | Last Modified | Just now OR Today           |

  @deferred @homebase
  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-19 Create playbook with Family visibility
    # Deferred: Family (share with Homebase family) not in MVP. Visibility options are Private / Public only.

  @deferred @homebase
  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-20 Create playbook with Local only visibility
    # Deferred: Local only (exclude from Homebase) not in MVP. Visibility options are Private / Public only.

  Scenario: FOB-PLAYBOOKS-CREATE_PLAYBOOK-21 Auto-increment version on creation
    Given Maria is creating a new playbook
    When she reaches "Step 3: Publishing Settings"
    Then she sees "Initial Version: v1.0" and it is read-only
    And she cannot modify the version number on creation
    And the version will be v1.0 after creation
