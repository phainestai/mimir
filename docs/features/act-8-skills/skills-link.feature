Feature: FOB-SKILLS-LINK_SKILL-1 Link and Unlink Skills to Activities
  As a methodology author (Maria)
  I want to link reusable skills to activities
  So that each activity has tech-specific guidance and I can reuse skills across multiple activities

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has skill "React Form Component" with capability_domain "GUI_FORM"
    And the playbook has skill "Django Form View" with capability_domain "GUI_FORM"
    And the playbook has activity "Build User Profile Form" in workflow "User Management"

  Scenario: FOB-SKILLS-LINK_SKILL-01 Link a skill to an activity from Activity edit
    Given Maria is editing activity "Build User Profile Form"
    When she selects "React Form Component" from the Skill dropdown
    And she clicks [Save Changes]
    Then the activity is linked to skill "React Form Component"
    And the activity detail page shows the linked skill

  Scenario: FOB-SKILLS-LINK_SKILL-02 Skill dropdown shows only playbook-scoped skills
    Given Maria is editing activity "Build User Profile Form"
    Then the Skill dropdown shows only skills from playbook "React Frontend v1.2"
    And skills from other playbooks are not shown

  Scenario: FOB-SKILLS-LINK_SKILL-03 Unlink a skill from an activity
    Given activity "Build User Profile Form" is linked to skill "React Form Component"
    When Maria edits the activity
    And she clears the Skill dropdown (selects "None")
    And she clicks [Save Changes]
    Then the activity has no skill linked
    And the skill "React Form Component" still exists in the playbook

  Scenario: FOB-SKILLS-LINK_SKILL-04 Multiple activities reference the same skill
    Given activity "Build User Profile Form" is linked to skill "React Form Component"
    And activity "Build Settings Form" is also linked to skill "React Form Component"
    When Maria views skill "React Form Component" on FOB-SKILLS-VIEW_SKILL-1
    Then she sees "Referenced by Activities (2)" section
    And both activities are listed

  Scenario: FOB-SKILLS-LINK_SKILL-05 Activity shows no skill linked
    Given activity "Build User Profile Form" has no skill linked
    When Maria views the activity detail
    Then she sees "No skill linked" in the Skill section
    And she sees [Link Skill] button
