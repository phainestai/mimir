Feature: FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 View Playbook Details
  As a methodology author (Maria)
  I want to view complete playbook details
  So that I can understand the methodology structure and content

  Background:
    Given Maria is authenticated in FOB
    And the playbook "React Frontend Development" exists with:
      | field      | value                  |
      | author     | Mike Chen              |
      | version    | v1.2                   |
      | status     | Active                 |
      | source     | Downloaded (Usability) |
      | workflows  |                      3 |
      | activities |                     24 |
      | artifacts  |                     12 |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-01 Open playbook detail page
    Given Maria is on FOB-PLAYBOOKS-LIST+FIND-1
    And "React Frontend Development" is in the list
    When she clicks [View] in the Actions menu
    Then she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And she sees the playbook detail page
    And the breadcrumb shows "Playbooks > React Frontend Development > Overview"

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-02 View header information
    Given Maria is on the playbook detail page for "React Frontend Development"
    Then the header displays:
      | element       | value                        |
      | Name          | React Frontend Development   |
      | Version badge | v1.2                         |
      | Status badge  | Active (green)               |
      | Author        | Mike Chen (Usability family) |
      | Last modified |                  2 weeks ago |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-03 View Overview tab content (default)
    Given Maria is on the playbook detail page
    Then the Overview tab is selected by default
    And she sees the full playbook description
    And she sees Quick Stats Card with:
      | stat       | count              |
      | Workflows  |                  3 |
      | Phases     |                  8 |
      | Activities |                 24 |
      | Artifacts  |                 12 |
      | Roles      |                  5 |
      | Howtos     |                 24 |
      | Goals      | Coming soon (v2.1) |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-04 View metadata in Overview
    Given Maria is on the Overview tab
    Then she sees Metadata section with:
      | field    | value                                   |
      | Category | Development                             |
      | Tags     | react, frontend, component-architecture |
      | Created  |                            3 months ago |
      | Source   | Downloaded from Usability family        |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-05 View workflows list in Overview ✅ IMPLEMENTED
    Given Maria is on the Overview tab
    Then she sees Workflows Section
    And each workflow displays: Name, Description, Activity count
    And she sees [View Workflow] link for each workflow
    When she clicks [View Workflow] on "Component Design"
    Then she navigates to ACT 3: WORKFLOWS detail page
    # Implemented: Workflows shown with name, description, order badge
    # Clickable links to workflow detail pages
    # Quick edit button for each workflow

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-06 Navigate to Workflows tab ✅ IMPLEMENTED
    Given Maria is on the playbook detail page
    When she clicks the "Workflows" tab
    Then she sees the full list of workflows
    And workflows show dependency visualization (if any)
    And she sees workflow filtering options
    # Implemented: Workflows tab with embedded workflows list
    # Client-side filtering by name (search) and phase presence
    # Activity dependencies shown in individual workflow detail pages
    # 13 integration tests covering all aspects
    # Empty states for no workflows and filtered results

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-07 Add workflow button (editable playbooks only) ✅ IMPLEMENTED
    Given Maria owns the playbook "Product Discovery Framework"
    And she is on the Workflows tab
    Then she sees [Add Workflow] button
    When she is viewing a downloaded playbook "React Frontend Development"
    And she is on the Workflows tab
    Then the [Add Workflow] button is not visible
    # Implemented: Add Workflow + Manage buttons in workflows section
    # Only visible if can_edit (owned playbooks)
    # Empty state with 'Create First Workflow' button

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-08 Navigate to History tab
    Given Maria is on the playbook detail page
    When she clicks the "History" tab
    Then she sees the version timeline
    And versions are listed: v1.0, v1.1, v1.2
    And each version shows:
      | field          |
      | Version number |
      | Date           |
      | Author         |
      | Change summary |
    And each version has [View This Version] and [Compare with Current] buttons

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-09 View specific version from History
    Given Maria is on the History tab
    When she clicks [View This Version] for v1.0
    Then she sees the playbook as it was in v1.0
    And a notice displays "You are viewing version v1.0 (not current)"
    And she sees [Return to Current Version] button

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-10 Compare versions
    Given Maria is on the History tab
    When she clicks [Compare with Current] for v1.0
    Then she sees the Version Comparison View
    And the view shows split-pane diff viewer
    And left pane shows "Version v1.0"
    And right pane shows "Current (v1.2)"
    And differences are highlighted:
      | color  | meaning  |
      | green  | Added    |
      | red    | Removed  |
      | yellow | Modified |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-11 View PIP history in History tab
    Given Maria is on the History tab
    Then she sees "PIP History" section
    And PIPs that led to new versions are listed
    And each PIP shows: Title, Submitter, Status, Related version

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-12 Navigate to Settings tab (owned playbooks only)
    Given Maria owns the playbook "Product Discovery Framework"
    And she is on the playbook detail page
    When she clicks the "Settings" tab
    Then she sees Settings tab content:
      | section             |
      | Visibility settings |
      | Publishing settings |
      | Sharing options     |
      | Transfer Ownership  |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-13 Settings tab not visible for downloaded playbooks
    Given Maria is viewing downloaded playbook "React Frontend Development"
    Then the "Settings" tab is not visible
    And only tabs shown are: Overview, Workflows, History

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-14 Top actions for owned playbooks
    Given Maria owns the playbook "Product Discovery Framework"
    And she is on the playbook detail page
    Then she sees top action buttons:
      | button         |
      | Edit           |
      | Delete         |
      | Export JSON    |
      | Duplicate      |
      | Disable/Enable |
      | ...More        |

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-15 Top actions for downloaded playbooks
    Given Maria is viewing downloaded playbook "React Frontend Development"
    Then she sees limited action buttons:
      | button    |
      | Duplicate |
      | ...More   |
    And Edit, Delete, Export JSON buttons are not visible

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-16 Click Edit button ✅ IMPLEMENTED
    Given Maria owns the playbook
    And she is on the playbook detail page
    When she clicks [Edit]
    Then she is redirected to FOB-PLAYBOOKS-EDIT_PLAYBOOK-1
    And she sees the edit form pre-populated
    # Implemented: Edit button in header (if can_edit)
    # Full edit form with all fields pre-populated
    # Tests: 11 integration tests passing

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-17 Click Delete button
    Given Maria owns the playbook
    And she is on the playbook detail page
    When she clicks [Delete]
    Then the FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 modal appears
    And she sees deletion confirmation

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-18 Export playbook to JSON ✅ IMPLEMENTED
    Given Maria owns the playbook "Product Discovery Framework"
    And she is on the playbook detail page
    When she clicks [Export JSON]
    Then a file download is triggered
    And the file is named "product-discovery-framework-v1.0.json"
    # Implemented: playbook_export view
    # JSON download with metadata
    # Filename format: name-vX.json

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-19 Duplicate playbook ✅ IMPLEMENTED
    Given Maria is on the playbook detail page
    When she clicks [Duplicate]
    Then a modal appears "Duplicate playbook?"
    And she can enter a new name
    When she enters "React Frontend Development (My Copy)" and confirms
    Then a new local playbook is created
    And she is redirected to the new playbook's detail page
    # Implemented: playbook_duplicate view
    # Creates shallow copy (metadata only)
    # Sets source='owned', status='draft'

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-20 Disable/Enable toggle ✅ IMPLEMENTED
    Given Maria owns an Active playbook
    And she is on the playbook detail page
    When she clicks [Disable]
    Then a confirmation modal appears
    When she confirms
    Then the playbook status changes to "Disabled"
    And the status badge updates to gray
    And the button changes to [Enable]
    # Implemented: playbook_toggle_status view
    # Toggles active <-> disabled
    # Draft status stays draft

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-21 Back to playbooks list
    Given Maria is on the playbook detail page
    When she clicks [Back to Playbooks List] link
    Then she returns to FOB-PLAYBOOKS-LIST+FIND-1

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-22 Breadcrumb navigation
    Given Maria is on the playbook detail page
    And the breadcrumb shows "Playbooks > React Frontend Development > Overview"
    When she clicks "Playbooks" in the breadcrumb
    Then she returns to FOB-PLAYBOOKS-LIST+FIND-1

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-23 View playbook with optional Phases
    Given Maria is viewing a playbook with optional Phases
    Then the Quick Stats shows Phases count: 8
    When she is viewing a playbook without Phases
    Then the Quick Stats shows Phases: "N/A" or "0"

  Scenario: FOB-PLAYBOOKS-VIEW_PLAYBOOK-24 Status badge colors
    Given Maria views playbooks with different statuses
    Then she sees status badges with correct colors:
      | status   | color  |
      | Active   | green  |
      | Disabled | gray   |
      | Draft    | yellow |
