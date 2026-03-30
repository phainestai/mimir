Feature: FOB-PLAYBOOKS-LIST+FIND-1 Playbooks List and Search
  As a methodology author (Maria)
  I want to view, search, and filter my playbooks
  So that I can quickly find and manage methodologies I need

  Background:
    Given Maria is authenticated in FOB
    And she is on the FOB Dashboard

  Scenario: FOB-PLAYBOOKS-LIST+FIND-01 View playbooks list with existing playbooks
    Given Maria has 3 playbooks in her FOB:
      | name                       | author          | version | status   | source     |
      | React Frontend Development | Mike Chen       | v1.2    | Active   | Downloaded |
      | UX Research Methodology    | Maria Rodriguez | v2.1    | Active   | Owned      |
      | Design System Patterns     | Community       | v1.0    | Disabled | Downloaded |
    When she clicks "Playbooks" in the main navigation
    Then she sees the playbooks list page
    And the header shows "Playbooks (3)"
    And she sees all 3 playbooks in the table
    And each playbook row shows: Name, Description, Author, Version, Status, Last Modified, Actions

  Scenario: FOB-PLAYBOOKS-LIST+FIND-02 Navigate to create new playbook
    Given Maria is on the playbooks list page
    When she clicks the [Create New Playbook] button
    Then she is redirected to FOB-PLAYBOOKS-CREATE_PLAYBOOK-1
    And she sees the playbook creation wizard

  Scenario: FOB-PLAYBOOKS-LIST+FIND-03 Search playbooks by name
    Given Maria is on the playbooks list page
    And she has playbooks including "React Frontend Development"
    When she enters "React" in the search box
    Then she sees only playbooks matching "React" in name, description, or author
    And "React Frontend Development" appears in the results
    And unmatched playbooks are hidden

  Scenario: FOB-PLAYBOOKS-LIST+FIND-04 Search with no results
    Given Maria is on the playbooks list page
    When she enters "NonExistentPlaybook" in the search box
    Then she sees "No playbooks found matching 'NonExistentPlaybook'"
    And she sees a [Clear Search] button
    And the playbooks table is empty

  Scenario: FOB-PLAYBOOKS-LIST+FIND-05 Filter playbooks by status
    Given Maria is on the playbooks list page
    And she has both Active and Disabled playbooks
    When she selects "Active" from the Status filter
    Then she sees only Active playbooks
    And Disabled playbooks are hidden
    And the filter badge shows "Status: Active"

  Scenario Outline: FOB-PLAYBOOKS-LIST+FIND-06 Filter playbooks by source
    Given Maria is on the playbooks list page
    And she has playbooks from different sources
    When she selects "<source>" from the Source filter
    Then she sees only "<source>" playbooks
    And the filter badge shows "Source: <source>"

    Examples:
      | source     |
      | Local      |
      | Downloaded |
      | Owned      |

  Scenario: FOB-PLAYBOOKS-LIST+FIND-07 Filter playbooks by category
    Given Maria is on the playbooks list page
    And she has playbooks in categories: Design, Development, Research
    When she selects "Design" from the Category filter
    Then she sees only Design category playbooks
    And other categories are hidden
    And the filter badge shows "Category: Design"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-08 Clear all filters
    Given Maria is on the playbooks list page
    And she has applied Status filter "Active"
    And she has applied Source filter "Owned"
    When she clicks [Clear Filters]
    Then all filters are removed
    And she sees all playbooks regardless of status or source
    And no filter badges are displayed

  Scenario: FOB-PLAYBOOKS-LIST+FIND-09 Sort playbooks by column
    Given Maria is on the playbooks list page
    And she has multiple playbooks
    When she clicks the "Name" column header
    Then playbooks are sorted alphabetically by name (ascending)
    When she clicks the "Name" column header again
    Then playbooks are sorted reverse alphabetically by name (descending)
    And a sort indicator appears on the "Name" column

  Scenario Outline: FOB-PLAYBOOKS-LIST+FIND-10 Sort by different columns
    Given Maria is on the playbooks list page
    When she clicks the "<column>" column header
    Then playbooks are sorted by "<column>" in ascending order

    Examples:
      | column        |
      | Author        |
      | Version       |
      | Status        |
      | Last Modified |

  Scenario: FOB-PLAYBOOKS-LIST+FIND-11 Navigate to view playbook details
    Given Maria is on the playbooks list page
    And "React Frontend Development" is in the list
    When she clicks [View] in the Actions menu for "React Frontend Development"
    Then she is redirected to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    And she sees the playbook detail page for "React Frontend Development"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-12 Navigate to edit playbook
    Given Maria is on the playbooks list page
    And "UX Research Methodology" is in the list
    And Maria is the author of "UX Research Methodology"
    When she clicks [Edit] in the Actions menu for "UX Research Methodology"
    Then she is redirected to FOB-PLAYBOOKS-EDIT_PLAYBOOK-1
    And she sees the edit form pre-populated with playbook data

  Scenario: FOB-PLAYBOOKS-LIST+FIND-13 Open delete playbook confirmation
    Given Maria is on the playbooks list page
    And "Design System Patterns" is in the list
    When she clicks [Delete] in the Actions menu for "Design System Patterns"
    Then the FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 modal appears
    And the modal shows "Delete Playbook?"
    And the modal shows playbook details for "Design System Patterns"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-14 Export playbook to JSON (owned playbooks only)
    Given Maria is on the playbooks list page
    And "UX Research Methodology" is owned by Maria
    When she clicks [Export JSON] in the Actions menu for "UX Research Methodology"
    Then a file download is triggered
    And the file is named "ux-research-methodology-v2.1.json"
    And the file contains the complete playbook data in JSON format

  Scenario: FOB-PLAYBOOKS-LIST+FIND-15 Export not available for downloaded playbooks
    Given Maria is on the playbooks list page
    And "React Frontend Development" is a downloaded playbook
    When she opens the Actions menu for "React Frontend Development"
    Then the [Export JSON] option is disabled or hidden
    And a tooltip explains "Only owned playbooks can be exported"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-16 Import playbook from JSON
    Given Maria is on the playbooks list page
    When she clicks [Import from JSON]
    Then the import modal appears
    And she sees a file upload area "Drop JSON file here or click to browse"
    And she sees accepted format ".json files only"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-17 Sync with Homebase (when connected)
    Given Maria is on the playbooks list page
    And Maria is connected to Homebase
    When she clicks [Sync with Homebase]
    Then the sync operation starts
    And she sees "Checking for updates..." status
    And available playbooks from her families are listed

  Scenario: FOB-PLAYBOOKS-LIST+FIND-18 Sync disabled when not connected to Homebase
    Given Maria is on the playbooks list page
    And Maria is NOT connected to Homebase
    Then the [Sync with Homebase] button is disabled
    And hovering shows tooltip "Connect to Homebase in Settings to enable sync"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-19 Empty state display for new users
    Given Maria is on the playbooks list page
    And Maria has zero playbooks
    Then she sees an empty bookshelf illustration
    And she sees "No playbooks yet"
    And she sees "Create your first playbook, download from Homebase, or import from JSON"
    And she sees three action buttons:
      | button          |
      | Create Playbook |
      | Browse Families |
      | Import JSON     |

  Scenario: FOB-PLAYBOOKS-LIST+FIND-20 Pagination with many playbooks
    Given Maria is on the playbooks list page
    And Maria has 45 playbooks
    When the page loads
    Then she sees the first 20 playbooks
    And she sees pagination controls at the bottom
    And the controls show "Page 1 of 3"
    When she clicks "Next Page"
    Then she sees playbooks 21-40
    And the controls show "Page 2 of 3"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-21 Combine search and filter
    Given Maria is on the playbooks list page
    And she has multiple playbooks
    When she enters "Frontend" in the search box
    And she selects "Active" from the Status filter
    Then she sees only Active playbooks with "Frontend" in name/description/author
    And both search term and filter badge are displayed
    And results match both criteria

  Scenario: FOB-PLAYBOOKS-LIST+FIND-22 Row hover shows action menu
    Given Maria is on the playbooks list page
    And "React Frontend Development" is in the list
    When she hovers over the "React Frontend Development" row
    Then the row is highlighted
    And the Actions dropdown menu icon becomes visible
    When she clicks the Actions dropdown
    Then she sees the action menu with options: View, Edit, Delete, Export JSON, More
  # ============================================================
  # NAVBAR INTEGRATION - Wire when Playbooks block is complete
  # ============================================================

  Scenario: FOB-PLAYBOOKS-LIST+FIND-23 Playbooks link appears in main navigation
    Given the Playbooks feature is fully implemented
    And Maria is authenticated in FOB
    When she views any page in FOB
    Then she sees "Playbooks" link in the main navbar
    And the link has icon "fa-book-sparkles"
    And the link has tooltip "Browse and manage your engineering playbooks"

  Scenario: FOB-PLAYBOOKS-LIST+FIND-24 Navigate to Playbooks from any page
    Given Maria is authenticated in FOB
    And she is on any page in FOB
    When she clicks "Playbooks" in the main navbar
    Then she is redirected to FOB-PLAYBOOKS-LIST+FIND-1
    And the Playbooks nav link is highlighted as active
