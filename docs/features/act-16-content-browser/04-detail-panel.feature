Feature: FOB-CONTENT-BROWSER-DETAIL-PANEL Content Browser Detail Panel
  As a methodology author (Maria) or team member
  I want to click a graph node to see its full details without leaving the graph
  So that I can explore entity details in context

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-08b Embed mode strips outer chrome from existing view
    Given any entity detail view is requested with ?embed=1
    Then the response renders only the entity content card
    And the response does NOT include: navbar, breadcrumbs, header action buttons,
      page <html>/<body> wrappers, or Bootstrap outer layout
    And the response DOES include: entity name, all key fields, Markdown rendered
      guidance (for Activities), tags, metadata — everything from the normal detail view
    And the HTTP response status is 200 for authorized requests
    And the HTTP response status is 403/404 for unauthorized requests (same as full view)


  Scenario: FOB-CONTENT-BROWSER-08 Click a node to open entity detail panel
    Given Maria is on the graph view canvas
    When she clicks a node (e.g., an Activity node)
    Then a side panel slides in from the right, overlaying the canvas
      (the canvas does NOT resize — the panel floats over it)
    And the panel loads the existing entity detail view in embed mode
      (GET <entity_detail_url>?embed=1)
    And the embedded view renders the entity's full detail without navbar, breadcrumbs,
      or outer layout
    And the clicked node is highlighted with a selection ring
    And the panel header shows:
      | button         | action                                                  |
      | [Open new tab] | opens entity detail URL in a new browser tab            |
      | [Open full]    | navigates current tab to entity detail URL (full page)  |
      | [×] close      | closes the panel                                        |
    And if the panel is already open and she clicks a different node,
      the panel content is replaced in-place (no close/reopen animation)


  Scenario: FOB-CONTENT-BROWSER-08c Session expires while detail panel is open
    Given Maria has the detail panel open showing an Activity
    When her Django session expires
    And she clicks a different node
    Then the panel detects a non-entity response (login page redirect)
    And redirects the current tab to /auth/login/?next=/browser/<pk>/


  Scenario: FOB-CONTENT-BROWSER-09 Close entity detail panel
    Given the entity detail panel is open
    When Maria clicks the [×] button on the panel header
    Then the panel closes
    And the node selection is cleared
    And the panel content is cleared
    When she clicks any empty area on the canvas (background, not a node or edge)
    Then the panel closes and the node selection is cleared
    And clicking an edge has no effect — it does not open or close the panel


  Scenario: FOB-CONTENT-BROWSER-09b Open entity full page in new tab
    Given the entity detail panel is open showing an Activity node
    When Maria clicks [Open new tab]
    Then the entity's standard detail URL opens in a new browser tab
    And the graph view and panel remain unchanged in the current tab


  Scenario: FOB-CONTENT-BROWSER-09c Open entity full page in current tab
    Given the entity detail panel is open showing a Workflow node
    When Maria clicks [Open full]
    Then the browser navigates the current tab to the entity's standard detail URL
    And she sees the full detail page with navbar, breadcrumbs, and all actions