# =============================================================================
# IMPLEMENTATION STATUS (as of 2025-11-28)
# =============================================================================
#
# COMPLETED SCENARIOS:
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-05: Workflows list in Overview ✅
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-07: Add workflow button ✅
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-16: Edit button ✅
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-18: Export to JSON ✅
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-19: Duplicate playbook ✅
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-20: Toggle status ✅
#
# INTEGRATION ENHANCEMENTS (Not in original spec):
# - Workflows are clickable (link to workflow_detail)
# - Quick edit button on each workflow
# - "Manage" button to go to full workflow list
# - Empty state with "Create First Workflow" button
# - Workflow order badges (#1, #2, etc.)
# - Global workflows overview accessible from navbar
#
# TESTS:
# - Playbook EDIT: 11 integration tests ✅
# - Playbook VIEW Phase 1: 9 tests ✅
# - Playbook VIEW Phase 2: 5 tests ✅
# - Workflows CRUDV: 40 tests ✅
#
# MISSING TESTS:
# ⚠️  No playbook LIST tests found!
# ⚠️  Should implement tests from playbooks-list-find.feature
#
# DEFERRED SCENARIOS (Future Implementation):
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-03: Quick Stats (phases, activities, artifacts, roles counts)
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-04: Tags display
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-06: Workflows tab (separate from Overview)
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-08-11: History tab and version comparison
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-12-13: Settings tab
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-17: Delete button (Issue #31)
# - FOB-PLAYBOOKS-VIEW_PLAYBOOK-23: Phases integration (when Phase model exists)
#
