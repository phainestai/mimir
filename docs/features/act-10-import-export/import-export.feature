Feature: FOB-IMPORT-EXPORT-1 Import and Export Playbooks
  As a methodology author (Maria)
  I want to import and export playbooks
  So that I can share and backup my work

  Background:
    Given Maria is authenticated in FOB

  Scenario: FOB-IMPORT-01 Export playbook as JSON
    Given Maria is viewing a playbook
    When she clicks [Export] > [Export as JSON]
    Then playbook is downloaded as .json file
    And the file contains complete playbook structure

  Scenario: FOB-IMPORT-02 Export playbook as MPA
    Given Maria is viewing a playbook
    When she clicks [Export] > [Export as .mpa]
    Then playbook is packaged as .mpa file
    And it includes all workflows, activities, artifacts

  Scenario: FOB-IMPORT-03 Import playbook from JSON
    Given Maria is on playbooks list
    When she clicks [Import] > [From JSON]
    And she selects a valid .json file
    Then the playbook is imported
    And she sees success notification

  Scenario: FOB-IMPORT-04 Import validation errors
    Given Maria imports an invalid JSON
    Then she sees validation errors
    And she can fix errors or cancel import

  Scenario: FOB-IMPORT-05 Import with conflict resolution
    Given Maria imports a playbook with same name
    Then she sees conflict dialog
    And she can: Rename, Replace, or Cancel

  Scenario: FOB-IMPORT-06 Bulk export multiple playbooks
    Given Maria selects 3 playbooks
    When she clicks [Bulk Export]
    Then all 3 playbooks are exported as single .zip file
