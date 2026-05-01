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

  Scenario: FOB-PLAYBOOKS-VERSIONING-07 Releasing a playbook bumps major version and requires a release description
    Given I have a draft playbook "Ready Playbook" at version "0.9"
    When I view the playbook details
    And I click "Release" button
    Then I should see Release modal "Release Playbook?"
    And modal explains "Releasing increments the major version (v0.9 → v1.0) and sets status to Released"
    And modal warns "Released playbooks can only be changed via PIP"
    And modal requires field "Release Description" (multi-line, mandatory)
    When I fill "Release Description" with "Initial production release"
    And I confirm release
    Then I should see version badge "v1.0"
    And I should see status badge "Released" in blue
    And "Edit" button should be disabled
    And "Submit PIP" button should be visible
    And the version history records v1.0 with description "Initial production release" and status "Released"

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

  Scenario: FOB-PLAYBOOKS-VERSIONING-12 Version history tab shows all major and minor versions with descriptions
    Given I have a playbook "Evolving Playbook" with version history:
      | Version | Status   | Kind  | Date       | Description                                  | Source     |
      |     0.1 | Draft    | minor | 2024-01-01 | Initial creation                             | author     |
      |     0.2 | Draft    | minor | 2024-01-05 | Added workflow "Discovery"                   | author     |
      |     0.3 | Draft    | minor | 2024-01-10 | Updated playbook description                 | author     |
      |     1.0 | Released | major | 2024-01-15 | Initial production release                   | release    |
      |     1.1 | Released | minor | 2024-02-01 | PIP-12: add Activity "Generate Manifest"     | PIP-12     |
      |     1.2 | Released | minor | 2024-02-10 | PIP-15: 3 edits across Workflow BTE          | PIP-15     |
      |     2.0 | Released | major | 2024-03-01 | GORBACT rollout: uniform manifests           | release    |
    When I view the playbook details
    And I navigate to "History" tab
    Then I should see version timeline with all 7 entries in reverse-chronological order
    And each entry shows: version, kind (major/minor), status, date, description, source
    And major entries (v1.0, v2.0) are visually distinguished from minor entries
    And entries sourced from a PIP link to that PIP
    And entries sourced from a release show the release description
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
    # ==================== RELEASE DESCRIPTION & RE-RELEASE ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-20 Release is blocked when description is missing
    Given I have a draft playbook "No Description" at version "0.4"
    And the playbook has at least one workflow
    When I click "Release" button
    And I leave "Release Description" empty
    And I confirm release
    Then I should see validation error "Release Description is required"
    And the Release modal should remain open
    And playbook status should remain "Draft"
    And playbook version should remain "0.4"

  Scenario: FOB-PLAYBOOKS-VERSIONING-21 Re-releasing a Released playbook bumps to the next major version
    Given I have a released playbook "Mature Playbook" at version "1.3"
    And the playbook has accumulated minor changes since v1.0
    When I click "Release" button
    Then the Release modal explains "Releasing increments the major version (v1.3 → v2.0) and sets status to Released"
    When I fill "Release Description" with "GORBACT rollout: enforces uniform GORBACT manifests across workflows"
    And I confirm release
    Then I should see version badge "v2.0"
    And I should see status badge "Released" in blue
    And version history records v2.0 with description "GORBACT rollout: enforces uniform GORBACT manifests across workflows" and status "Released"
    And all prior versions (v1.0, v1.1, v1.2, v1.3) remain visible in version history
    # ==================== PIP -> MINOR BUMP ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-22 Approving a PIP produces a single minor bump aggregating all its changes
    Given I have a released playbook "GORBACT-aware Playbook" at version "1.0"
    And a PIP "PIP-42: Use GORBACT uniformly" exists with changes:
      | Target              | Action                                        |
      | Workflow EST        | Add Activity "Generate GORBACT Manifest"      |
      | Skill library       | Add Skill "XXX with Gorbact"                  |
      | Artifact library    | Add Artifact "GORBACT Manifest"               |
      | Workflow BTE        | Edit BTE-06 to require "GORBACT Manifest" in  |
    When the PIP is approved and merged
    Then playbook version should increment to "1.1"
    And major version should remain "1"
    And version history records exactly one new entry "v1.1" (not one per change)
    And the v1.1 description summarizes all 4 changes from PIP-42
    And the v1.1 history entry links back to PIP-42
    And status should remain "Released"

  Scenario: FOB-PLAYBOOKS-VERSIONING-23 Approving multiple PIPs produces sequential minor bumps
    Given I have a released playbook "Active Playbook" at version "1.0"
    When PIP-12 is approved (1 change)
    Then playbook version should be "1.1"
    When PIP-15 is approved (3 changes)
    Then playbook version should be "1.2"
    When PIP-19 is approved (2 changes)
    Then playbook version should be "1.3"
    And version history shows v1.0, v1.1, v1.2, v1.3 with one entry per PIP
    # ==================== ADMIN REVERT TO DRAFT ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-24 Admin can revert a Released playbook back to Draft, retaining version number
    Given I am logged in as an admin
    And there exists a released playbook "Locked Playbook" at version "1.2"
    When I open the playbook in admin tools
    And I click "Revert to Draft"
    And I confirm the action
    Then playbook status should change to "Draft"
    And playbook version should remain "1.2"
    And complete version history (v1.0, v1.1, v1.2) should be preserved
    And version history records an admin event "Reverted to Draft by admin" at v1.2
    And "Edit" button should now be enabled
    And "Submit PIP" button should no longer be visible

  Scenario: FOB-PLAYBOOKS-VERSIONING-25 Editing an admin-reverted Draft resumes minor bumps; next Release bumps to next major
    Given an admin reverted "Locked Playbook" from Released v1.2 to Draft v1.2
    When I edit the playbook description
    And I save
    Then playbook version should be "1.3"
    And status should remain "Draft"
    When I add a workflow
    Then playbook version should be "1.4"
    When I click "Release"
    And I fill "Release Description" with "Re-release after admin revert"
    And I confirm release
    Then playbook version should be "2.0"
    And status should be "Released"
    And version history shows the full timeline: v1.0, v1.1, v1.2 (Released), v1.2 (Reverted), v1.3, v1.4, v2.0
    # ==================== SCHEMA & MIGRATION ====================

  Scenario: FOB-PLAYBOOKS-VERSIONING-26 PlaybookVersion stores X.Y versions with descriptions, kind, and source
    Given the data model for playbook version history
    Then each PlaybookVersion row stores:
      | field          | type / constraint                                                                 |
      | version_number | Decimal(5,1) — semantic X.Y (e.g. 0.3, 1.0, 1.2)                                |
      | description    | TextField — release description for major bumps; change summary for minor bumps |
      | is_major       | Boolean — true when created by Release action; false for aggregated minor edits   |
      | source         | Enum: author, release, pip, admin                                                 |
      | pip            | FK to PIP, nullable; set when source is pip                                       |
      | snapshot_data  | JSONField — playbook snapshot                                                      |
      | change_summary | TextField (legacy mirror of description until UI fully migrated), may be merged   |
      | created_at     | DateTime                                                                            |
      | created_by     | FK User, nullable                                                                  |
    And unique constraint (playbook, version_number)
    And default ordering newest version first

  Scenario: FOB-PLAYBOOKS-VERSIONING-27 Migration preserves existing integer PlaybookVersion history
    Given existing PlaybookVersion rows with integer version_number 1, 2, 3 for a playbook
    When migration to X.Y shape runs
    Then version_number becomes 1.0, 2.0, 3.0
    And is_major is backfilled True for migrated rows
    And source is backfilled "release" for migrated rows (best-effort)
    And description uses existing change_summary where applicable
    And no rows dropped
    And running migrations twice does not corrupt data
