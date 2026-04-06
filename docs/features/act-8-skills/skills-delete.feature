Feature: FOB-SKILLS-DELETE_SKILL-1 Delete Skill
  As a methodology author (Maria)
  I want to delete skills
  So that I can remove obsolete or replaced guidance

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has skill "Legacy Form Guide"
    And the skill has capability_domain "GUI_FORM" and technology_stack "jQuery"

  Scenario: FOB-SKILLS-DELETE_SKILL-01 Open delete confirmation
    Given Maria is on skills list
    When she clicks [Delete] for "Legacy Form Guide"
    Then the FOB-SKILLS-DELETE_SKILL-1 modal appears
    And it shows "Delete Skill?"

  Scenario: FOB-SKILLS-DELETE_SKILL-02 Modal shows skill details and metadata
    Given the delete modal is open
    Then it displays skill title "Legacy Form Guide"
    And it shows Capability Domain "GUI_FORM"
    And it shows Technology Stack "jQuery"
    And it shows warning about referenced activities

  Scenario: FOB-SKILLS-DELETE_SKILL-03 Warning about referenced activities
    Given 5 activities reference this skill
    Then the modal shows "Referenced by 5 activities"
    And it lists the first 5 activity names
    And it shows "These activities will have their skill reference cleared"

  Scenario: FOB-SKILLS-DELETE_SKILL-04 Confirm deletion
    Given the delete modal is open
    When she clicks [Delete Skill]
    Then the skill is deleted
    And all referencing activities have their skill FK set to NULL
    And she sees success notification
    And she is redirected to FOB-SKILLS-LIST+FIND-1

  Scenario: FOB-SKILLS-DELETE_SKILL-05 Cancel deletion
    Given the delete modal is open
    When she clicks [Cancel]
    Then the modal closes
    And the skill is not deleted
