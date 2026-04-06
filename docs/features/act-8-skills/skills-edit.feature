Feature: FOB-SKILLS-EDIT_SKILL-1 Edit Skill
  As a methodology author (Maria)
  I want to edit skill details including capability and tech stack metadata
  So that I can keep guidance documentation accurate and properly categorized

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has skill "React Form Component"
    And the skill has capability_domain "GUI_FORM" and technology_stack "React+Redux"

  Scenario: FOB-SKILLS-EDIT_SKILL-01 Open edit form with all fields pre-populated
    Given Maria is viewing the skill on FOB-SKILLS-VIEW_SKILL-1
    When she clicks [Edit Skill]
    Then she is redirected to FOB-SKILLS-EDIT_SKILL-1
    And Title is pre-populated with "React Form Component"
    And Capability Domain is pre-populated with "GUI_FORM"
    And Technology Stack is pre-populated with "React+Redux"
    And Content is pre-populated with existing Markdown

  Scenario: FOB-SKILLS-EDIT_SKILL-02 Edit skill title
    Given Maria is on the edit form
    When she changes Title to "Advanced React Form Component"
    And she clicks [Save Changes]
    Then the skill title is updated
    And she sees success notification

  Scenario: FOB-SKILLS-EDIT_SKILL-03 Edit capability domain and technology stack
    Given Maria is on the edit form
    When she changes Capability Domain to "GUI_WIZARD"
    And she changes Technology Stack to "React+MUI"
    And she clicks [Save Changes]
    Then capability_domain and technology_stack are updated
    And autocomplete suggestions include the new values for future skills

  Scenario: FOB-SKILLS-EDIT_SKILL-04 Edit skill content
    Given Maria is on the edit form
    When she updates the Content in Markdown editor
    And she clicks [Save Changes]
    Then the content is updated

  Scenario: FOB-SKILLS-EDIT_SKILL-05 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then changes are discarded
