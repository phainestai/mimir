Feature: FOB-CONTENT-BROWSER-GRAPH Content Browser Graph Rendering
  As a methodology author (Maria) or team member
  I want to see all playbook entities rendered as a navigable graph
  So that I can understand the full structure and relationships of a playbook at a glance

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-04 Graph shows all playbook entities and their relationships
    Given Maria has opened "FeatureFactory" in the graph view
    Then the canvas shows a node for each entity in the playbook:
      Playbook (anchor), Workflows, Activities, Artifacts, Skills, Agents, Rules
    And nodes are visually differentiated by entity type (distinct colour per type)
    And Activity nodes that belong to a Phase show a small Phase colour chip
    And Phase is NOT a graph node — it is a filter and a label on Activity nodes
    And directed edges connect related entities:
      | relationship            | example                 |
      | Playbook contains       | Playbook → Workflow     |
      | Workflow contains       | Workflow → Activity     |
      | Activity produces       | Activity → Artifact     |
      | Activity consumes       | Artifact → Activity     |
      | Activity uses skill     | Activity → Skill        |
      | Activity assigned agent | Activity → Agent        |
      | Activity governed by    | Activity → Rule         |
      | Predecessor dependency  | Activity → Activity     |
    And edges are visually differentiated by relationship type


  Scenario: FOB-CONTENT-BROWSER-06 Default layout is hierarchical top-down
    Given Maria opens a playbook in the graph view
    Then nodes are arranged in a top-down hierarchy:
      Playbook → Workflows → Activities → (Skills / Agents / Rules / Artifacts)
    And Artifacts sit at the same level as Activities' resource nodes (below Activities)
    And Predecessor edges between Activities are horizontal within the same level
    And the layout is computed automatically (no manual positioning needed)


  Scenario: FOB-CONTENT-BROWSER-19 Layout mode switcher toggles between ELK algorithms
    Given Maria is on the graph view canvas with a playbook loaded
    Then a layout-mode button (data-testid="browser-layout-btn") is visible in the canvas controls area
    And the button label reflects the current active layout ("Layered" or "MTree")
    When Maria clicks the layout button
    Then the active layout cycles to the next algorithm:
      | cycle order | elk algorithm       | button label |
      | 1 (default) | layered             | Layered      |
      | 2           | mrtree              | MTree        |
    And after MTree the next click cycles back to Layered
    And the graph immediately re-runs the ELK layout with the new algorithm
      — nodes are visibly repositioned in the canvas
    And the graph fits to screen automatically after each layout re-run
    And the active layout name is stored in the URL query param "layout"
      so that reloading or sharing the URL preserves the chosen layout
    And the layout switch does NOT reset any active entity-type or phase filters
    Note: the layoutstop event listener must be attached before layout.run() is called
      to guarantee fit() fires even when layout completes synchronously


  Scenario: FOB-CONTENT-BROWSER-07 Pan, zoom and navigate the canvas
    Given Maria is on the graph view canvas
    Then she can pan by clicking and dragging the background
    And she can zoom in/out using the scroll wheel or pinch gesture
    And a mini-map (cytoscape-navigator) shows her viewport position
    And zoom controls (+/−/fit) are available on the canvas


  Scenario: FOB-CONTENT-BROWSER-07b Canvas zoom control buttons are interactive
    Given Maria is on the graph view canvas with a playbook loaded
    Then the zoom control buttons are visible:
      | button           | data-testid       | expected action                            |
      | Zoom in  (+)     | browser-zoom-in   | increases canvas zoom level by ~30%        |
      | Zoom out (−)     | browser-zoom-out  | decreases canvas zoom level by ~30%        |
      | Fit      (⊡)    | browser-zoom-fit  | fits all nodes into the viewport           |
    And each button is clickable — pointer events reach it (no invisible overlay blocks input)
    And clicking [+] visibly zooms in the graph
    And clicking [−] visibly zooms out the graph
    And clicking [⊡] resets zoom so all nodes fit in the viewport


  Scenario: FOB-CONTENT-BROWSER-29 Re-plot button re-runs layout on demand
    Given Maria is on the graph view canvas with a playbook loaded
    Then a [Re-plot] button (data-testid="browser-replot-btn") is visible in the canvas controls area
    When she clicks [Re-plot]
    Then the graph re-runs the current ELK layout algorithm (no algorithm change)
    And only the nodes currently present in the Cytoscape graph are included in the layout
    And the graph fits to screen automatically after the layout completes
    And clicking [Re-plot] does NOT change the active layout algorithm or any active filters
    Note: entity-type filter toggles already auto-trigger a re-layout; Re-plot is a manual
      re-trigger for cases where re-arrangement is desired without changing filter state
      (e.g. after window resize, after phase dimming, or on user preference)


  Scenario: FOB-CONTENT-BROWSER-10 Fit graph to screen
    Given Maria has panned or zoomed the canvas
    When she clicks the [Fit] button
    Then the graph zooms and pans to fit all nodes in the viewport


  Scenario: FOB-CONTENT-BROWSER-14 Loading state while graph data is fetched
    Given Maria opens a playbook in the graph view
    Then she sees a loading spinner on the canvas
    Until the API response is received and nodes are rendered


  Scenario: FOB-CONTENT-BROWSER-20b No performance warning banner is ever shown
    Given Maria opens any playbook in the graph view
    Then the canvas never shows a "performance may be reduced" or degraded-mode banner
      regardless of how many nodes or edges the playbook contains
    And the element data-testid="browser-degraded-banner" is absent from the DOM
      (it must be fully removed, not merely hidden)


  Scenario: FOB-CONTENT-BROWSER-14b CDN scripts fail to load
    Given Maria navigates to /browser/ or /browser/<pk>/
    When the Cytoscape.js CDN script fails to load
    Then a bootstrap guard detects that window.cytoscape is undefined
    And replaces the canvas area with a static HTML fallback:
      "The graph view failed to load." and a [Reload page] button
    And this fallback is pure HTML — it does NOT depend on content-browser.js executing


  Scenario: FOB-CONTENT-BROWSER-15 Empty playbook shows friendly empty state
    Given a playbook "Empty Playbook" exists with no workflows or activities
    When Maria opens it in the Content Browser
    Then the canvas shows: "This playbook has no content yet."
    And a [Go to Playbook] button links to the playbook detail page
    And the structural tree section is hidden (nothing to show)
    And the resource section shows: "Select a Workflow to see its resources."
    And the entity-type filter toolbar is shown with all counts at zero
    And the Phase filter is hidden (no phases in an empty playbook)
