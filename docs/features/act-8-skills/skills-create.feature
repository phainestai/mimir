Feature: FOB-SKILLS-CREATE_SKILL-1 Create Skill
  As a methodology author (Maria)
  I want to create reusable, tech-specific skills within a playbook
  So that activities can reference them for step-by-step guidance

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"

  Scenario: FOB-SKILLS-CREATE_SKILL-01 Open create skill form from playbook
    Given Maria is on FOB-SKILLS-LIST+FIND-1 for playbook "React Frontend v1.2"
    When she clicks [Create New Skill]
    Then she is redirected to FOB-SKILLS-CREATE_SKILL-1
    And the form shows "Create Skill in React Frontend v1.2"

  Scenario: FOB-SKILLS-CREATE_SKILL-02 Create skill with all fields
    Given Maria is on the create skill form
    When she enters "React Form Component" in Title
    And she enters "GUI_FORM" in Capability Domain
    And she enters "React+Redux" in Technology Stack
    And she enters step-by-step guidance in Content (Markdown)
    And she clicks [Create Skill]
    Then the skill is created in playbook "React Frontend v1.2"
    And she sees success notification
    And she is redirected to FOB-SKILLS-VIEW_SKILL-1

  Scenario: FOB-SKILLS-CREATE_SKILL-03 Validate required fields
    Given Maria is on the create skill form
    When she leaves Title empty
    And she clicks [Create Skill]
    Then she sees validation error "Title is required"

  Scenario: FOB-SKILLS-CREATE_SKILL-04 Capability Domain autocomplete
    Given other skills in the playbook have domains "GUI_FORM", "API_CRUD", "DB_MIGRATION"
    When Maria starts typing "GUI" in Capability Domain
    Then she sees autocomplete suggestions: "GUI_FORM"
    And she can also enter a new value like "GUI_LIST"

  Scenario: FOB-SKILLS-CREATE_SKILL-05 Technology Stack autocomplete
    Given other skills in the playbook have stacks "React+Redux", "Django+HTMX"
    When Maria starts typing "React" in Technology Stack
    Then she sees autocomplete suggestions: "React+Redux"
    And she can also enter a new value like "React+MUI"

  Scenario: FOB-SKILLS-CREATE_SKILL-06 Rich text formatting in Content
    Given Maria is on the create skill form
    Then Content field supports Markdown formatting
    And she can add headings, bold, italic, lists, code blocks, and links

  Scenario: FOB-SKILLS-CREATE_SKILL-07 Cancel skill creation
    Given Maria has entered skill data
    When she clicks [Cancel]
    Then she sees "Discard changes?" confirmation
    When she confirms
    Then no skill is created
