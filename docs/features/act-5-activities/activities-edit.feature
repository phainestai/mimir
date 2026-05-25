Feature: FOB-ACTIVITIES-EDIT_ACTIVITY-1 Edit Activity
  As a methodology author (Maria)
  I want to edit activity details
  So that I can update work tasks

  Background:
    Given Maria is authenticated in FOB
    And she owns workflow "Component Development"
    And the workflow has activity "Setup component structure"

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-01 Open edit form
    Given Maria is viewing the activity
    When she clicks [Edit Activity]
    Then she is redirected to FOB-ACTIVITIES-EDIT_ACTIVITY-1
    And all fields are pre-populated

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-02 Edit activity name
    Given Maria is on the edit form
    When she changes Name to "Initialize component structure"
    And she clicks [Save Changes]
    Then the activity is updated

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-03 Edit activity description
    Given Maria is on the edit form
    When she updates the Description
    And she saves
    Then the description is updated

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-04 Change phase assignment
    Given the activity is in "Planning" phase
    When she changes phase to "Implementation"
    And she saves
    Then the activity is moved to Implementation phase

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-05 Change activity order
    Given the activity is at order #3
    When she changes order to "1"
    And she saves
    Then the activity moves to position 1

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-06 Add dependencies
    Given the activity has no dependencies
    When she adds "Define requirements" as dependency
    And she saves
    Then the dependency is added

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-07 Remove dependencies
    Given the activity has 2 dependencies
    When she removes one dependency
    And she saves
    Then the dependency is removed

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-08 Manage agent, skills, and artifacts
    Given Maria is on the edit form
    When she selects "Code Reviewer" as assigned agent
    And she checks "React Development" and "Deploy to AWS Beanstalk" as required skills
    And she checks "API Specification" and "Database Schema" as input artifacts
    And she saves
    Then the agent is linked to the activity
    And both skills are linked to the activity
    And the 2 artifacts are linked as inputs

  Scenario: FOB-ACTIVITIES-EDIT_ACTIVITY-09 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then changes are discarded
