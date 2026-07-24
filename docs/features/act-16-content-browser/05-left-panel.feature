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
    And a [‹] toggle button sits on the right edge of the left panel, vertically centred
    And clicking [‹] collapses the left panel to zero width and changes the icon to [›]
    And when collapsed, the [›] button remains visible on the left edge of the viewport
      so Maria can always find and click it to expand the panel again
    And clicking [›] expands the left panel back to ~280px and changes the icon to [‹]
    And collapsing or expanding the left panel causes the canvas to resize to fill the new available width


  # ── Playbook header (left panel) ─────────────────────────────────────────────

  Scenario: FOB-CONTENT-BROWSER-21 Left panel shows active playbook name at top
    Given Maria is viewing "FeatureFactory" in the graph view
    Then the top of the left panel shows:
      | element               | value                                                |
      | Playbook name heading | FeatureFactory                                       |
      | Status badge          | draft / released / active / disabled (badge colours) |
    And no [Change Playbook] or [Select Playbook] button is shown


  # ── Structural tree ──────────────────────────────────────────────────────────

  Scenario: FOB-CONTENT-BROWSER-24 Structural tree shows Workflow → Activity hierarchy
    Given Maria is on the graph view with the left panel expanded
    Then below the playbook header she sees the "Structure" tree
    And the tree contains only structural entities:
      | level | entity   | icon                   |
      | 1     | Workflow | diagram-project (blue) |
      | 2     | Activity | list-check (green)     |
    And each Activity row shows a small Phase colour chip if the activity is assigned to a phase
    And unassigned activities show no Phase chip
    And the tree starts fully collapsed — all Workflow rows are collapsed,
      no Activity rows are visible on initial load


  Scenario: FOB-CONTENT-BROWSER-25 Structural tree Workflow nodes are collapsible
    Given Maria sees the structural tree
    When she clicks a Workflow node chevron
    Then that Workflow's Activities collapse / expand


  Scenario: FOB-CONTENT-BROWSER-26 Clicking a structural tree node navigates and opens the detail panel
    Given Maria sees the structural tree

    # ── Clicking a Workflow row ───────────────────────────────────────────────
    When she clicks the text/icon area of a Workflow row (NOT the chevron ▸/▾)
    Then the Cytoscape canvas pans and zooms to centre that Workflow node in the viewport
    And the Workflow canvas node receives a selection ring (same red highlight as canvas tap)
    And the right detail panel opens with the Workflow's embed content
    And the structural tree row is highlighted (bold + accent background)
    And the accordion ALSO expands that Workflow's Activities (same as clicking the chevron)
      so the user can immediately see the highlighted child activities without an extra click

    # ── Clicking the chevron only ─────────────────────────────────────────────
    When she clicks ONLY the chevron ▸/▾ on a Workflow row
    Then the accordion toggles (expand / collapse) WITHOUT navigating the canvas
    And the detail panel does NOT open or change

    # ── Clicking an Activity row ─────────────────────────────────────────────
    When she clicks an Activity row in the tree
    Then the canvas pans and zooms to centre the Activity node
    And the Activity canvas node receives a selection ring
    And the right detail panel opens with the Activity's embed content
    And the structural tree row is highlighted

    # ── Uniform: both directions trigger same behaviour ───────────────────────
    Note: treeview click and canvas tap must produce identical visual outcome —
    same selection ring, same detail panel content, same tree row highlight.

    # IMPLEMENTATION NOTE (FOB-26 revised 2026-06-02):
    # Previous spec had "detail panel does NOT open automatically (tree navigation ≠ detail open)".
    # This is changed: tree row click DOES open detail panel, identical to canvas tap.
    # Accordion expand/collapse moves to the CHEVRON click only (not the full row).
    # Root cause of bug: _buildStructureTree click handler returns early when
    #   .browser-tree-toggle span is found (workflow rows), never navigating.
    #   Activity rows navigate but don't call _openDetailPanel.
    # Fix: wire chevron span click separately; wire row click to navigate + _openDetailPanel.


  Scenario: FOB-CONTENT-BROWSER-27 Active node in structural tree is highlighted
    Given Maria has clicked a Workflow or Activity canvas node or structural tree row
    Then the corresponding structural tree row is highlighted (bold + accent background)
    And the highlight follows selection — only one item is highlighted at a time
    And clicking Artifact, Skill, Agent, or Rule canvas nodes does NOT highlight a
      structural tree row — those entity types appear only in the resource tree
    When she deselects by clicking the canvas background or [×] on the detail panel
    Then the structural tree row highlight is cleared


  Scenario: FOB-CONTENT-BROWSER-27b Canvas tap on activity expands its parent workflow in tree
    Given Maria is viewing the structural tree (all workflows collapsed)
    When she clicks an Activity node on the Cytoscape canvas
    Then the structural tree highlights the Activity row (as per FOB-27)
    And the parent Workflow accordion section is automatically expanded
      so the highlighted Activity row is visible without Maria having to manually expand it
    When she clicks a Workflow node on the canvas
    Then the structural tree highlights the Workflow row
    And the accordion for that Workflow expands (Activities become visible)
    Note: BUG FOB-58 — previously canvas tap highlighted the tree row but did not expand
      the parent workflow accordion, meaning the highlighted row was invisible (still collapsed)
    Note: _highlightTreeNode must also call _expandTreeSection(nodeId) for activity nodes
      and _expandTreeSection for workflow nodes so the relevant section is open


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

