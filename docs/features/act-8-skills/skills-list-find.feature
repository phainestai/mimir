Feature: FOB-SKILLS-LIST+FIND-1 Skills List and Search
  As a methodology author (Maria)
  I want to view and search skills within a playbook
  So that I can manage reusable, tech-specific guidance and see which capabilities are covered

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend v1.2"
    And the playbook has 12 skills defined
    And skills have capability_domain and technology_stack metadata

  Scenario: FOB-SKILLS-LIST+FIND-01 Navigate to skills list from playbook
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    When she clicks the "Skills" tab
    Then she is redirected to FOB-SKILLS-LIST+FIND-1
    And she sees "Skills in React Frontend v1.2" header

  Scenario: FOB-SKILLS-LIST+FIND-02 View skills table with capability metadata
    Given Maria is on skills list
    Then she sees all 12 skills
    And each skill shows: Title, Capability Domain, Technology Stack, Activities (count), Actions
    And "Capability Domain" shows values like "GUI_FORM", "API_CRUD"
    And "Technology Stack" shows values like "React+Redux", "Django+HTMX"
    And "Activities" shows the count of activities referencing each skill

  Scenario: FOB-SKILLS-LIST+FIND-03 Create new skill from playbook
    Given Maria is on skills list
    When she clicks [Create New Skill]
    Then she is redirected to FOB-SKILLS-CREATE_SKILL-1
    And the form is scoped to playbook "React Frontend v1.2"

  Scenario: FOB-SKILLS-LIST+FIND-04 Search skills by name or metadata
    Given Maria is on skills list
    When she enters "Form" in search
    Then only skills matching "Form" in title, capability_domain, technology_stack, or content are shown

  Scenario: FOB-SKILLS-LIST+FIND-05 Filter by Capability Domain
    Given skills have domains "GUI_FORM", "GUI_LIST", "API_CRUD", "DB_MIGRATION"
    When she selects "GUI_FORM" from the Capability Domain filter
    Then only skills with capability_domain "GUI_FORM" are shown
    And the filter dropdown shows autocomplete suggestions from existing values

  Scenario: FOB-SKILLS-LIST+FIND-06 Filter by Technology Stack
    Given skills have stacks "React+Redux", "Django+HTMX", "FastAPI"
    When she selects "Django+HTMX" from the Technology Stack filter
    Then only skills with technology_stack "Django+HTMX" are shown
    And the filter dropdown shows autocomplete suggestions from existing values

  Scenario: FOB-SKILLS-LIST+FIND-07 View activity usage count
    Given skill "Component Form Guide" is referenced by 3 activities
    When Maria is on skills list
    Then that skill shows "3" in the Activities column
    And she can click the count to see which activities reference it

  Scenario: FOB-SKILLS-LIST+FIND-08 Navigate to view skill
    Given Maria is on skills list
    When she clicks [View] for a skill
    Then she is redirected to FOB-SKILLS-VIEW_SKILL-1

  Scenario: FOB-SKILLS-LIST+FIND-09 Empty state display
    Given the playbook has zero skills
    Then she sees "No skills yet"
    And she sees [Create First Skill] button

  Scenario: FOB-SKILLS-LIST+FIND-10 Filter unlinked skills
    Given 4 skills have zero activities referencing them
    When she filters by "Unlinked"
    Then only those 4 skills with zero activity references are shown
