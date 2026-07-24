Feature: FOB-CONTENT-BROWSER-ACCESS Content Browser Access and Navigation
  As a methodology author (Maria) or team member
  I want to open the Content Browser from a playbook I am viewing
  So that I can explore that playbook's entity graph without picking a playbook first

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-01 Content Browser opened from Playbook detail header
    Given Maria is on the playbook detail page for "FeatureFactory"
    Then she sees a [Content Browser] button in the playbook header action bar
    And the button is positioned immediately before [Back]
    And it links to /browser/<pk>/ for that playbook
    And "Content Browser" is NOT shown in the top navigation bar


  Scenario: FOB-CONTENT-BROWSER-01b Unauthenticated user is redirected to login
    Given Bob is not logged in
    When he navigates to /browser/3/
    Then he is redirected to the FOB login page
    And after logging in he is returned to the URL he originally requested


  Scenario: FOB-CONTENT-BROWSER-02 /browser/ without a playbook id returns 404
    Given Maria navigates to /browser/
    Then the view returns HTTP 404
    And she sees the standard Django 404 page
    And the Content Browser chrome is NOT rendered


  Scenario: FOB-CONTENT-BROWSER-03 /browser/<pk>/ loads the graph for that playbook directly
    Given Maria navigates directly to /browser/3/
    Then the three-panel layout is rendered
    And the canvas loads with the graph for the playbook with id=3
    And the left panel heading shows that playbook's name
    And the structural tree is populated


  # NOTE: FOB-CONTENT-BROWSER-03b (in-browser playbook switching) REMOVED — entry is playbook-scoped from Playbook detail.
  # NOTE: FOB-CONTENT-BROWSER-03f (URL filter param normalisation) REMOVED — filter toolbar dropped.


  Scenario: FOB-CONTENT-BROWSER-03c Inaccessible or missing playbook returns 404
    Given a visitor navigates to /browser/42/ (private playbook they cannot access)
    And a visitor navigates to /browser/9999/ (no such playbook exists)
    Then in both cases the view returns HTTP 404
    And the visitor sees the standard Django 404 page
    And the Content Browser chrome is NOT rendered
    And the response does not reveal whether the playbook exists or is private
