Feature: FOB-PIP-CREATE-1 Create Playbook Improvement Proposal with Structured Changes
  As a methodology author (Maria)
  I want to create a PIP with typed Changes (ADD / ALTER / DROP / LINK / UNLINK)
  So that I can propose specific, reviewable alterations to a Released playbook

  Status: 🔲 TODO
  Related: act-9-pips/pips-list.feature, act-9-pips/pips-view.feature

  Background:
    Given Maria is authenticated in FOB
    And the following playbooks exist:
      | id | name                   | status   | version |
      |  1 | React Frontend Dev     | released |     1.0 |
      |  2 | UX Research Methodology| released |     2.1 |
      |  3 | My Draft Playbook      | draft    |     0.3 |
    And playbook id=1 has the following entities:
      | type     | id | name                    | parent_workflow |
      | Workflow | 10 | Component Development   | —               |
      | Workflow | 11 | Testing & Documentation | —               |
      | Activity | 20 | Setup Project           | 10              |
      | Activity | 21 | Create Components       | 10              |
      | Activity | 22 | Component Testing       | 11              |
      | Activity | 23 | Write Documentation     | 11              |
      | Skill    | 30 | React Component Guide   | —               |
      | Agent    | 40 | Cautious Developer      | —               |

  # ============================================================================
  # ENTRY POINTS
  # ============================================================================

  Scenario: FOB-PIP-CREATE-01 Open PIP creation from Released playbook detail
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 for "React Frontend Dev" (id=1)
    When she clicks [Submit PIP]
    Then she is redirected to FOB-PIP-CREATE-1
    And the Target Playbook field is pre-filled with "React Frontend Dev v1.0"
    And the Target Playbook field is locked (read-only)

  Scenario: FOB-PIP-CREATE-02 Open PIP creation from PIPs list
    Given Maria is on FOB-PIP-LIST-1
    When she clicks [+ New PIP]
    Then she is redirected to FOB-PIP-CREATE-1
    And the Target Playbook field is empty (dropdown to select)
    And the dropdown shows only Released playbooks (not drafts)

  Scenario: FOB-PIP-CREATE-03 Draft playbook not available as PIP target
    Given Maria opens FOB-PIP-CREATE-1 from PIPs list
    When she opens the Target Playbook dropdown
    Then she sees "React Frontend Dev v1.0" in the list
    And she sees "UX Research Methodology v2.1" in the list
    And she does NOT see "My Draft Playbook v0.3" (drafts are excluded)

  # ============================================================================
  # FORM VALIDATION
  # ============================================================================

  Scenario: FOB-PIP-CREATE-04 Submit button disabled until title and one Change are present
    Given Maria is on FOB-PIP-CREATE-1 with target "React Frontend Dev"
    And the title field is empty
    And the Change list is empty
    Then the [Submit for Review] button is disabled
    When she enters title "Add Accessibility Audit"
    Then the [Submit for Review] button is still disabled (no Changes yet)
    When she adds one Change
    Then the [Submit for Review] button becomes enabled

  Scenario: FOB-PIP-CREATE-05 Title is required, summary is optional
    Given Maria is on FOB-PIP-CREATE-1
    When she leaves the Title field empty and clicks [Save as Draft]
    Then she sees inline error "Title is required"
    And the PIP is not saved

  # ============================================================================
  # ADDING CHANGES — ADD type
  # ============================================================================

  Scenario: FOB-PIP-CREATE-06 Add an ADD Change — append at end of workflow
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she clicks [+ Add Change]
    And she selects Type "ADD"
    And she selects Entity Type "Activity"
    And she enters Name "Accessibility Audit"
    And she selects Position "Append at end of workflow"
    And she selects Parent Workflow "Testing & Documentation (id=11)"
    And she enters Content "Ensure React components meet WCAG 2.1 AA standards using axe-core and jest-axe."
    And she clicks [Add Change]
    Then Change #1 appears in the Change list:
      | type        | ADD                                    |
      | entity_type | Activity                               |
      | name        | Accessibility Audit                    |
      | position    | Append at end of workflow (id=11)      |
      | content     | Ensure React components meet WCAG 2.1… |

  Scenario: FOB-PIP-CREATE-07 Add an ADD Change — insert after named sibling
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she clicks [+ Add Change]
    And she selects Type "ADD"
    And she selects Entity Type "Activity"
    And she enters Name "Accessibility Audit"
    And she selects Position "After existing activity"
    And she selects sibling "Component Testing (id=22)"
    And she enters Content "Accessibility checks using axe-core."
    And she clicks [Add Change]
    Then Change #1 shows position "After: Component Testing (id=22)"

  Scenario: FOB-PIP-CREATE-08 Add an ADD Change for a Workflow
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she adds a Change:
      | type        | ADD                                           |
      | entity_type | Workflow                                      |
      | name        | Performance Optimisation                      |
      | position    | Append at end of playbook                     |
      | content     | Covers bundle size, lazy loading, and caching |
    Then Change #1 appears in the Change list with entity_type "Workflow"

  # ============================================================================
  # ADDING CHANGES — ALTER type
  # ============================================================================

  Scenario: FOB-PIP-CREATE-09 Add an ALTER Change for an existing Activity
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she clicks [+ Add Change]
    And she selects Type "ALTER"
    And she selects Entity Type "Activity"
    And she selects Target "Component Testing (id=22)"
    And she enters New Content "Add axe-core a11y tests alongside existing Jest unit tests. Fail the build on any a11y violation."
    And she clicks [Add Change]
    Then Change #1 appears in the Change list:
      | type        | ALTER                        |
      | entity_type | Activity                     |
      | target_id   |                           22 |
      | target_name | Component Testing            |
      | content     | Add axe-core a11y tests… |

  Scenario: FOB-PIP-CREATE-10 Add an ALTER Change for a Skill
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she adds a Change:
      | type        | ALTER                                               |
      | entity_type | Skill                                               |
      | target      | React Component Guide (id=30)                       |
      | content     | Add section: "Accessibility first" with code samples |
    Then Change #1 entity_type is "Skill" and target is "React Component Guide (id=30)"

  # ============================================================================
  # ADDING CHANGES — DROP type
  # ============================================================================

  Scenario: FOB-PIP-CREATE-11 Add a DROP Change for an existing Activity
    Given Maria is on FOB-PIP-CREATE-1 targeting "React Frontend Dev v1.0"
    When she clicks [+ Add Change]
    And she selects Type "DROP"
    And she selects Entity Type "Activity"
    And she selects Target "Write Documentation (id=23)"
    And she enters Rationale "Documentation is now auto-generated from code comments; manual activity is redundant."
    And she clicks [Add Change]
    Then Change #1 appears in the Change list:
      | type        | DROP                                    |
      | entity_type | Activity                                |
      | target_id   |                                      23 |
      | target_name | Write Documentation                     |
      | rationale   | Documentation is now auto-generated … |

  # ============================================================================
  # CHANGE LIST MANAGEMENT
  # ============================================================================

  Scenario: FOB-PIP-CREATE-12 Multiple Changes in one PIP — ordered list
    Given Maria has added the following Changes to PIP draft:
      | # | type  | entity_type | name / target           |
      | 1 | ADD   | Activity    | Accessibility Audit     |
      | 2 | ALTER | Activity    | Component Testing (id=22)|
      | 3 | DROP  | Activity    | Write Documentation (id=23) |
    Then the Change list shows 3 entries in order #1, #2, #3

  Scenario: FOB-PIP-CREATE-13 Remove a Change from the list
    Given Maria has Changes #1 (ADD) and #2 (ALTER) in her PIP draft
    When she clicks [Remove] on Change #1
    Then Change list shows only 1 entry (the former #2, now renumbered #1)
    And the PIP has 1 Change

  Scenario: FOB-PIP-CREATE-14 Change requires at minimum a type and entity_type
    Given Maria is adding a Change
    When she selects Type "ADD" and Entity Type "Activity"
    And she leaves Name empty
    And she clicks [Add Change]
    Then she sees inline error "Name is required for ADD changes"
    And the Change is not added to the list

  Scenario: FOB-PIP-CREATE-15 DROP change requires rationale
    Given Maria is adding a DROP Change
    When she leaves the Rationale field empty
    And she clicks [Add Change]
    Then she sees inline error "Rationale is required for DROP changes"

  # ============================================================================
  # PREVIEW DIFF
  # ============================================================================

  Scenario: FOB-PIP-CREATE-16 Preview Diff shows cumulative impact on playbook
    Given Maria has 2 Changes in her PIP draft:
      | # | type  | entity_type | detail                      |
      | 1 | ADD   | Activity    | Accessibility Audit (after 22) |
      | 2 | ALTER | Activity    | Component Testing (id=22)   |
    When she clicks [Preview Diff]
    Then a diff panel opens showing:
      | section              | change_type |
      | Component Testing    | Modified    |
      | Accessibility Audit  | Added       |
    And the diff panel shows the new content for each changed entity

  # ============================================================================
  # SAVE AND SUBMIT
  # ============================================================================

  Scenario: FOB-PIP-CREATE-17 Save as Draft preserves PIP without submitting
    Given Maria has completed the PIP form with 1 Change
    When she clicks [Save as Draft]
    Then PIP is created with status "Draft"
    And Maria is redirected to FOB-PIP-DETAIL-1 for the new PIP
    And the PIP does NOT appear in Galdr's processing queue
    And the breadcrumb shows "PIPs > Add Accessibility Audit"

  Scenario: FOB-PIP-CREATE-18 Submit for Review triggers Galdr processing
    Given Maria has completed the PIP form with 1 ADD Change
    When she clicks [Submit for Review]
    Then PIP is created with status "Submitted"
    And within seconds the status transitions to "Processing (Galdr)"
    And Maria is redirected to FOB-PIP-DETAIL-1 showing status "Processing (Galdr)"
    And a FOB notification is created: "PIP 'Add Accessibility Audit' submitted — Galdr is reviewing your changes."

  Scenario: FOB-PIP-CREATE-19 Cancel returns to PIPs list without saving
    Given Maria is on FOB-PIP-CREATE-1 with unsaved changes
    When she clicks [Cancel]
    Then a confirmation modal appears: "Cancel this PIP?"
    When she clicks [Cancel]
    Then she is redirected to FOB-PIP-LIST-1
    And no PIP was created
