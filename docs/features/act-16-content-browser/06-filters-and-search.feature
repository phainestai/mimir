Feature: FOB-CONTENT-BROWSER-FILTERS Content Browser Filters and Search
  As a methodology author (Maria) or team member
  I want to filter the graph by entity type and phase, and search nodes by name
  So that I can focus on the parts of the playbook relevant to me

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-11 Filter canvas nodes by entity type
    Given Maria is on the graph view
    Then she sees an entity type filter toolbar (above or beside the canvas)
    And each filterable entity type has a toggle button showing its total node count:
      Workflow, Activity, Artifact, Skill, Agent, Rule
    And the single Playbook root node is NOT filterable — it is always shown
    And the count does not change when the type is toggled off (it reflects total, not visible)
    When she deactivates "Rules"
    Then all Rule nodes are hidden from the canvas
    And edges whose source OR target is a Rule node are also hidden
    And if "Activities" is deactivated, orphaned resource nodes (Skills, Agents, Rules,
      Artifacts with no other visible connections) are also hidden
    And the active filter state is reflected in the URL: ?types=workflow,activity,...
    When the currently selected node type is hidden (e.g. she hides Activities while an Activity is selected)
    Then the detail panel closes and the selection ring is cleared
    When she re-activates "Rules"
    Then Rule nodes and edges reappear
    And if all entity types are active the types param is removed from the URL entirely


  Scenario: FOB-CONTENT-BROWSER-11b Phase filter is shared between canvas and structural tree
    Given Maria is on the graph view and the playbook has phases defined
    Then both the canvas filter toolbar and the structural tree show a Phase filter control
    And the filter lists all phases in the playbook plus "(Unphased)"
    And if a playbook has NO phases defined, the Phase filter control is hidden entirely
    When Maria activates only "Inception"
    Then on the canvas: Activity nodes not in "Inception" are dimmed (opacity 0.2 — still visible)
    And edges to/from dimmed Activity nodes are also dimmed
    And non-Activity nodes (Workflows, Skills, Agents, Rules, Artifacts) on canvas are unaffected
    And on the structural tree: only Workflows with at least one "Inception" activity are shown,
      and within those Workflows only "Inception" activities appear
    And the active phase filter is reflected in the URL: ?phases=<id1>,<id2>
    And the canvas and structural tree share the same phase filter state and URL query param —
      changing either control updates both simultaneously
    When she clears the Phase filter
    Then all nodes return to normal visibility
    And the phases param is removed from the URL


  Scenario: FOB-CONTENT-BROWSER-12 Search nodes by name
    Given Maria is on the graph view
    When she types "Plan" in the search box
    Then nodes whose names contain "Plan" are highlighted (full opacity)
    And non-matching nodes are dimmed (reduced opacity)
    And edges are NOT dimmed by search — they remain at full opacity regardless of node match
    When both this search and FOB-CONTENT-BROWSER-11b phase filter are active simultaneously
    Then a node must satisfy BOTH to appear fully highlighted —
      nodes that fail either condition are dimmed; the search and phase dim states are cumulative
    When she clears the search
    Then all nodes return to normal appearance


  Scenario: FOB-CONTENT-BROWSER-03g Switching playbooks resets stale phase filter
    Given Maria is on /browser/3/?phases=2,5 (phases from playbook 3)
    When she switches to playbook 7 (which has different or no phases)
    Then the phases param is cleared from the URL if none of the IDs exist in playbook 7
    And the Phase filter resets to "All phases" for the new playbook
    And the entity-type filter is preserved across the switch


  Scenario: FOB-CONTENT-BROWSER-32 Clicking resource with hidden canvas node still opens panel
    Given the entity-type filter is active and Rule nodes are hidden from the canvas
    And a Rule is linked to an Activity and appears in the resource tree
    When Maria clicks that Rule in the resource tree
    Then the detail panel still opens with the Rule's embed view
    And no canvas highlighting occurs (the node is filtered out, not visible)
