Feature: FOB-CONTENT-BROWSER-FILTERS Content Browser Filters and Search
  As a methodology author (Maria) or team member
  I want to search nodes by name
  So that I can focus on the parts of the playbook relevant to me

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  # NOTE: FOB-CONTENT-BROWSER-11 (entity-type filter toolbar) REMOVED
  # The entity-type filter toolbar has been removed from the Content Browser UI.
  # All entity types are always shown; there is no per-type toggle control.

  # NOTE: FOB-CONTENT-BROWSER-11b (phase filter) REMOVED
  # The phase filter toolbar has been removed from the Content Browser UI.
  # All phases are always visible; there is no phase filter control.

  # NOTE: FOB-CONTENT-BROWSER-03g (playbook switch resets filters) REMOVED
  # Filter reset on playbook switch is no longer relevant as filters no longer exist.


  Scenario: FOB-CONTENT-BROWSER-12 Search nodes by name
    Given Maria is on the graph view
    When she types "Plan" in the search box
    Then nodes whose names contain "Plan" are highlighted (full opacity)
    And non-matching nodes are dimmed (reduced opacity)
    And edges are NOT dimmed by search — they remain at full opacity regardless of node match
    When she clears the search
    Then all nodes return to normal appearance


  Scenario: FOB-CONTENT-BROWSER-32 Clicking resource in tree still opens panel
    Given a Rule is linked to an Activity and appears in the resource tree
    When Maria clicks that Rule in the resource tree
    Then the detail panel still opens with the Rule's embed view
