Feature: FOB-CONTENT-BROWSER-CANVAS-CONTROLS Content Browser Canvas Display Controls
  As a methodology author (Maria) or team member
  I want fine-grained control over how the graph is visually rendered
  So that I can explore playbook structure in the view that best suits my current task

  Background:
    Given Maria is authenticated in FOB
    And the playbook "FeatureFactory" exists with at least 2 workflows,
      each with at least 3 activities, some with predecessor links between them,
      and at least one activity with a skill, agent, and rule attached

  # ---------------------------------------------------------------------------
  # FOB-35 — Edge routing picker
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-35 Edge routing picker — dropdown to select Cytoscape curve-style
    Given Maria is on the graph view canvas with a playbook loaded
    Then an edge routing button (data-testid="browser-routing-btn") is visible
      in the canvas controls toolbar alongside the layout picker
    And the button label shows the human-readable name of the currently active routing style
    And the button shows a chevron icon (▾) indicating it opens a dropdown
    When Maria clicks the edge routing button
    Then a dropdown panel (data-testid="browser-routing-dropdown") opens near the button
    And the dropdown lists the following options:
      | routing-key  | label              | Cytoscape curve-style |
      | bezier       | Bezier (default)   | bezier                |
      | straight     | Straight           | straight              |
      | taxi         | Orthogonal         | taxi                  |
      | haystack     | Haystack           | haystack              |
      | segments     | Segments           | segments              |
      | round-seg    | Round Segments     | round-segments        |
    And each option has data-testid="browser-routing-option-{routing-key}"
    And the currently active option is visually highlighted
    When Maria selects "Orthogonal"
    Then the dropdown closes
    And the routing button label updates to "Orthogonal"
    And ALL edges in the graph immediately update their curve-style to "taxi"
      without rebuilding the node positions or re-running the layout algorithm
    And the active routing key is stored in the URL query param "routing"
      so that reloading or sharing the URL preserves the chosen routing style
    When Maria presses Escape while the dropdown is open
    Then the dropdown closes without changing the active routing style
    Note: routing change is a style-only update — cy.style().update() is sufficient,
      no need to re-add elements or re-run the layout
    Note: "bezier" is the default when no "routing" URL param is present
    Note: if the "routing" URL param contains an unrecognised value, fall back
      to "bezier" silently
    Note: "haystack" forces straight bundled lines; it may look identical to
      "straight" on sparse graphs — this is expected behaviour


  # ---------------------------------------------------------------------------
  # FOB-36 — Activity sequence edges toggle
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-36 Sequence edges toggle — show/hide predecessor links between activities
    Given Maria is on the graph view canvas with a playbook loaded
    And the playbook has activities connected by predecessor (sequence) edges
    Then a sequence toggle button (data-testid="browser-seq-toggle") is visible
      in the canvas controls toolbar
    And the button label reads "Seq ✓" when sequence edges are shown (default: ON)
    And the button label reads "Seq ✗" when sequence edges are hidden
    And the button has a pressed/active visual state when sequence edges are shown
    When Maria clicks the sequence toggle to turn sequence edges OFF
    Then all predecessor (sequence/activity→activity) edges are removed from the Cytoscape graph
    And the graph is fully rebuilt (same as entity-type filter rebuild):
      nodes and non-sequence edges are re-added, then the current layout algorithm re-runs
    And the graph fits to screen automatically after the layout completes
    And the state is stored in the URL query param "seq=0"
    When Maria clicks the sequence toggle again to turn sequence edges back ON
    Then predecessor edges are added back to the Cytoscape graph
    And the graph is fully rebuilt and re-laid out with the current layout algorithm
    And the "seq" URL param is removed (default-on state needs no param)
    Note: "sequence edge" means an edge whose relationship type is "predecessor"
      in the graph API response — not activity→resource edges
    Note: other edge types (contains, produces, consumes, uses, assigned, governed)
      are unaffected by this toggle
    Note: hiding sequence edges is particularly useful with compound view (FOB-37)
      where predecessor arrows inside a compound box can visually clutter the layout
    Note: toggle state is preserved when entity-type filter or phase filter changes;
      the rebuild triggered by those filters must respect the current seq toggle state


  # ---------------------------------------------------------------------------
  # FOB-37 — Workflow compound view toggle
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-37 Compound view toggle — workflows as containing boxes vs graph nodes
    Given Maria is on the graph view canvas with a playbook loaded
    Then a compound view toggle button (data-testid="browser-compound-toggle") is visible
      in the canvas controls toolbar
    And the button label reads "Grouped ✗" in default (flat) mode
    And the button label reads "Grouped ✓" in compound mode

    When Maria activates compound view (clicks the toggle to turn it ON):

    Then the Cytoscape graph is fully rebuilt with compound node semantics:
      - Each Workflow node becomes a compound parent node (data-testid prefix "browser-node-workflow-{pk}")
      - Each Activity node that belongs to that Workflow has its Cytoscape "parent" set
          to the Workflow node ID, making it a child inside the Workflow box
      - Each resource node (Skill, Agent, Rule, Artifact) that is connected to an Activity
          within that Workflow also has its "parent" set to the same Workflow node ID,
          nesting inside the same compound box
      - The Playbook root node remains a standalone node above all compound boxes
      - The compound layout is re-run using the current layout algorithm

    And the visual presentation of compound boxes follows these rules:
      - Background fill: a light tinted shade of the graph canvas background,
          distinct but harmonious — use #eef2ff (very light periwinkle) so compound boxes
          are clearly distinguishable from the white canvas without clashing with node colours
      - Border: 2px solid #0d6efd (Mimir primary blue) with border-radius 8px
      - Workflow label: displayed at the top-left corner of the compound box,
          font-weight 700, color #0d6efd, font-size slightly larger than activity node labels
      - Workflow label position: data-testid="browser-node-workflow-{pk}-label"
            with Cytoscape label valign "top" and halign "left"
      - Compound box padding: minimum 20px on all sides so child nodes do not overlap the border

    And clicking the Workflow compound box itself (not a child node) opens the Workflow detail panel
      (same behaviour as clicking a Workflow node in flat mode)
    And clicking a child Activity or resource node inside the box opens that entity's detail panel
      (behaviour is unchanged from flat mode)

    When Maria deactivates compound view (clicks the toggle OFF):
    Then the graph rebuilds in flat mode — Workflow nodes are regular graph nodes again
    And all "parent" assignments are cleared before the rebuild
    And the current layout algorithm re-runs in flat mode

    And the compound view state is stored in the URL query param "compound=1"
      (absent or "0" means flat mode)

    Note: compound view and entity-type filter are composable — if Workflows are filtered OFF,
      compound view is effectively no-op (no compound parents remain); this is acceptable
    Note: compound view interacts with the sequence toggle (FOB-36): when both compound view
      and seq=0 are active, the resulting graph shows tidy boxes with no sequence clutter —
      the most structured/hierarchical reading of the playbook
    Note: ELK compound layout uses the parent/child relationship to keep children inside
      their parent's bounding box — ELK Layered handles this natively via the compound port
      mechanism; no additional configuration is needed beyond setting node parents
    Note: for layouts other than ELK (dagre, cola, etc.) compound behaviour depends on
      each layout's compound support — graceful degradation is acceptable (boxes may not
      contain children but layout still runs without error)


  # ---------------------------------------------------------------------------
  # FOB-38 — Enhanced node visual styling
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-38 Node shapes and styles fit Mimir design language
    Given Maria opens any playbook in the graph view
    Then the canvas graph uses the following refined visual style for each entity type,
      inspired by the Mimir design system (Montserrat font, Bootstrap 5.3 palette,
      card-style aesthetics with rounded corners and clear role differentiation):

      Node shapes:
      | entity type | shape           | rationale                                          |
      | Playbook    | round-octagon   | Unique, distinctive anchor — stands apart from all |
      |             |                 | other nodes; "hub" shape signals centrality        |
      | Workflow    | round-rectangle | Clean card-like shape; retains current identity    |
      |             | (wider aspect)  | Wider min-width to accommodate workflow names      |
      | Activity    | bottom-round-   | Subtle differentiation from Workflow within the    |
      |             | rectangle       | same family — flat top, rounded bottom             |
      | Artifact    | round-diamond   | Document/data shape; clearly non-entity resource   |
      | Skill       | hexagon         | Technical/tool connotation; common in skill graphs |
      | Agent       | ellipse         | Person/role metaphor; keep circular to signal human|
      | Rule        | cut-rectangle   | Clipped corners signal "constraint" without being  |
      |             |                 | as soft as round-rectangle                         |

      Node colours (unchanged from current Bootstrap palette, better contrast):
      | entity type | background      | border          | label colour   |
      | Playbook    | #6f42c1         | #5a32a3 (−1 shade) | #ffffff     |
      | Workflow    | #0d6efd         | #0a58ca (−1 shade) | #ffffff     |
      | Activity    | #198754         | #146c43 (−1 shade) | #ffffff     |
      | Artifact    | #ffc107         | #cc9a06 (−1 shade) | #212529     |
      | Skill       | #fd7e14         | #ca6510 (−1 shade) | #ffffff     |
      | Agent       | #0dcaf0         | #0aa2c0 (−1 shade) | #212529     |
      | Rule        | #6c757d         | #565e64 (−1 shade) | #ffffff     |

      Typography (all nodes):
      | property    | value                                                  |
      | font-family | Montserrat, system-ui (matches Mimir site font)        |
      | font-size   | 11px for resource nodes (Artifact/Skill/Agent/Rule),   |
      |             | 13px for Activity, 14px for Workflow, 15px for Playbook|
      | font-weight | 600 for Playbook/Workflow/Activity; 400 for resources  |
      | text-wrap   | wrap (truncate long names with ellipsis at 2 lines)    |
      | text-max-width | node width − 8px padding                           |

      Border and depth:
      | property            | value                                          |
      | border-width        | 2px for all nodes (was 0 or 1px)               |
      | border-opacity      | 1                                              |
      | background-opacity  | 1                                              |
      | shadow (via outline)| not supported natively in cy; compensate via   |
      |                     | slightly higher border-width on hover state    |

      Hover / selection states (unchanged semantics, updated style):
      | state     | style                                                        |
      | selected  | 3px ring in #dc3545 (danger red) — unchanged                 |
      | dimmed    | opacity 0.2 (phase filter / search) — unchanged             |
      | hover     | border-width 3px, border-color same entity border colour    |

    And the Playbook root node is visually the most prominent element on the canvas
      (largest font, unique shape, deepest colour)
    And resource nodes (Artifact, Skill, Agent, Rule) are visually lighter/smaller
      than structural nodes (Workflow, Activity) to communicate hierarchy
    And the overall palette reads as a coherent set — all colours drawn from Bootstrap 5.3
      semantic tokens to match the rest of the Mimir UI

    Note: shapes are set via the Cytoscape.js stylesheet "shape" property; all listed shapes
      are natively supported in Cytoscape.js 3.x without additional plugins
    Note: "bottom-round-rectangle" shape is: flat top corners, rounded bottom corners —
      it is available natively as the shape name "bottom-round-rectangle"
    Note: Montserrat must already be loaded by the page (it is — via Mimir's Google Fonts
      import in base.html); no additional font CDN entry is needed in browser_graph.html
    Note: node min-width/min-height should be set to give shapes room to breathe:
      Playbook 80×60, Workflow 120×40, Activity 110×38, resources 70×30
