Feature: FOB-ARTIFACTS-DELETE_ARTIFACT-1 Delete Artifact
  As a methodology author (Maria)
  I want to delete artifacts
  So that I can remove obsolete deliverables

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend v1.2"
    And the playbook has artifact "Old Template Document"

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-01 Open delete confirmation
    Given Maria is on artifacts list
    When she clicks [Delete] for "Old Template Document"
    Then the FOB-ARTIFACTS-DELETE_ARTIFACT-1 modal appears
    And it shows "Delete Artifact?"

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-02 Modal shows artifact details
    Given the delete modal is open
    Then it displays artifact name and type
    And it shows warning about activity links

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-03 Warning about linked activities
    Given the artifact is used in 3 activities
    Then the modal shows "Used in 3 activities"
    And it lists the activities
    And it shows "Activity links will be removed"

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-04 Confirm deletion
    Given the delete modal is open
    When she clicks [Delete Artifact]
    Then the artifact is deleted
    And activity links are removed
    And she sees success notification

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-05 Cancel deletion
    Given the delete modal is open
    When she clicks [Cancel]
    Then the modal closes
    And the artifact is not deleted

  Scenario: FOB-ARTIFACTS-DELETE_ARTIFACT-06 Delete artifact with template
    Given the artifact has an attached template file
    Then the modal shows "Template file will be deleted"
    When she confirms deletion
    Then the artifact and template are both deleted
