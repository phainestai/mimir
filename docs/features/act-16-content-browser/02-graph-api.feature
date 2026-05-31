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


  Scenario: FOB-CONTENT-BROWSER-13b Graph API failure shows error state
    Given Maria opens a playbook in the graph view
    When the GET /api/playbooks/<pk>/graph/ request fails (network error or 5xx)
    Then the canvas shows an error message: "Could not load graph data."
    And a [Retry] button re-triggers the API fetch
    And the left panel structure tree shows: "Could not load structure."
    And the resource section shows: "Select a Workflow to see its resources."


  Scenario: FOB-CONTENT-BROWSER-13c Session expires while graph is loaded
    Given Maria is viewing a graph and her Django session expires
    When content-browser.js fetches /api/playbooks/<pk>/graph/ (e.g. on retry)
    Then the client detects the non-JSON response and redirects to /auth/login/?next=/browser/<pk>/
    And the redirect URL does NOT include filter params — filter state is lost on re-auth
      (acceptable: user can re-apply filters after logging back in)


  Scenario: FOB-CONTENT-BROWSER-13d Playbook deleted while Maria is viewing it
    Given Maria is viewing the graph for playbook 7
    When the playbook is deleted (by the owner or admin) during her session
    And she triggers a graph reload (e.g. clicks [Retry])
    Then the graph API returns 404
    And the canvas shows: "This playbook is no longer available."
    And a [Browse other playbooks] button navigates to /browser/
