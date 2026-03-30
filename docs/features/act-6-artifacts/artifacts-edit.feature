Feature: FOB-ARTIFACTS-EDIT_ARTIFACT-1 Edit Artifact
  As a methodology author (Maria)
  I want to edit artifact details
  So that I can update deliverable definitions

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has artifact "Component Design Document"

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-01 Open edit form
    Given Maria is viewing the artifact
    When she clicks [Edit Artifact]
    Then she is redirected to FOB-ARTIFACTS-EDIT_ARTIFACT-1
    And all fields are pre-populated

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-02 Edit artifact name
    Given Maria is on the edit form
    When she changes Name to "Component Architecture Document"
    And she clicks [Save Changes]
    Then the artifact is updated

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-03 Edit artifact description
    Given Maria is on the edit form
    When she updates the Description
    And she saves
    Then the description is updated

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-04 Change artifact type
    Given the artifact is type "Document"
    When she changes type to "Diagram"
    And she saves
    Then the type is updated

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-05 Toggle required status
    Given the artifact is not required
    When she checks "Required" checkbox
    And she saves
    Then the artifact becomes required

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-06 Update activity associations
    Given the artifact is linked to 1 activity
    When she adds another activity link
    And she saves
    Then the artifact is linked to 2 activities

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-07 Update template file
    Given the artifact has a template
    When she uploads a new template file
    And she saves
    Then the new template replaces the old one

  Scenario: FOB-ARTIFACTS-EDIT_ARTIFACT-08 Cancel editing
    Given Maria has made changes
    When she clicks [Cancel]
    Then changes are discarded
