Feature: FOB-SKILLS-VIEW_SKILL-1 View Skill Details
  As a methodology author (Maria)
  I want to view skill details including capability and tech stack metadata
  So that I can understand what technology guidance is available and which activities use it

  Background:
    Given Maria is authenticated in FOB
    And she is viewing skill "React Form Component" in playbook "React Frontend v1.2"
    And the skill has capability_domain "GUI_FORM" and technology_stack "React+Redux"

  Scenario: FOB-SKILLS-VIEW_SKILL-01 Open skill detail page
    Given Maria is on FOB-SKILLS-LIST+FIND-1
    When she clicks [View] for "React Form Component"
    Then she is redirected to FOB-SKILLS-VIEW_SKILL-1
    And she sees breadcrumb: Playbooks > React Frontend v1.2 > Skills > React Form Component

  Scenario: FOB-SKILLS-VIEW_SKILL-02 View skill header with metadata
    Given Maria is on the skill detail page
    Then she sees skill title "React Form Component"
    And she sees Capability Domain badge "GUI_FORM"
    And she sees Technology Stack badge "React+Redux"
    And she sees parent playbook badge "React Frontend v1.2"

  Scenario: FOB-SKILLS-VIEW_SKILL-03 View skill content
    Given Maria is on the skill detail page
    Then she sees the formatted Markdown content
    And formatting is preserved (headings, bold, italic, lists, code blocks)

  Scenario: FOB-SKILLS-VIEW_SKILL-04 View activities referencing this skill
    Given 3 activities reference this skill
    Then she sees "Referenced by Activities (3)" section
    And she sees a list of activity names with their workflow context
    And each activity link navigates to FOB-ACTIVITIES-VIEW_ACTIVITY-1

  Scenario: FOB-SKILLS-VIEW_SKILL-05 Edit skill button
    Given Maria is viewing the skill
    When she clicks [Edit Skill]
    Then she is redirected to FOB-SKILLS-EDIT_SKILL-1

  Scenario: FOB-SKILLS-VIEW_SKILL-06 Delete skill button
    Given Maria is viewing the skill
    When she clicks [Delete Skill]
    Then the FOB-SKILLS-DELETE_SKILL-1 modal appears
