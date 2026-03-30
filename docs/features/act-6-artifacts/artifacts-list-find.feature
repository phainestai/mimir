Feature: FOB-ARTIFACTS-LIST+FIND-1 Artifacts List and Search
  As a methodology author (Maria)
  I want to view and search artifacts across activities
  So that I can manage deliverables and documents

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend v1.2"
    And the playbook has 15 artifacts across workflows

  Scenario: FOB-ARTIFACTS-LIST+FIND-01 Navigate to artifacts list from playbook
    Given Maria is on FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
    When she clicks the "Artifacts" tab
    Then she is redirected to FOB-ARTIFACTS-LIST+FIND-1
    And she sees "Artifacts in React Frontend v1.2" header

  Scenario: FOB-ARTIFACTS-LIST+FIND-02 View artifacts table
    Given Maria is on artifacts list
    Then she sees all 15 artifacts
    And each artifact shows: Name, Type, Activity, Required, Status, Actions

  Scenario: FOB-ARTIFACTS-LIST+FIND-03 Create new artifact
    Given Maria is on artifacts list
    When she clicks [Create New Artifact]
    Then she is redirected to FOB-ARTIFACTS-CREATE_ARTIFACT-1

  Scenario: FOB-ARTIFACTS-LIST+FIND-04 Search artifacts by name
    Given Maria is on artifacts list
    When she enters "Design" in search
    Then only artifacts matching "Design" are shown

  Scenario: FOB-ARTIFACTS-LIST+FIND-05 Filter by artifact type
    Given artifacts have types: Document, Template, Code, Diagram
    When she filters by "Document"
    Then only Document artifacts are shown

  Scenario: FOB-ARTIFACTS-LIST+FIND-06 Filter by required status
    Given some artifacts are required
    When she filters by "Required Only"
    Then only required artifacts are shown

  Scenario: FOB-ARTIFACTS-LIST+FIND-07 Filter by activity
    Given Maria is on artifacts list
    When she filters by activity "Component Setup"
    Then only artifacts for that activity are shown

  Scenario: FOB-ARTIFACTS-LIST+FIND-08 Group by workflow
    Given Maria is on artifacts list
    When she clicks [Group by Workflow]
    Then artifacts are grouped by their parent workflow

  Scenario: FOB-ARTIFACTS-LIST+FIND-09 Navigate to view artifact
    Given Maria is on artifacts list
    When she clicks [View] for an artifact
    Then she is redirected to FOB-ARTIFACTS-VIEW_ARTIFACT-1

  Scenario: FOB-ARTIFACTS-LIST+FIND-10 Empty state display
    Given the playbook has zero artifacts
    Then she sees "No artifacts yet"
    And she sees [Create First Artifact] button
