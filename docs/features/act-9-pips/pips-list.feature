Feature: FOB-PIP-LIST-1 View and Filter PIPs
  As a methodology author (Maria)
  I want to view all my PIPs and filter by status
  So that I can track which change requests are pending, accepted, or rejected

  Status: 🔲 TODO
  Related: act-9-pips/pips-create.feature, act-9-pips/pips-view.feature

  Background:
    Given Maria is authenticated in FOB
    And the following PIPs exist for user "maria":
      | id | title                        | target_playbook            | changes | status              | submitted_at | status_changed_at |
      | 42 | Add Accessibility Audit      | React Frontend Dev (id=1)  |       1 | Reviewed            | 2026-05-14   | 2026-05-15        |
      | 38 | State Management Patterns    | React Frontend Dev (id=1)  |       2 | Accepted            | 2026-04-20   | 2026-04-22        |
      | 35 | Drop Legacy IE Support       | React Frontend Dev (id=1)  |       1 | Rejected            | 2026-04-10   | 2026-04-11        |
      | 30 | Add Figma Integration        | UX Research (id=2)         |       3 | Draft               | 2026-03-05   | 2026-03-05        |
      | 28 | Improve Onboarding Flow      | UX Research (id=2)         |       1 | Submitted           | 2026-03-01   | 2026-03-01        |
      | 27 | Rename Discovery Activity    | UX Research (id=2)         |       1 | Processing (Galdr)  | 2026-02-28   | 2026-02-28        |

  # ============================================================================
  # NAVIGATION
  # ============================================================================

  Scenario: FOB-PIP-LIST-01 Navigate to PIPs list from top nav
    Given Maria is on any page in FOB
    When she clicks "PIPs" in the top navigation bar
    Then she is redirected to FOB-PIP-LIST-1
    And the page header shows "PIPs (6)"
    And the "PIPs" nav item is highlighted as active
    And the count pill on the PIPs nav item is cleared to 0

  Scenario: FOB-PIP-LIST-02 Count pill shows new status changes since last visit
    Given Maria last visited FOB-PIP-LIST-1 at "2026-05-14T10:00:00"
    And PIP-42 moved to status "Reviewed" at "2026-05-15T08:00:00"
    And PIP-38 moved to status "Accepted" at "2026-05-14T09:00:00"
    When Maria views any page in FOB before opening the PIPs list
    Then the PIPs nav item shows count pill "2"
    When she opens FOB-PIP-LIST-1
    Then the count pill disappears (resets to 0)
    And "status_changed_since_last_view" is False for all PIPs

  Scenario: FOB-PIP-LIST-03 Count pill resets after list_pips MCP call
    Given the PIPs nav count pill shows "1" for Maria
    When her AI assistant calls MCP tool "list_pips"
    Then "status_changed_since_last_view" is reset for all returned PIPs
    And the PIPs nav count pill shows "0" on next page load

  # ============================================================================
  # LIST DISPLAY
  # ============================================================================

  Scenario: FOB-PIP-LIST-04 Default view shows My PIPs tab
    Given Maria navigates to FOB-PIP-LIST-1
    Then she sees the "My PIPs" tab selected by default
    And she sees 6 rows in the table
    And each row shows: PIP ID, Title, Target Playbook, Changes count, Status badge, Submitted date, Last Updated date, Actions dropdown

  Scenario: FOB-PIP-LIST-05 Status badges have correct colours
    Given Maria is on FOB-PIP-LIST-1 with no filters
    Then PIP-42 row shows status badge "Reviewed" in purple
    And PIP-38 row shows status badge "Accepted" in green
    And PIP-35 row shows status badge "Rejected" in red
    And PIP-30 row shows status badge "Draft" in gray
    And PIP-28 row shows status badge "Submitted" in blue
    And PIP-27 row shows status badge "Processing (Galdr)" in yellow

  Scenario: FOB-PIP-LIST-06 Blue dot appears on rows changed since last view
    Given Maria's last_viewed_at is "2026-05-14T10:00:00"
    And PIP-42 "status_changed_at" is "2026-05-15T08:00:00" (after last view)
    And PIP-38 "status_changed_at" is "2026-04-22T12:00:00" (before last view)
    When Maria opens FOB-PIP-LIST-1
    Then PIP-42 row shows a blue dot indicator
    And PIP-38 row has no blue dot indicator

  Scenario: FOB-PIP-LIST-07 Row actions available based on status
    Given Maria is on FOB-PIP-LIST-1
    Then PIP-30 (Draft) row actions dropdown shows: View, Edit, Cancel
    And PIP-28 (Submitted) row actions dropdown shows: View, Cancel
    And PIP-42 (Reviewed) row actions dropdown shows: View only
    And PIP-38 (Accepted) row actions dropdown shows: View only
    And PIP-35 (Rejected) row actions dropdown shows: View only

  # ============================================================================
  # FILTERS
  # ============================================================================

  Scenario: FOB-PIP-LIST-08 Filter by single status — Reviewed
    Given Maria is on FOB-PIP-LIST-1
    When she selects "Reviewed" in the Status filter
    Then she sees 1 row: PIP-42
    And the table header shows "PIPs (1)"

  Scenario: FOB-PIP-LIST-09 Filter by multiple statuses — Draft and Submitted
    Given Maria is on FOB-PIP-LIST-1
    When she selects "Draft" and "Submitted" in the Status filter
    Then she sees 2 rows: PIP-30 and PIP-28
    And the table header shows "PIPs (2)"

  Scenario: FOB-PIP-LIST-10 Filter by target playbook
    Given Maria is on FOB-PIP-LIST-1
    When she selects "UX Research (id=2)" from the Target Playbook dropdown
    Then she sees 3 rows: PIP-30, PIP-28, PIP-27
    And PIPs targeting React Frontend Dev are hidden

  Scenario: FOB-PIP-LIST-11 Filter by Accepted shows accepted PIPs only
    Given Maria is on FOB-PIP-LIST-1
    When she selects "Accepted" in the Status filter
    Then she sees 1 row: PIP-38 "State Management Patterns"
    And the row shows status badge "Accepted" in green

  Scenario: FOB-PIP-LIST-12 Filter by Rejected shows rejected PIPs only
    Given Maria is on FOB-PIP-LIST-1
    When she selects "Rejected" in the Status filter
    Then she sees 1 row: PIP-35 "Drop Legacy IE Support"
    And the row shows status badge "Rejected" in red

  Scenario: FOB-PIP-LIST-13 Clear filters restores full list
    Given Maria has filtered by "Reviewed"
    When she clicks [Clear Filters]
    Then she sees all 6 rows
    And the Status filter shows all options unselected

  Scenario: FOB-PIP-LIST-14 Combine status and playbook filters
    Given Maria is on FOB-PIP-LIST-1
    When she selects status "Draft" and playbook "UX Research (id=2)"
    Then she sees 1 row: PIP-30 "Add Figma Integration"

  # ============================================================================
  # NAVIGATION FROM LIST
  # ============================================================================

  Scenario: FOB-PIP-LIST-15 Click View navigates to PIP detail
    Given Maria is on FOB-PIP-LIST-1
    When she clicks [View] on PIP-42
    Then she is redirected to FOB-PIP-DETAIL-1 for PIP-42
    And the breadcrumb shows "PIPs > Add Accessibility Audit"

  Scenario: FOB-PIP-LIST-16 Click Edit on Draft navigates to edit screen
    Given Maria is on FOB-PIP-LIST-1
    When she clicks [Edit] on PIP-30 (Draft)
    Then she is redirected to FOB-PIP-EDIT-1 for PIP-30

  Scenario: FOB-PIP-LIST-17 Create new PIP button appears on list
    Given Maria is on FOB-PIP-LIST-1
    Then she sees a [+ New PIP] button in the page header
    When she clicks [+ New PIP]
    Then she is redirected to FOB-PIP-CREATE-1

  # ============================================================================
  # EMPTY STATES
  # ============================================================================

  Scenario: FOB-PIP-LIST-18 Empty state when no PIPs exist
    Given Maria has no PIPs at all
    When she navigates to FOB-PIP-LIST-1
    Then she sees the message "You haven't submitted any PIPs yet."
    And she sees subtext "Find a Released playbook you'd like to improve and click [Submit PIP]."
    And the PIPs nav item shows no count pill

  Scenario: FOB-PIP-LIST-19 Empty state when filter returns no results
    Given Maria is on FOB-PIP-LIST-1
    When she selects "Processing (Galdr)" in the Status filter
    And there are no PIPs in that status
    Then she sees "No PIPs match the selected filters."
    And she sees [Clear Filters] button

  # ============================================================================
  # ADMIN ALL PIPs TAB
  # ============================================================================

  Scenario: FOB-PIP-LIST-20 Admin sees All PIPs tab
    Given user "mike" has the Administrator role in FOB
    And 10 PIPs exist across all users (maria=6, alex=4)
    When Mike navigates to FOB-PIP-LIST-1
    Then he sees both "My PIPs" and "All PIPs" tabs
    When he clicks "All PIPs"
    Then he sees all 10 PIPs with a "Submitted by" column showing submitter name

  Scenario: FOB-PIP-LIST-21 Non-admin does not see All PIPs tab
    Given Maria does not have the Administrator role
    When she navigates to FOB-PIP-LIST-1
    Then she sees only the "My PIPs" tab
    And there is no "All PIPs" tab visible
