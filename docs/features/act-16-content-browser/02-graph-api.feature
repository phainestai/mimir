Feature: FOB-CONTENT-BROWSER-API Content Browser Graph API and Data
  As a methodology author (Maria) or team member
  I want graph data to load reliably and errors to be communicated clearly
  So that I can recover from failures without losing my place

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-13 Graph data served from API endpoint
    Given Maria opens a playbook in the graph view
    Then content-browser.js fetches data from GET /api/playbooks/<pk>/graph/
    And the response drives graph rendering with nodes, edges, and phase metadata
    And the response respects the same visibility/access rules as the playbook detail page


  Scenario: FOB-CONTENT-BROWSER-13b Activity phase metadata is included in graph API response
    Given a playbook has an activity "Design Form" assigned to a Phase "Construction" (colour #3B82F6)
    When the graph API is called for that playbook
    Then the activity node in the response includes phase metadata in its meta object:
      | field         | value               |
      | phase_id      | the Phase's pk      |
      | phase_name    | "Construction"      |
      | phase_colour  | "#3B82F6"           |
    And the phase_colour value is a valid hex colour string starting with "#"
    And an activity NOT assigned to a phase has no phase_id in its meta object


  Scenario: FOB-CONTENT-BROWSER-13e Resource nodes are scoped per-activity (no cross-referencing dedup)
    Given a playbook has two activities "Build Login" and "Build Register"
    And both activities use the same Rule "Validate Input"
    When the graph API is called for that playbook
    Then the response contains TWO Rule nodes: one scoped to "Build Login" and one to "Build Register"
    And each Rule node has a unique namespaced id, e.g. "rule:7:activity:3" and "rule:7:activity:5"
    And each Rule node carries the same entity_pk, detail_url and embed_url as the canonical entity
    And each Rule node has a distinct graph-id so Cytoscape renders them as separate visual nodes
    And edges connect each Rule node only to its respective Activity
    And the same per-activity scoping applies to: Skills, Agents, Artifacts (input/output)
    And Workflows and Activities themselves are NOT duplicated — they remain single nodes
    Notes:
      This intentional duplication eliminates cross-referencing edges that cause layout chaos.
      The resource tree (FOB-CONTENT-BROWSER-28) still deduplicates — it shows each resource
      once regardless of how many activities use it.
      Node id format for resource nodes: "<type>:<entity_pk>:activity:<activity_pk>"
      Node id format for structural nodes: "<type>:<entity_pk>" (unchanged)


  Scenario: FOB-CONTENT-BROWSER-13f Activity nodes include a display code label
    Given a playbook has a workflow "Build Phase Execution" with abbreviation "BPE"
    And that workflow has activities with order 1, 2, 3 named "Plan", "Implement", "Test"
    When the graph API is called for that playbook
    Then each activity node in the response includes a display_code field:
      e.g. "BPE-1", "BPE-2", "BPE-3"
    And the display_code is derived from: "{workflow.abbreviation}-{activity.order}"
    And when a workflow has no abbreviation set the display_code is an empty string
    And Cytoscape renders activity nodes with a two-line label:
      first line: display_code (smaller, muted)
      second line: activity name (normal weight)
    And if display_code is empty only the activity name is shown (single line, no blank line)


  Scenario: FOB-CONTENT-BROWSER-13g Sequence edges show execution order within a workflow
    Given a workflow has three activities with order 1, 2, 3
    When the graph API is called for that playbook
    Then the response contains sequence edges connecting consecutive activities:
      activity(order=1) → activity(order=2) → activity(order=3)
    And sequence edges have relationship="sequence"
    And sequence edges are distinct from predecessor edges (relationship="predecessor")
      — predecessor edges represent explicit cross-step or cross-workflow dependencies
        while sequence edges always represent the natural execution order within a workflow
    And if a workflow has only one activity no sequence edge is emitted for it
    And sequence edges are NOT emitted across workflow boundaries
    And on the canvas sequence edges are rendered as solid mid-weight arrows
      distinct from the dashed predecessor edges


    Given Maria opens a playbook in the graph view
    When the GET /api/playbooks/<pk>/graph/ request fails (network error or 5xx)
    Then the canvas shows an error message: "Could not load graph data."
    And a [Retry] button re-triggers the API fetch
    And the left panel structure tree shows: "Could not load structure."
    And the resource section shows: "Select a Workflow to see its resources."


  Scenario: FOB-CONTENT-BROWSER-13c Session expires while graph is loaded
    Given Maria is viewing a graph and her Django session expires
    When content-browser.js fetches /api/playbooks/<pk>/graph/ (e.g. on retry)
    Then the client detects the non-JSON response and redirects to /auth/user/login/?next=/browser/<pk>/
    And the redirect URL does NOT include filter params — filter state is lost on re-auth
      (acceptable: user can re-apply filters after logging back in)


  Scenario: FOB-CONTENT-BROWSER-13d Playbook deleted while Maria is viewing it
    Given Maria is viewing the graph for playbook 7
    When the playbook is deleted (by the owner or admin) during her session
    And she triggers a graph reload (e.g. clicks [Retry])
    Then the graph API returns 404
    And the canvas shows: "This playbook is no longer available."
    And a [Browse other playbooks] button navigates to /browser/

