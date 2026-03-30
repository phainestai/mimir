Feature: FOB-SYNC-1 Sync Playbooks with Family
  As a methodology author (Maria)
  I want to sync playbooks with family members
  So that we stay in sync with latest changes

  Background:
    Given Maria and Mike are in same family
    And Maria has FOB installed locally

  Scenario: FOB-SYNC-01 Clean download from Mike
    Given Mike has a playbook Maria doesn't have
    When Maria clicks [Sync]
    Then she sees Mike's playbook available
    When she clicks [Download]
    Then playbook is downloaded to her FOB

  Scenario: FOB-SYNC-02 Clean upload to Mike
    Given Maria has a new playbook
    When she clicks [Share] > [Share with Family]
    Then Mike sees the playbook in his sync list
    And he can download it

  Scenario: FOB-SYNC-03 Conflict detection
    Given both Maria and Mike edited same playbook
    When Maria syncs
    Then she sees conflict warning
    And she can choose: Keep Mine, Take Theirs, or Merge

  Scenario: FOB-SYNC-04 Merge conflicts
    Given Maria has conflicts
    When she selects [Merge]
    Then she sees side-by-side comparison
    And she can select which changes to keep

  Scenario: FOB-SYNC-05 Sync status indicator
    Given Maria is on dashboard
    Then she sees sync status: Up to date, Changes pending, or Conflicts

  Scenario: FOB-SYNC-06 Auto-sync setting
    Given Maria enables auto-sync
    Then playbooks automatically sync every hour
    And she gets notifications of changes
