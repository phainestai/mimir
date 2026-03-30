Feature: Playbook Versioning and Lifecycle Management
    As a methodology author
    I want automatic version tracking for my draft playbooks
    And controlled change management for released playbooks
    So that I can iterate freely during development but maintain stability in production

  Background:
    Given I am logged in as "maria@ux.com"
    And I am on the playbooks list page
    # ==================== DRAFT VERSIONING ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-01 Create new draft playbook starts at version 0.1
    When I click "Create New Playbook"
    And I fill in basic information:
      | Field       | Value                        |
      | Name        | Product Discovery Framework  |
      | Description | User research and validation |
      | Category    | Product                      |
    And I select status "Draft"
    And I click "Create Playbook"
    Then I should see playbook detail page
    And I should see version badge "v0.1"
    And I should see status badge "Draft" in yellow

  Scenario: FOB-PLAYBOOKS-VERSIONING-02 Editing draft playbook metadata increments version
    Given I have a draft playbook "UX Research" at version "0.1"
    When I click "Edit" on the playbook
    And I change description to "Updated user research methodology"
    And I click "Save Changes"
    Then I should see success message "Playbook updated successfully (v0.2)"
    And I should see version badge "v0.2"
    And I should see status badge "Draft" in yellow

  Scenario: FOB-PLAYBOOKS-VERSIONING-03 Adding workflow to draft playbook increments version
    Given I have a draft playbook "Product Playbook" at version "0.2"
    When I view the playbook details
    And I navigate to "Workflows" tab
    And I click "Create New Workflow"
    And I fill in:
      | Field       | Value                    |
      | Name        | Discovery Phase          |
      | Description | User research activities |
    And I click "Create Workflow"
    Then playbook version should be "0.3"
    And I should see the new workflow "Discovery Phase"

  Scenario: FOB-PLAYBOOKS-VERSIONING-04 Adding activity to workflow increments playbook version
    Given I have a draft playbook "Dev Playbook" at version "0.3"
    And the playbook has workflow "Setup"
    When I navigate to workflow "Setup"
    And I click "Create Activity"
    And I fill in:
      | Field    | Value                |
      | Name     | Install Dependencies |
      | Guidance | Run npm install      |
    And I click "Save Activity"
    Then playbook version should be "0.4"
    And activity "Install Dependencies" should be visible

  Scenario: FOB-PLAYBOOKS-VERSIONING-05 Editing activity increments playbook version
    Given I have a draft playbook "Test Playbook" at version "0.5"
    And the playbook has workflow "Phase 1" with activity "Task A"
    When I edit activity "Task A"
    And I change the name to "Updated Task A"
    And I click "Save Changes"
    Then playbook version should be "0.6"

  Scenario: FOB-PLAYBOOKS-VERSIONING-06 Deleting workflow increments playbook version
    Given I have a draft playbook "Sample Playbook" at version "0.7"
    And the playbook has workflows:
      | Name    |
      | Phase 1 |
      | Phase 2 |
    When I delete workflow "Phase 2"
    And I confirm deletion
    Then playbook version should be "0.8"
    And workflow "Phase 2" should not be visible
    # ==================== RELEASE WORKFLOW ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-07 Releasing draft playbook sets version to 1.0
    Given I have a draft playbook "Ready Playbook" at version "0.9"
    When I view the playbook details
    And I click "Release" button
    Then I should see confirmation modal "Release Playbook?"
    And modal explains "This will change status to Released and set version to v1.0"
    And modal warns "Released playbooks can only be changed via PIP"
    When I confirm release
    Then I should see version badge "v1.0"
    And I should see status badge "Released" in blue
    And "Edit" button should be disabled
    And "Submit PIP" button should be visible

  Scenario: FOB-PLAYBOOKS-VERSIONING-08 Edit button disabled for released playbooks
    Given I have a released playbook "Production Playbook" at version "1.0"
    When I view the playbook details
    Then "Edit" button should be disabled
    And edit button tooltip should say "Released playbooks require PIP"

  Scenario: FOB-PLAYBOOKS-VERSIONING-09 Attempting to edit released playbook shows error
    Given I have a released playbook "Stable Playbook" at version "1.0"
    When I try to access edit URL directly
    Then I should be redirected to playbook detail page
    And I should see error "This playbook is Released and cannot be edited directly. Please submit a PIP (Process Improvement Proposal) to make changes."

  Scenario: FOB-PLAYBOOKS-VERSIONING-10 Cannot add workflow to released playbook
    Given I have a released playbook "Final Playbook" at version "1.0"
    When I view the playbook details
    And I navigate to "Workflows" tab
    Then "Create New Workflow" button should be disabled
    And tooltip should say "Released playbooks require PIP for changes"
    # ==================== VERSION DISPLAY ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-11 Playbook list shows current version
    Given I have playbooks:
      | Name          | Status   | Version |
      | Draft Work    | Draft    |     0.3 |
      | Stable Prod   | Released |     1.0 |
      | Another Draft | Draft    |     0.7 |
    When I am on the playbooks list page
    Then I should see versions in the list:
      | Playbook      | Version |
      | Draft Work    | v0.3    |
      | Stable Prod   | v1.0    |
      | Another Draft | v0.7    |

  Scenario: FOB-PLAYBOOKS-VERSIONING-12 Version history tab shows all versions
    Given I have a playbook "Evolving Playbook" with version history:
      | Version | Status   | Date       | Changes                |
      |     0.1 | Draft    | 2024-01-01 | Initial creation       |
      |     0.2 | Draft    | 2024-01-05 | Added workflow         |
      |     0.3 | Draft    | 2024-01-10 | Updated description    |
      |     1.0 | Released | 2024-01-15 | Released to production |
    When I view the playbook details
    And I navigate to "History" tab
    Then I should see version timeline with all 4 versions
    And each version shows date and change summary
    # ==================== DUPLICATE & EXPORT ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-13 Duplicating released playbook creates draft at v0.1
    Given I have a released playbook "Original" at version "1.0"
    When I click "Duplicate" on the playbook
    And I set new name "Copy of Original"
    And I confirm duplication
    Then I should see new playbook "Copy of Original"
    And new playbook version should be "0.1"
    And new playbook status should be "Draft"

  Scenario: FOB-PLAYBOOKS-VERSIONING-14 Export includes version number in filename
    Given I have a draft playbook "Export Test" at version "0.5"
    When I click "Export JSON" on the playbook
    Then I should download file "export-test-v0.5.json"
    And JSON should contain version "0.5"
    And JSON should contain status "draft"
    # ==================== MCP INTEGRATION ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-15 MCP can edit draft playbooks
    Given I have a draft playbook "MCP Editable" at version "0.2"
    When AI assistant via MCP suggests editing the playbook
    And MCP tool executes playbook update
    Then playbook version should increment to "0.3"
    And changes should be applied successfully

  Scenario: FOB-PLAYBOOKS-VERSIONING-16 MCP cannot edit released playbooks
    Given I have a released playbook "MCP Protected" at version "1.0"
    When AI assistant via MCP attempts to edit the playbook
    Then MCP should return error "Playbook is Released - use PIP workflow"
    And MCP should suggest "Create a PIP to propose changes"
    And playbook version should remain "1.0"
    # ==================== EDGE CASES ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-17 Multiple rapid edits increment version correctly
    Given I have a draft playbook "Rapid Edit" at version "0.1"
    When I edit the playbook and save (version → 0.2)
    And I edit the playbook again and save (version → 0.3)
    And I add a workflow (version → 0.4)
    And I add an activity (version → 0.5)
    Then playbook version should be "0.5"
    And version history should show all 5 versions

  Scenario: FOB-PLAYBOOKS-VERSIONING-18 Cannot release playbook with validation errors
    Given I have a draft playbook "Invalid Playbook" at version "0.2"
    And the playbook has no workflows
    When I click "Release" button
    Then I should see validation error "Playbook must have at least one workflow to be released"
    And playbook status should remain "Draft"
    And playbook version should remain "0.2"

  Scenario: FOB-PLAYBOOKS-VERSIONING-19 Version increments persist across page reloads
    Given I have a draft playbook "Persistent" at version "0.3"
    When I edit the playbook and save
    Then version should be "0.4"
    When I refresh the page
    Then version should still be "0.4"
    When I navigate away and return
    Then version should still be "0.4"
