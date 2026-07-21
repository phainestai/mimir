Feature: FOB-CONTENT-BROWSER-ACCESS Content Browser Access and Navigation
  As a methodology author (Maria) or team member
  I want to access the Content Browser from anywhere in FOB
  So that I can navigate directly to any playbook's graph view

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-01 Content Browser added to top navigation after Home
    Given Maria is on any page in FOB
    Then she sees "Content Browser" in the top navigation bar
    And it is positioned second — directly after "Home" in the nav order
    And it links to /browser/


  Scenario: FOB-CONTENT-BROWSER-01b Unauthenticated user is redirected to login
    Given Bob is not logged in
    When he navigates to /browser/
    And when he navigates to /browser/3/
    Then in both cases he is redirected to the FOB login page
    And after logging in he is returned to the URL he originally requested


  Scenario: FOB-CONTENT-BROWSER-02 /browser/ with no playbook selected shows empty state
    Given Maria navigates to /browser/
    Then the three-panel layout is rendered
    And the left panel shows:
      | element               | value                       |
      | Playbook name heading | "(No playbook selected)"    |
      | [Select Playbook] btn | visible (replaces [Change]) |
    And the canvas shows a centred empty-state card:
      | element | content                                            |
      | Icon    | large diagram-project icon                         |
      | Heading | "Select a playbook to explore"                     |
      | Body    | "Choose a playbook to see its full entity graph."  |
      | Button  | [Select Playbook] — triggers the playbook picker   |
    And the structural tree section is hidden (not rendered)
    And the resource section shows: "Select a Workflow to see its resources."


  Scenario: FOB-CONTENT-BROWSER-03 /browser/<pk>/ loads the graph for that playbook directly
    Given Maria navigates directly to /browser/3/
    Then the three-panel layout is rendered
    And the canvas loads with the graph for the playbook with id=3
    And the left panel heading shows that playbook's name
    And the structural tree is populated


  Scenario: FOB-CONTENT-BROWSER-03b URL is the source of truth for the active playbook
    Given Maria is viewing /browser/3/ (FeatureFactory)
    When she uses [Change Playbook] and selects "React Frontend Development" (id=7)
    Then the URL updates to /browser/7/
    And the browser back button returns her to /browser/3/ (FeatureFactory)
    And she can copy /browser/7/ and share it — the recipient opens directly to that playbook
    Note: Entity-type and phase filter URL params were removed with the filter toolbar (FOB-11/11b).
    Note: Layout/routing/compound URL params may appear after custom-layout changes (FOB-63); default mode resets on full page load.


  # NOTE: FOB-CONTENT-BROWSER-03f (URL filter param normalisation) REMOVED — filter toolbar dropped.


  Scenario: FOB-CONTENT-BROWSER-03c Inaccessible or missing playbook returns 404
    Given a visitor navigates to /browser/42/ (private playbook they cannot access)
    And a visitor navigates to /browser/9999/ (no such playbook exists)
    Then in both cases the view returns HTTP 404
    And the visitor sees the standard Django 404 page
    And the Content Browser chrome is NOT rendered
    And the response does not reveal whether the playbook exists or is private


  Scenario: FOB-CONTENT-BROWSER-03e Playbook picker only shows accessible playbooks
    Given Maria is on /browser/ or clicks [Change Playbook] / [Select Playbook]
    Then the picker lists only playbooks she can access:
      | included                                                      |
      | Playbooks she owns (any status)                               |
      | Public non-draft playbooks (status: released/active/disabled) |
      | Playbooks shared with a team she belongs to                   |
    And she does NOT see:
      | excluded                                     |
      | Private playbooks owned by other users       |
      | Public draft playbooks owned by other users  |
    And for any accessible public non-draft playbook she can open /browser/<pk>/
      and view the full graph even if she is not the owner
    And no edit actions are visible in the detail panel for playbooks she does not own


  Scenario: FOB-CONTENT-BROWSER-23b Selecting a playbook from the picker navigates via full page load
    Given the playbook picker is open
    When Maria clicks a playbook entry in the picker
    Then the browser performs a full page navigation to /browser/<selected_pk>/
      (i.e. window.location.href assignment, not an in-place AJAX/JS state update)
    So that the resulting loaded state is byte-for-byte identical to
      opening /browser/<selected_pk>/ directly in a new tab
    And layout params from the previous playbook are not carried over (fresh default layout mode on load)
    And the back button navigates to the page where the picker was opened
