Feature: FOB-WORKFLOWS-RULES-1 Rules CRUDLF (playbook-scoped)
  As a methodology author (Maria)
  I want to manage IDE-style rules for a playbook
  So that activities can reuse the same guidance and export includes .mdc files

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v0.5"

  Scenario: RULES-01 Global rules list
    When Maria opens the Rules entry in the navbar
    Then she sees rules for her owned playbooks
    And each row links to rule detail within its playbook

  Scenario: RULES-02 Playbook rules list
    Given Maria opens playbook Rules from playbook context
    Then she sees rules for that playbook
    And she can create a new rule when the playbook is editable

  Scenario: RULES-03 Create and view rule
    When Maria creates rule "pytest-first" with content
    Then she sees rule detail with title and slug
    And she sees linked activities count
