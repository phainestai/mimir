Feature: FOB-DASHBOARD-1 Dashboard and Navigation
  As a methodology author (Maria)
  I want to navigate FOB efficiently
  So that I can access my work quickly

  Background:
    Given Maria is authenticated in FOB
    And she is on FOB-DASHBOARD-1

  Scenario: FOB-DASHBOARD-01 View dashboard overview
    Given Maria is on the dashboard
    Then she sees "My Playbooks" section with 5 most recently accessed playbooks
    And she sees "Recently Used" section showing last 10 accessed items (Playbooks/Workflows/Activities) with usage counts
    And she sees quick action buttons for Create/Import/Sync

  Scenario: FOB-DASHBOARD-02 Recently Used section shows usage statistics
    Given Maria is on the dashboard
    And she has accessed "React Frontend Development" playbook 15 times
    And she last accessed it 2 hours ago
    When she views the "Recently Used" section
    Then she sees "React Frontend Development" | Playbook | "15 times" | "2 hours ago"
    And she sees a [View] button to quickly navigate to it

  Scenario: FOB-DASHBOARD-03 Recently Used tracks only views, not edits
    Given Maria is on the dashboard
    When she views the "Recently Used" section
    Then it shows items she has VIEWED/ACCESSED
    And it does NOT show create/update/delete operations
    And it is NOT an audit trail or activity log

  Scenario: FOB-DASHBOARD-04 Navigate to Playbooks
    Given Maria is on the dashboard
    When she clicks "Playbooks" in main navigation
    Then she is redirected to FOB-PLAYBOOKS-LIST+FIND-1

  Scenario: FOB-DASHBOARD-05 Quick create playbook
    Given Maria is on the dashboard
    When she clicks [+ New Playbook] quick action
    Then she is redirected to FOB-PLAYBOOKS-CREATE_PLAYBOOK-1

  Scenario: FOB-DASHBOARD-06 View recent playbook
    Given Maria sees recent playbooks on dashboard
    When she clicks a recent playbook
    Then she is redirected to that playbook's view page

  Scenario: FOB-DASHBOARD-07 Access settings
    Given Maria is on the dashboard
    When she clicks her profile menu
    And she clicks [Settings]
    Then she is redirected to FOB-SETTINGS-1

  Scenario: FOB-DASHBOARD-08 Global search
    Given Maria is anywhere in FOB
    When she uses global search for "Component"
    Then she sees results across: Playbooks, Workflows, Activities
    And she can navigate to any result
