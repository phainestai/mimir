Feature: FOB-SKILLS-LINK_SKILL-1 Link and Unlink Skills to Activities (M2M)
  As a methodology author (Maria)
  I want to link one or more reusable skills to an activity
  So that each activity can offer multiple tech-specific guidance options and skills can be reused across activities

  Status: ✅ DONE - Multi-skill M2M link/unlink via GUI and MCP
  Branch: feature/skill-activity-m2m
  Related: act-13-mcp/interact-with-skills-via-mcp

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has skill "React Form Component" with capability_domain "GUI_FORM"
    And the playbook has skill "Django Form View" with capability_domain "GUI_FORM"
    And the playbook has skill "Deploy to AWS Beanstalk" with capability_domain "DEPLOY"
    And the playbook has activity "Build User Profile Form" in workflow "User Management"

  Scenario: FOB-SKILLS-LINK_SKILL-01 Link a skill to an activity from Activity edit
    Given Maria is editing activity "Build User Profile Form"
    When she checks "React Form Component" in the Skills checkbox list
    And she clicks [Save Changes]
    Then the activity is linked to skill "React Form Component"
    And the activity detail page shows the linked skill

  Scenario: FOB-SKILLS-LINK_SKILL-02 Skills checkbox list shows only playbook-scoped skills
    Given Maria is editing activity "Build User Profile Form"
    Then the Skills checkbox list shows only skills from playbook "React Frontend v1.2"
    And skills from other playbooks are not shown

  Scenario: FOB-SKILLS-LINK_SKILL-03 Link multiple skills to one activity
    Given Maria is editing activity "Pick Application Deployment Style"
    When she checks "Deploy to AWS Beanstalk"
    And she checks "Deploy to AWS with EKS"
    And she clicks [Save Changes]
    Then the activity is linked to both skills
    And the activity detail page lists both skills under Required Skills

  Scenario: FOB-SKILLS-LINK_SKILL-04 Unlink one skill while keeping others
    Given activity "Pick Application Deployment Style" is linked to skills "Deploy to AWS Beanstalk" and "Deploy to AWS with EKS"
    When Maria edits the activity
    And she unchecks "Deploy to AWS Beanstalk"
    And she clicks [Save Changes]
    Then the activity is still linked to "Deploy to AWS with EKS"
    And the activity is not linked to "Deploy to AWS Beanstalk"

  Scenario: FOB-SKILLS-LINK_SKILL-05 Unlink all skills from an activity
    Given activity "Build User Profile Form" is linked to skill "React Form Component"
    When Maria edits the activity
    And she unchecks all skills in the Skills checkbox list
    And she clicks [Save Changes]
    Then the activity has no skills linked
    And the skill "React Form Component" still exists in the playbook

  Scenario: FOB-SKILLS-LINK_SKILL-06 Multiple activities reference the same skill
    Given activity "Build User Profile Form" is linked to skill "React Form Component"
    And activity "Build Settings Form" is also linked to skill "React Form Component"
    When Maria views skill "React Form Component" on FOB-SKILLS-VIEW_SKILL-1
    Then she sees "Referenced by Activities (2)" section
    And both activities are listed

  Scenario: FOB-SKILLS-LINK_SKILL-07 Activity shows no skills linked
    Given activity "Build User Profile Form" has no skills linked
    When Maria views the activity detail
    Then she sees "No skills linked" in the Skills section
    And she sees [Link Skills] button
