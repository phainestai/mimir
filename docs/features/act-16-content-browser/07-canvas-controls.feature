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
    And the dropdown lists the following options (all curve-style values supported by Cytoscape 3.x):
      | routing-key       | label                | Cytoscape curve-style |
      | bezier            | Bezier (default)     | bezier                |
      | unbundled-bezier  | Unbundled Bezier     | unbundled-bezier      |
      | straight          | Straight             | straight              |
      | taxi              | Orthogonal           | taxi                  |
      | haystack          | Haystack             | haystack              |
      | segments          | Segments             | segments              |
      | round-seg         | Round Segments       | round-segments        |
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
    Note: COMPOSABILITY — the sequence toggle MUST work in all graph modes:
      - when compound view is OFF (flat mode): seq toggle filters/adds edges as normal
      - when compound view is ON (grouped mode): seq toggle must also filter/add edges
        correctly within the compound graph; the rebuild path used by _applySeqToggle
        must detect the current compound state and call _buildCompoundElements (not
        _buildFilteredElements) when compound view is active — both rebuilds must
        honour the current seq toggle state; currently _applySeqToggle always falls
        back to flat rebuild regardless of compound mode — THIS IS A BUG that must be
        fixed so that seq=0 works correctly when compound=1


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
      - Workflow label: displayed ABOVE the top-left corner of the compound box (not
          inside it), using a negative text-margin-y offset so the label floats gently
          above the box boundary — implementation: text-valign "top", text-halign "left",
          text-margin-x 6px (right), text-margin-y -14px (upward); this places the label
          in empty space above the box rather than overlapping the interior of child nodes
      - Workflow label position: data-testid="browser-node-workflow-{pk}-label"
            with Cytoscape label valign "top" and halign "left"
      - Workflow label MUST be visible in compound mode — if text-valign/halign alone
          produces an invisible or clipped label, add a text-background-color: #ffffff
          text-background-opacity: 0.85 and text-background-padding: 3px to ensure
          readability against the canvas background
      - font-weight 700, color #0d6efd, font-size slightly larger than activity node labels
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
    Note: COMPOUND LAYOUT — when compound view is ON, the layout algorithm MUST be applied to
      activity nodes inside compound boxes (not just to top-level workflow-parent nodes):
      - For ELK layouts (elk-layered, elk-stress, etc.): ELK natively supports compound layout
        via the parent/child relationship; however the layout must be configured to use the
        NESTED_ALGORITHM option or the parent compound node must receive elk:algorithm in its
        data so that child node positions are computed by the layout engine, not left random;
        without this, child nodes render on top of each other at the compound origin
      - For dagre/cola/cose: compound behaviour varies; dagre does not support compound nodes
        natively and will ignore child parentage — graceful degradation is acceptable (boxes
        may not contain children visually) but MUST NOT crash or produce an error state
      - The Reflow button (data-testid="browser-reflow-btn") MUST trigger a full layout re-run
        that includes re-positioning child nodes inside each compound box, not only top-level
        positions; the current bug where only top-level workflow-box positions change on reflow
        but activity child nodes inside remain static MUST be fixed
      - Layout picker changes (FOB-34) MUST also re-run the full compound layout including
        children, not only the outer graph topology
    Note: for layouts other than ELK (dagre, cola, etc.) compound behaviour depends on
      each layout's compound support — graceful degradation is acceptable (boxes may not
      contain children but layout still runs without error)


  # ---------------------------------------------------------------------------
  # FOB-38 — Enhanced node visual styling
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-38 Node shapes, icons, and styles fit Mimir design language
    Given Maria opens any playbook in the graph view
    Then the canvas graph uses the following refined visual style for each entity type,
      inspired by the Mimir design system (Montserrat font, Bootstrap 5.3 pastel palette,
      rounded-rectangle button aesthetic, FontAwesome icons, no-overflow layout):

      Node shape — ALL entity types use the SAME shape: round-rectangle
        (matching Mimir's rounded-corner button aesthetic for visual consistency);
        differentiation between node types is achieved through colour and icon, not shape:
        | entity type | shape           | min-width | min-height |
        | Playbook    | round-rectangle | 120px     | 44px       |
        | Workflow    | round-rectangle | 120px     | 40px       |
        | Activity    | round-rectangle | 110px     | 38px       |
        | Artifact    | round-rectangle | 90px      | 32px       |
        | Skill       | round-rectangle | 90px      | 32px       |
        | Agent       | round-rectangle | 90px      | 32px       |
        | Rule        | round-rectangle | 90px      | 32px       |

      Node icons — each node renders a FontAwesome icon (same icons as Mimir top-nav),
        displayed left-of-label using Cytoscape label content with Unicode glyphs;
        the icon font-family must be "Font Awesome 6 Free" (weight 900 for solid icons);
        icon and label text are composed as a single Cytoscape "label" using a newline or
        a combined unicode + space + name string — the icon MUST remain a stable fixed size
        (12–14px) while the node text can shrink; icon must never overflow the node boundary:
        | entity type | FA icon class              | Unicode glyph |
        | Playbook    | fa-solid fa-book-sparkles  | \ue4A5        |
        | Workflow    | fa-solid fa-diagram-project| \uf542        |
        | Activity    | fa-solid fa-bars-progress  | \ue0a3        |
        | Artifact    | fa-solid fa-gift           | \uf06b        |
        | Skill       | fa-solid fa-hand-holding-magic | \ue4BB    |
        | Agent       | fa-solid fa-brain-circuit  | \ue4d2        |
        | Rule        | fa-solid fa-scale-balanced | \uf24e        |

      Node colours — pastel Bootstrap 5.3-derived tints (lighter, softer than previous
        saturated palette) so icons and labels remain legible with dark text:
        | entity type | background  | border      | label/icon colour |
        | Playbook    | #e0cffc     | #9461fb     | #3d0a91           |
        | Workflow    | #cfe2ff     | #9ec5fe     | #084298           |
        | Activity    | #d1e7dd     | #a3cfbb     | #0a3622           |
        | Artifact    | #fff3cd     | #ffda6a     | #664d03           |
        | Skill       | #ffe5d0     | #fecba1     | #6e1d0b           |
        | Agent       | #cff4fc     | #9eeaf9     | #055160           |
        | Rule        | #e2e3e5     | #c4c8cb     | #2b2d2f           |

      Edge colour — ALL edges (regardless of relationship type) MUST use a single
        uniform colour: black (#000000 or #212529);
        the per-edge-type colour scheme used in previous versions MUST be removed;
        edge width: 1.5px for all types; dashed/dotted line styles per edge type are
        acceptable for visual differentiation but colour is always black

      Typography (all nodes):
        | property       | value                                                    |
        | font-family    | Montserrat, system-ui (matches Mimir site font)          |
        | font-size      | 11px (default for all nodes; see FOB-39 for size toggle) |
        | font-weight    | 600 for Playbook/Workflow/Activity; 400 for resources    |
        | text-wrap      | wrap                                                     |
        | text-overflow  | ellipsis (single line) — text MUST NOT overflow node box |
        | text-max-width | node width − 16px (8px padding each side)               |

      No-overflow rule — icon and label content MUST be visually contained within the
        node boundary at all zoom levels; Cytoscape clip-shape "node" must be applied;
        long names that exceed node width MUST be truncated with ellipsis, not overflow

      Border and depth:
        | property           | value                             |
        | border-width       | 2px for all nodes                 |
        | border-opacity     | 1                                 |
        | background-opacity | 1                                 |

      Hover / selection states:
        | state     | style                                                        |
        | selected  | 3px ring in #dc3545 (danger red)                             |
        | dimmed    | opacity 0.2 (phase filter / search)                          |
        | hover     | border-width 3px, same entity border colour                  |

    And the Playbook root node is visually the most prominent element on the canvas
      (Playbook background #e0cffc is deepest purple-tint, slightly larger min-size)
    And all edges are black (#212529) so the graph reads as clean diagram lines
    And the overall palette reads as a coherent pastel set, all drawn from Bootstrap 5.3
      tint colours, matching the rest of the Mimir UI

    Note: shapes are set via the Cytoscape.js stylesheet "shape" property; round-rectangle
      is natively supported in Cytoscape.js 3.x without additional plugins
    Note: Montserrat and Font Awesome must already be loaded by the page — both are loaded
      via Mimir's Google Fonts / CDN imports in base.html; no additional CDN entry needed
    Note: FontAwesome Unicode glyphs in Cytoscape require that the font-family of the label
      be set to "Font Awesome 6 Free" (weight 900) — the icon and label text can be composed
      as a two-line label (icon on line 1, name on line 2) using "\n" as separator
    Note: if exact FA Unicode values need verification, reference the FA6 icon search at
      fontawesome.com/search — the glyphs listed above are the correct solid icon codes


  # ---------------------------------------------------------------------------
  # FOB-39 — Node size mode toggle
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-39 Node size mode toggle — uniform size vs auto-width
    Given Maria is on the graph view canvas with a playbook loaded
    Then a node-size-mode toggle button (data-testid="browser-node-size-toggle") is visible
      in the canvas controls toolbar
    And the button label reads "Auto-width" in default mode (text-size-fixed)
    And the button label reads "Fixed size" when in fixed-size mode

    When the graph is in "Fixed size" mode (default):
    Then ALL nodes have identical fixed dimensions:
      - structural nodes (Playbook, Workflow, Activity): min-width 120px, min-height 40px
      - resource nodes (Artifact, Skill, Agent, Rule): min-width 90px, min-height 32px
    And node label text is rendered with text-wrap: wrap and text-overflow: ellipsis
      so that long names that exceed the fixed node width are truncated with ellipsis
    And the font-size for labels remains at the standard size (11px for resources, 13px others)
    And each entity type is visually consistent — all Activity nodes are exactly the same size
      regardless of the length of their name

    When Maria clicks the node-size-mode toggle button (switches to "Auto-width" mode):
    Then the graph is rebuilt so that node widths expand to accommodate the full label text
      without truncation — each node is as wide as its longest text line requires
    And the font-size of ALL labels is held constant (same size as Fixed mode — no shrinking)
    And nodes with short names become narrower; nodes with long names become wider
    And the height of nodes remains fixed (min-height unchanged)
    And the layout algorithm re-runs automatically after switching modes so nodes are
      repositioned to fit their new widths without overlapping
    And the button label updates to reflect the active mode
    And the node-size-mode state is stored in the URL query param "nodesize"
      ("fixed" for Fixed size, "auto" for Auto-width; "fixed" is the default)

    When Maria clicks the toggle again (switches back to "Fixed size"):
    Then nodes revert to fixed dimensions and text truncation resumes
    And the layout re-runs again to reposition the now-narrower nodes
    And the "nodesize" URL param is removed (default "fixed" needs no param)

    Note: "Auto-width" mode is implemented by setting min-width to 0 and width to "label"
      in the Cytoscape stylesheet, which causes Cytoscape to compute each node's width from
      its label content; "Fixed size" mode sets explicit min-width values per node type
    Note: this toggle interacts with compound view (FOB-37) — in compound mode, node width
      changes must still be correct for child nodes inside compound boxes; the layout re-run
      after switching modes must also re-layout compound children (same requirement as FOB-37
      compound layout fix)
    Note: the toggle state must be preserved when entity-type filter, phase filter, seq toggle,
      or compound toggle changes — the rebuild triggered by those controls must respect the
      current node-size-mode

