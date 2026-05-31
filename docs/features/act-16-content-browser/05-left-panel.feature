Feature: FOB-CONTENT-BROWSER-LEFT-PANEL Content Browser Left Panel
  As a methodology author (Maria) or team member
  I want a left panel showing the playbook structure and linked resources
  So that I can navigate the graph and explore related entities efficiently

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with workflows, activities, phases, skills, agents, and rules


  Scenario: FOB-CONTENT-BROWSER-20 Layout — three-panel chrome
    Given Maria is on /browser/<pk>/ with a valid accessible playbook
    Then the page is divided into three vertical panels:
      | panel        | position | default state           |
      | Left panel   | left     | expanded (~280px)       |
      | Canvas       | center   | always visible          |
      | Detail panel | right    | hidden until node click |
    And a [‹] toggle button on the left panel edge collapses / expands it
    And collapsing the left panel gives the canvas the full remaining width


  # ── Playbook selector ────────────────────────────────────────────────────────

  Scenario: FOB-CONTENT-BROWSER-21 Left panel shows active playbook name at top
    Given Maria is viewing "FeatureFactory" in the graph view
    Then the top of the left panel shows:
      | element               | value                                                |
      | Playbook name heading | FeatureFactory                                       |
      | Status badge          | draft / released / active / disabled (badge colours) |
      | [Change Playbook] btn | visible below the name                               |


  Scenario: FOB-CONTENT-BROWSER-22 Change Playbook and Select Playbook open the same picker
    Given Maria is on the Content Browser (with or without a playbook loaded)
    When she clicks [Change Playbook] in the left panel header
    Then the playbook picker opens (inline slide-down within the left panel)
    When she clicks [Select Playbook] in the canvas empty-state card
    Then the same playbook picker opens
    And if the left panel was collapsed it auto-expands before the picker slides down
    And the picker lists only playbooks accessible to Maria (see FOB-CONTENT-BROWSER-03e)
    And each row shows: Playbook name, Status badge, Workflow count
    And the currently active playbook (if any) is highlighted with a checkmark
    And a search input at the top allows filtering the list by name


  Scenario: FOB-CONTENT-BROWSER-23 Selecting a playbook from the picker loads it
    Given the playbook picker is open
    When Maria clicks a different playbook "React Frontend Development"
    Then the picker closes
    And the old graph is immediately cleared and a loading spinner appears
    And the detail panel closes (if it was open)
    And the structural tree clears
    And the resource section resets to: "Select a Workflow to see its resources."
    And the canvas reloads with the graph data for "React Frontend Development"
    And the left panel heading updates to "React Frontend Development"
    And the structural tree updates to reflect the new playbook's content
    And the URL updates to /browser/<new_pk>/
    And if the fetch fails, the canvas shows "Could not load graph data." [Retry]
      and the previous graph is NOT restored (canvas stays empty with the error state)


  # ── Structural tree ──────────────────────────────────────────────────────────

  Scenario: FOB-CONTENT-BROWSER-24 Structural tree shows Workflow → Activity hierarchy
    Given Maria is on the graph view with the left panel expanded
    Then below the playbook selector she sees the "Structure" tree
    And the tree contains only structural entities:
      | level | entity   | icon                   |
      | 1     | Workflow | diagram-project (blue) |
      | 2     | Activity | list-check (green)     |
    And each Activity row shows a small Phase colour chip if the activity is assigned to a phase
    And unassigned activities show no Phase chip
    And the tree is expanded by default to show all Workflows
    And Activities are collapsed by default under each Workflow


  Scenario: FOB-CONTENT-BROWSER-25 Structural tree Workflow nodes are collapsible
    Given Maria sees the structural tree
    When she clicks a Workflow node chevron
    Then that Workflow's Activities collapse / expand


  Scenario: FOB-CONTENT-BROWSER-26 Clicking a structural tree node navigates the canvas
    Given Maria sees the structural tree
    When she clicks "Build Feature" (a Workflow node) in the tree
    Then the Cytoscape canvas pans and zooms to centre that node in the viewport
    And the corresponding canvas node is highlighted with a selection ring
    And the detail panel does NOT open automatically (tree navigation ≠ detail open)
    And the same behaviour applies when she clicks an Activity row in the tree:
      the canvas pans to centre the Activity node; panel does NOT open automatically


  Scenario: FOB-CONTENT-BROWSER-27 Active node in structural tree is highlighted
    Given Maria has clicked a Workflow or Activity canvas node or structural tree row
    Then the corresponding structural tree row is highlighted (bold + accent background)
    And the highlight follows selection — only one item is highlighted at a time
    And clicking Artifact, Skill, Agent, or Rule canvas nodes does NOT highlight a
      structural tree row — those entity types appear only in the resource tree
    When she deselects by clicking the canvas background or [×] on the detail panel
    Then the structural tree row highlight is cleared


  # ── Resource tree ────────────────────────────────────────────────────────────

  Scenario: FOB-CONTENT-BROWSER-28 Resource tree shows resources for the selected Workflow
    Given Maria has selected a Workflow (by clicking its canvas node or tree row)
    Then below the structural tree she sees the "Resources" section
    And it shows all resources linked to that Workflow's activities, grouped by type:
      Artifacts, Skills, Agents, Rules — each with a count badge and collapsible
    And within each group items are listed alphabetically by name
    And duplicates are deduplicated (if two activities share a skill, show once)
    And clicking any resource row opens its detail panel (embed view)
    And the resource tree is NOT affected by the phase filter — it always shows
      all resources for the selected Workflow's activities regardless of active phases
    When an Activity node is selected instead of a Workflow
    Then the resource tree shows the resources for that Activity's parent Workflow
    When no Workflow or Activity is selected
    Then the Resources section shows: "Select a Workflow to see its resources."
    When she selects a different Workflow
    Then the resource list updates accordingly

