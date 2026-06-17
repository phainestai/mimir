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


  Scenario: FOB-CONTENT-BROWSER-33 Graph nodes are inserted in a deterministic order for optimal ELK layout
    Given Maria opens any playbook in the graph view
    Then the Cytoscape element array passed to ELK is constructed in this exact order:
      1. All Workflow nodes (in their stored workflow order)
      2. All Activity nodes, sorted by workflow order then by activity order within each workflow
      3. For each Activity (in the order above): its resource nodes immediately follow —
           Agent, Skills, Rules, Artifacts linked to that activity
    And this ordering applies both on initial page load and after every entity-type filter rebuild
    And the ELK layout algorithm receives the workflow→activity backbone first,
      so it can treat that backbone as the primary structure and group resource nodes
      naturally around their parent activities
    Note: resource node IDs encode their parent activity ("<type>:<pk>:activity:<act_pk>")
      so ordering is derived client-side without additional API changes


  Scenario: FOB-CONTENT-BROWSER-19 Layout picker — 2-level dropdown to select any layout algorithm
    Given Maria is on the graph view canvas with a playbook loaded
    Then a layout picker button (data-testid="browser-layout-btn") is visible in the canvas controls area
    And the button label shows the human-readable name of the currently active layout
    And the button shows a chevron icon (▾) indicating it opens a dropdown
    When Maria clicks the layout picker button
    Then a 2-level dropdown panel (data-testid="browser-layout-dropdown") opens near the button
    And the panel is grouped by layout library, each group showing:
      | group header | data-testid prefix              |
      | ELK          | browser-layout-group-elk        |
      | Dagre        | browser-layout-group-dagre      |
      | Cola         | browser-layout-group-cola       |
      | Klay         | browser-layout-group-klay       |
      | CiSE         | browser-layout-group-cise       |
      | Euler        | browser-layout-group-euler      |
      | AVSDF        | browser-layout-group-avsdf      |
      | CoSE-Bilkent | browser-layout-group-cose-bilkent |
      | fCoSE        | browser-layout-group-fcose      |
      | Cytoscape    | browser-layout-group-cy         |
    And each group lists its available layout options as clickable items
      (data-testid="browser-layout-option-{layout-key}")
    And the currently active layout option is visually highlighted (active/checked state)
    When Maria clicks any layout option
    Then the dropdown closes
    And the layout picker button label updates to the chosen layout's human-readable name
    And the graph immediately re-runs the new layout algorithm — nodes are visibly repositioned
    And the graph fits to screen automatically after the layout completes
    And the active layout key is stored in the URL query param "layout"
      so that reloading or sharing the URL preserves the chosen layout
    And the layout switch does NOT reset any active entity-type or phase filters
    When Maria presses Escape while the dropdown is open
    Then the dropdown closes without changing the active layout
    Note: the layoutstop event listener must be attached before layout.run() is called
      to guarantee fit() fires even when layout completes synchronously
    Note: if the "layout" URL param contains an unrecognised value the browser falls back
      to the default layout (elk-layered) silently


  Scenario: FOB-CONTENT-BROWSER-34 Layout picker catalog — all available layout algorithms
    Given Maria opens the layout picker dropdown
    Then the following 24 layout algorithms are available, grouped as shown:
      | group        | layout-key           | label              | library CDN                              |
      | ELK          | elk-layered          | Layered (default)  | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-mrtree           | Tree               | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-force            | Force              | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-stress           | Stress             | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-disco            | Disco              | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-radial           | Radial             | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-rectpacking      | Rect Packing       | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-sporeOverlap     | Spore Overlap      | elkjs + cytoscape-elk (already loaded)   |
      | ELK          | elk-sporeCompaction  | Spore Compact      | elkjs + cytoscape-elk (already loaded)   |
      | Dagre        | dagre-tb             | Top-Down           | dagre + cytoscape-dagre (already loaded) |
      | Dagre        | dagre-lr             | Left-Right         | dagre + cytoscape-dagre (already loaded) |
      | Cola         | cola                 | Cola               | cytoscape-cola (CDN)                     |
      | Klay         | klay                 | Klay               | klayjs + cytoscape-klay (CDN)            |
      | CiSE         | cise                 | CiSE               | cytoscape-cise (CDN)                     |
      | Euler        | euler                | Euler              | cytoscape-euler (CDN)                    |
      | AVSDF        | avsdf                | AVSDF              | cytoscape-avsdf (CDN)                    |
      | CoSE-Bilkent | cose-bilkent         | CoSE-Bilkent       | cytoscape-cose-bilkent (CDN)             |
      | fCoSE        | fcose                | fCoSE              | cytoscape-fcose (CDN)                    |
      | Cytoscape    | cy-grid              | Grid               | native cytoscape (already loaded)        |
      | Cytoscape    | cy-circle            | Circle             | native cytoscape (already loaded)        |
      | Cytoscape    | cy-concentric        | Concentric         | native cytoscape (already loaded)        |
      | Cytoscape    | cy-breadthfirst      | Breadth-first      | native cytoscape (already loaded)        |
      | Cytoscape    | cy-cose              | CoSE               | native cytoscape (already loaded)        |
      | Cytoscape    | cy-random            | Random             | native cytoscape (already loaded)        |
    And "elk-layered" is the default layout when no "layout" URL param is present
    And legacy URL values "layered" and "mrtree" are mapped to "elk-layered" and "elk-mrtree"
      for backward compatibility with existing bookmarks/shared URLs
    And each layout library required but not yet loaded is fetched from CDN at page load
      (all scripts listed in browser_graph.html <head> — not lazy-loaded at selection time)
    Note: all 9 ELK sub-algorithms (layered, stress, mrtree, radial, force, disco,
      sporeOverlap, sporeCompaction, rectpacking) are driven by the elk.algorithm property —
      no additional CDN needed; the single elkjs bundle includes all algorithms
    Note: layout-key values are used verbatim as the URL "layout" query param value


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


  Scenario: FOB-CONTENT-BROWSER-07c Fit graph to screen
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
