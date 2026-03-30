Feature: FOB-PIPS-CREATE_PIP-1 Create Playbook Improvement Proposal
  As a methodology author (Maria)
  I want to create PIPs for playbook improvements
  So that I can track and implement enhancements

  Background:
    Given Maria is authenticated in FOB
    And she is viewing playbook "React Frontend v1.2"

  Scenario: FOB-PIPS-CREATE_PIP-01 AI-suggested PIP
    Given Maria is viewing a playbook
    When the AI detects improvement opportunity
    Then she sees PIP suggestion notification
    When she clicks [Review Suggestion]
    Then she sees FOB-PIPS-CREATE_PIP-1 modal
    And the form is pre-filled with AI suggestion

  Scenario: FOB-PIPS-CREATE_PIP-02 Manual PIP creation
    Given Maria is on playbook view
    When she clicks [+ New PIP]
    Then she sees FOB-PIPS-CREATE_PIP-1 modal
    And she can enter: Title, Description, Type, Priority

  Scenario: FOB-PIPS-CREATE_PIP-03 Create PIP with type
    Given Maria is creating a PIP
    When she selects type "Add Activity"
    And she enters details
    And she clicks [Create PIP]
    Then the PIP is created with status "Proposed"

  Scenario: FOB-PIPS-CREATE_PIP-04 PIP types available
    Given Maria is creating a PIP
    Then she sees type options:
      | Type                 |
      | Add Activity         |
      | Remove Activity      |
      | Modify Activity      |
      | Add Workflow         |
      | Restructure          |
      | Documentation Update |
      | Other                |

  Scenario: FOB-PIPS-CREATE_PIP-05 Set PIP priority
    Given Maria is creating a PIP
    Then she can set priority: Low, Medium, High, Critical
