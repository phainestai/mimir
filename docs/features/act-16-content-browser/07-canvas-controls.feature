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
    Given Maria is on the graph view canvas with custom layout mode enabled
    Then an edge routing button (data-testid="browser-routing-btn") is visible
      in the canvas controls toolbar alongside the layout picker
    And the button label shows the human-readable name of the currently active routing style
    And the button shows a chevron icon (▾) indicating it opens a dropdown
    When Maria clicks the edge routing button
    Then a dropdown panel (data-testid="browser-routing-dropdown") opens near the button
    And the dropdown lists the following options (all curve-style values supported by Cytoscape 3.x):
      | routing-key       | label                | Cytoscape curve-style |
      | bezier            | Bezier               | bezier                |
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
    Note: on page entry (FOB-63 default layout mode), routing is straight — the routing
      picker is hidden until custom layout is checked
    Note: in custom layout mode, if the "routing" URL param contains an unrecognised value,
      fall back to "bezier" silently
    Note: "haystack" forces straight bundled lines; it may look identical to
      "straight" on sparse graphs — this is expected behaviour


  # NOTE: FOB-CONTENT-BROWSER-36 (sequence edges toggle) REMOVED — superseded by FOB-51.
  # Predecessor edges are always visible; data-testid="browser-seq-toggle" is not in the DOM.

  # NOTE: FOB-CONTENT-BROWSER-37 (compound view toggle) REMOVED — superseded by FOB-61.
  # data-testid="browser-compound-toggle" is not in the DOM; use browser-compound-btn dropdown.


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
    Note: BUG FOB-50 — the layout re-run MUST be triggered after the stylesheet update so
      that node size changes are visible on the canvas; previously the stylesheet was updated
      but _runLayout() was not called — nodes remained at old fixed dimensions visually


  # ---------------------------------------------------------------------------
  # FOB-50 — Node size toggle must trigger layout reflow
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-50 Switching node size mode visibly repositions nodes on canvas
    Given Maria is on the graph view canvas with a playbook loaded in "Fixed size" mode
    When she clicks the node-size-mode toggle to switch to "Auto-width"
    Then the Cytoscape stylesheet is updated to use width="label" for all node types
    And _runLayout() is immediately called so nodes reposition to avoid overlap
    And the canvas visibly reflects the new node widths (wider nodes for long names)
    When she clicks the toggle again to switch back to "Fixed size"
    Then the stylesheet reverts to explicit fixed widths per node type
    And _runLayout() is called again so nodes reposition to their original uniform spacing
    And this reflow MUST happen whether compound view is on or off
    Note: the bug was that _applyNodeSizeToggle() called cy.style() to update the stylesheet
      but never called _runLayout() — the stylesheet change alone does not reposition nodes


  # ---------------------------------------------------------------------------
  # FOB-51 — Remove activity sequence (predecessor-order) edges toggle
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-51 Sequence edges toggle removed — predecessor edges are always visible
    Given Maria is on the graph view canvas with a playbook loaded
    Then the sequence toggle button (data-testid="browser-seq-toggle") is NOT present in the DOM
    And predecessor edges (relationship="predecessor") between activities are ALWAYS shown
    And there is no URL param "seq" — this param is removed from _parseUrlParams and _replaceCanonicalUrl
    And the _applySeqToggle, _updateSeqToggleBtn, _parseSeqParam, _seqEdgesOn functions are removed
    And all callers of _rebuildRespectingMode that previously depended on _seqEdgesOn are updated
      to always include predecessor edges (rebuild always uses the full edge set)
    Note: predecessor relationships are already defined via Activity.predecessor model field
      and surfaced in the graph API — the seq toggle was an additional redundant toggle that
      added edges purely based on workflow order numbers, which is not desired behaviour;
      predecessor edges shown are ONLY those explicitly set via the Activity.predecessor field


  # ---------------------------------------------------------------------------
  # FOB-52 — Flat mode: workflows connected to their activities via edges
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-52 In flat (ungrouped) mode workflows connect to their activities via edges
    Given Maria is on the graph view canvas with a playbook loaded in flat (not grouped) mode
    Then each Workflow node has visible edges connecting it to each of its Activity nodes
    And these "contains" edges are rendered as visible lines (NOT hidden) in flat mode
    And the edges run from Workflow node → Activity node with an arrowhead at the Activity end
    And in compound (grouped) mode these same "contains" edges are hidden (display:none)
      because the parent/child nesting already implies the relationship visually
    Note: BUG FOB-52 — previously "contains" edges (relationship="contains") were always
      hidden via the edge stylesheet regardless of compound state; in flat mode they MUST
      be shown so the graph is connected; the fix is to conditionally show "contains" edges
      in flat mode and hide them only in compound mode (update stylesheet per mode)


  # ---------------------------------------------------------------------------
  # FOB-53 — FontAwesome icons in Cytoscape node labels
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-53 Node type icons render correctly using FA6 Unicode glyphs
    Given Maria opens a playbook in the graph view
    Then each graph node displays a FontAwesome icon to the left of its label text
    And the icon is rendered as a Unicode character within the Cytoscape node label
    And the font-family for the node label MUST include "Font Awesome 6 Free" FIRST in the list
      followed by Montserrat and system-ui fallbacks
    And font-weight MUST be 900 (FA solid icons require weight 900 to render correctly)
    And the icon characters are:
      | entity type | Unicode | visible glyph          |
      | Playbook    | \uf5da  | fa-book-open-reader    |
      | Workflow    | \uf542  | fa-diagram-project     |
      | Activity    | \ue0a3  | fa-bars-progress       |
      | Artifact    | \uf06b  | fa-gift                |
      | Skill       | \uf544  | fa-hand-sparkles       |
      | Agent       | \ue0c4  | fa-robot               |
      | Rule        | \uf24e  | fa-scale-balanced      |
    And no node shows a blank rectangle or empty box in place of the icon
    Note: BUG FOB-53 — previously some icon codepoints were from FA6 Pro or did not
      exist in FA6 Free, causing blank rectangles to appear; all codepoints above are
      confirmed valid FA6 Free solid icons
    Note: the Cytoscape label function must compose icon glyph + space + node label string
      (e.g. ele => '\uf542 ' + ele.data('label')) — a plain string template literal
      like `${icon} data(label)` is NOT a Cytoscape data() mapper and renders literally


  # ---------------------------------------------------------------------------
  # FOB-54 — Compound mode workflow label always visible
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-54 Workflow name label is always visible above compound box in grouped mode
    Given Maria has activated compound (grouped) view
    Then each compound Workflow box displays the Workflow name as a label
    And the label is positioned ABOVE the top-left corner of the compound box boundary,
      floating in empty space above the box (not inside it, not overlapping child nodes)
    And the label is NOT clipped or hidden by any overflow or containment rule
    And Cytoscape's ":parent" selector is used to apply this label style
    And the text-valign is "top" and text-halign is "left" with text-margin-y: -20px
      and text-margin-x: 8px so the label clears the box border
    And the label has a white semi-transparent text-background (opacity 0.9, padding 4px)
      so it is readable against both the canvas background and any overlapping elements
    And the label is always the Workflow name from data('label') — NOT empty or undefined
    Note: BUG FOB-54 — previous implementation set _buildCompoundLabelStyle() with negative
      margin but the ":parent" selector in _cytoscapeCompoundStyle() may not have applied
      the label property at all; the fix must explicitly set 'label': ele => ele.data('label')
      on the :parent selector in addition to the margin and background properties


  # ---------------------------------------------------------------------------
  # FOB-55 — Canvas controls button layout: compact grouped rows
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-55 Canvas control buttons are compact and grouped by function in the bottom-right
    Given Maria is on the graph view canvas with a playbook loaded
    Then all canvas control buttons remain in the bottom-right corner of the canvas area
    And the buttons are approximately HALF the current size (use Bootstrap .btn-sm class or
      equivalent small sizing — no custom oversized buttons)
    And the buttons are arranged in compact rows grouped by function:
      Row 1 — Zoom controls:  [+] [−] [⊡]   (zoom in, zoom out, fit)
      Row 2 — Layout/Routing: [Layout ▾] [Routing ▾] [Re-plot]
      Row 3 — View modes:     [Custom layout ☐] [Grouping ▾] [Fixed size ✓] (Grouping and layout/routing pickers hidden until Custom layout is checked — FOB-63)
    And the button group container has data-testid="browser-controls-panel"
    And the overall footprint of the controls panel is compact enough that it does not
      obscure more than 15% of the canvas area at 1280×800 viewport
    Note: do NOT change data-testid values on existing buttons — tests depend on them


  # ---------------------------------------------------------------------------
  # FOB-56 — Full-screen canvas layout: no scroll, no gaps
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-56 Content browser page fills the viewport with no scrollbars or blank gaps
    Given Maria navigates to /browser/<pk>/
    Then the entire page fits within the browser viewport height (no vertical scrollbar)
    And there is NO visible gap between the top navigation bar and the top of the canvas area
    And there is NO visible gap between the bottom of the canvas area and the page footer (if any)
    And the canvas <div> (data-testid="browser-canvas") fills all available vertical space
      between the top nav and the bottom of the viewport using CSS flex or calc(100vh - navHeight)
    And the three-panel layout (left panel + canvas + detail panel) also fills full height
    And at viewport widths ≥ 1024px no horizontal scrollbar appears
    Note: the fix involves ensuring browser_graph.html and its wrapping Django template
      do not add extra padding/margin that creates gaps; the body and main container must
      use height: 100vh or a flex column that stretches to fill the viewport


  # ---------------------------------------------------------------------------
  # FOB-57 — Complete edge routing catalog
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-57 All Cytoscape curve-style values are available in the routing picker
    Given Maria has enabled custom layout mode and opens the edge routing dropdown
    Then the following routing options are available (ALL valid Cytoscape 3.x curve-style values):
      | routing-key       | label              | Cytoscape curve-style |
      | bezier            | Bezier             | bezier                |
      | unbundled-bezier  | Unbundled Bezier   | unbundled-bezier      |
      | straight          | Straight           | straight              |
      | taxi              | Orthogonal (Taxi)  | taxi                  |
      | haystack          | Haystack           | haystack              |
      | segments          | Segments           | segments              |
      | round-segments    | Round Segments     | round-segments        |
    And the routing-key "round-segments" maps to Cytoscape curve-style "round-segments"
      (previously stored as "round-seg" which is NOT a valid Cytoscape value — BUG FOB-57)
    And each routing option produces a visually distinct edge style on the canvas
    Note: BUG FOB-57 — the previous _ROUTING_CATALOG contained "round-seg" as both the key
      and the curve-style value; Cytoscape does not recognise "round-seg" — it silently falls
      back to bezier; the correct curve-style string is "round-segments"


  # ---------------------------------------------------------------------------
  # FOB-58 — Node font all-caps at certain zoom levels (rendering bug)
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-58 Canvas node labels never render in all-caps regardless of zoom level
    Given Maria is on the graph view canvas with a playbook loaded
    When Maria zooms in or out to any zoom level (0.2× to 5×)
    Then node labels retain their original mixed-case text at all zoom levels
    And no node label switches to ALL-CAPS rendering at any zoom level
    And node label font styling is explicitly protected against browser text-transform:
      - 'text-transform': 'none' is set on every node type selector in the Cytoscape stylesheet
      - 'min-zoomed-font-size': 8 is set in the Cytoscape initialization options
    And the compound parent (:parent) selector also explicitly sets 'text-transform': 'none'
    And the font-family for compound parent labels does NOT include 'Font Awesome 6 Free'
      (FA font is only needed for icon glyphs on leaf nodes, not for workflow name labels)
    Note: BUG FOB-58 — at certain zoom levels the canvas rendering switches font rendering
      path; without explicit 'text-transform: none', some browser/OS combinations render
      the label text in all-caps due to font synthesis or font hinting at extreme sizes.
      The font-weight: 900 combined with FA primary font-family may trigger all-caps at
      certain zoom thresholds. Fix: add explicit 'text-transform': 'none' to all node
      styles and set min-zoomed-font-size to prevent near-zero font rendering.


  # ---------------------------------------------------------------------------
  # FOB-59 — Add straight-triangle to edge routing catalog
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-59 Routing picker includes straight-triangle curve-style
    Given Maria has enabled custom layout mode and opens the edge routing dropdown
    Then the routing catalog includes the "straight-triangle" option:
      | routing-key       | label                | Cytoscape curve-style |
      | straight-triangle | Straight (Triangle)  | straight-triangle     |
    And selecting "Straight (Triangle)" renders edges as straight lines with
      a triangle/arrow head filling the line body (distinct visual from plain Straight)
    And the complete routing catalog is:
      | bezier | unbundled-bezier | straight | straight-triangle |
      | taxi | haystack | segments | round-segments |
    Note: BUG FOB-59 — the routing catalog was missing 'straight-triangle', a valid
      Cytoscape 3.x curve-style that renders a filled triangle along the edge.


  # ---------------------------------------------------------------------------
  # FOB-60 — Compound node label visibility, font size, and activity colour
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-60 Compound node labels are always visible with distinct activity colouring
    Given Maria has activated compound (grouped) view at the "group by workflow" level
    Then each Workflow compound box displays its name as a visible label in the top-left
      corner INSIDE the compound boundary (within the top padding area, not outside the box)
    And the compound label font-size is 50% larger than the regular node font-size:
      - Regular node font-size: 13px
      - Compound label font-size: 20px (≈ 1.5× base, expressed as an integer pixel value)
    And the compound label uses 'font-family': 'Montserrat, system-ui' WITHOUT 'Font Awesome 6 Free'
      (icon glyphs are not needed for parent compound labels)
    And the compound label has a white semi-transparent text-background
      (text-background-color: '#ffffff', text-background-opacity: 0.85, text-background-padding: '4px')
    And the Cytoscape ':parent' selector explicitly sets 'text-transform': 'none'
    And the compound background uses 'padding-top': '28px' to create space for the label
      so that 'text-valign': 'top' positions the label within the top padding strip,
      not overlapping child nodes
    And in "group by workflow AND activity" mode, Activity compound nodes that contain
      resource nodes (skills, agents, rules, artifacts) use a DIFFERENT background colour
      from workflow compound nodes:
      - Workflow compound:  background '#eef2ff' (light periwinkle)
      - Activity compound:  background '#d4edda' (light mint-green)
    And both compound types display their label in the same font style
    Note: BUG FOB-60 — the previous _cytoscapeCompoundStyle() set text-margin-y: -14 which
      was insufficient to push the label above the compound box border reliably. Replace with
      padding-top approach: compound nodes get extra padding-top so the label anchor (text-valign:top)
      lands in the visible padding strip. The :parent selector must also set font-family to
      Montserrat (without FA) and font-size: 20px.


  # ---------------------------------------------------------------------------
  # FOB-61 — 3-level compound grouping context menu
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-61 Compound grouping button becomes a 3-option context menu
    Given Maria is on the graph view canvas with a playbook loaded
    Then the compound toggle button (data-testid="browser-compound-toggle") is replaced by
      a context menu button labelled "Grouping ▾" (data-testid="browser-compound-btn")
    And clicking it opens a dropdown with exactly 3 options:
      | option-key          | label                          | data-testid                              |
      | none                | No Grouping                    | browser-compound-option-none             |
      | workflow            | Group by Workflow              | browser-compound-option-workflow         |
      | workflow-activity   | Group by Workflow & Activity   | browser-compound-option-workflow-activity|
    And the currently active option is indicated with a checkmark (✓) in the dropdown
    And the button label updates to reflect the active option, e.g. "No Grouping ▾"
    And selecting "No Grouping" renders the graph in flat mode (all nodes are leaf nodes,
      no compound boxes), identical to the previous _compoundViewOn = false state
    And selecting "Group by Workflow" renders workflows as compound parent boxes containing
      their activities and connected resource nodes — identical to the previous _compoundViewOn = true
    And selecting "Group by Workflow & Activity" renders TWO levels of compound nesting:
      - Workflows are compound parents for all their activities and resources (same as above)
      - Activities that have connected resource nodes (skills, agents, artifacts, rules)
        ALSO become compound parent nodes containing those resource nodes
      - Activity compound nodes have a distinct background colour from workflow nodes:
          Workflow compound: '#eef2ff' (light periwinkle)
          Activity compound: '#d4edda' (light mint-green)
    And the URL parameter 'compound' encodes the three levels:
      compound=none | compound=workflow | compound=workflow-activity
    And the URL param is updated on every selection without a page reload
    And the graph re-builds (remove + re-add elements + re-layout) on every selection change
    And the module-level variable tracking grouping state is '_compoundLevel' (string enum),
      NOT the old boolean '_compoundViewOn' (which is removed)
    And window._compoundLevel is exposed via Object.defineProperty for E2E test access
    Note: FEATURE FOB-61 — replaces the previous single boolean compound toggle with
      a 3-state context menu following the same pattern as the layout and routing dropdowns.
      The boolean _compoundViewOn must be replaced with _compoundLevel ∈ {none, workflow, workflow-activity}.
      All references to _compoundViewOn must be updated or removed.


  # ---------------------------------------------------------------------------
  # FOB-62 — Node text and icon overflow fix
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-62 Node text and icons never overflow or clip in any size mode
    Given Maria is on the graph view canvas with a playbook loaded
    When the node size mode is "Fixed size" (uniform nodes, fixed 120px wide)
    Then all node labels are contained within their node boundaries
    And the icon (FA glyph) is NEVER clipped or partially hidden by the node boundary
    And long node labels are truncated with an ellipsis ONLY on the TEXT part, NOT on the icon:
      - Icon: always fully visible at the left side of the label
      - Text: truncated with '...' if it exceeds available width after the icon
    And when the node size mode is "Auto width" (label-driven sizing)
    Then nodes expand horizontally to fit the full label text without truncation
    And the icon is always fully visible
    And the node height adjusts to fit multi-line text if the label is very long
    And in both modes, the 'text-max-width' constraint is removed or set to 'none' in auto mode
      so that auto-width nodes are not artificially truncated
    And toggling between modes triggers a visible re-layout (nodes reposition)
    Note: BUG FOB-62 — the current _buildEnhancedNodeStyle() sets 'text-max-width': 108
      which clips both icon and text even in auto-width mode. In fixed mode, the icon
      glyph at the start of the label is clipped when the full label exceeds text-max-width.
      Fix: split sizing into two code paths — fixed mode keeps width:120 with text-max-width
      applied only to the TEXT portion after the icon; auto mode sets width:'label' and
      removes text-max-width entirely.



  # ---------------------------------------------------------------------------
  # FOB-63 — Default layout mode vs custom layout mode toggle
  # ---------------------------------------------------------------------------

  Scenario: FOB-CONTENT-BROWSER-63 Custom layout toggle controls visibility of layout/edge/grouping buttons
    Given Maria opens any playbook in the Content Browser
    Then on page entry the canvas is in "default layout mode" (custom layout checkbox is unchecked)
    And in default layout mode the following settings are automatically applied:
      | setting   | value                                |
      | layout    | Klay                                 |
      | edge style | Straight                            |
      | grouping  | Group by workflow + activity         |
    And the following buttons are hidden in default layout mode:
      | button               | data-testid               |
      | Layout picker        | browser-layout-btn        |
      | Edge routing picker  | browser-routing-btn       |
      | Grouping picker      | browser-compound-btn      |
    And a "Custom layout" checkbox (data-testid="browser-custom-layout-toggle") is always visible
      in the canvas controls area and is unchecked on page entry
    And the Node size toggle, Re-plot, and Zoom buttons remain visible in default layout mode

    When Maria ticks the "Custom layout" checkbox
    Then the canvas switches to "custom layout mode"
    And the Layout picker, Edge routing picker, and Grouping picker buttons become visible
    And the currently applied layout/edge style/grouping are NOT changed by the toggle itself
      (they stay at the defaults that were applied on entry, or whatever the user last set)
    And Maria can use the now-visible buttons to freely change layout, edge style, and grouping

    When Maria unticks the "Custom layout" checkbox
    Then the canvas returns to default layout mode
    And the default settings are re-applied:
      layout = Klay, edge style = Straight, grouping = Group by workflow + activity
    And the Layout picker, Edge routing picker, and Grouping picker buttons are hidden again

    Note: The default mode settings are ALWAYS applied on page load regardless of any URL
      query params — the checkbox starts unchecked and defaults are enforced immediately.
    Note: "Custom layout" in the URL is not persisted — page reload always resets to default mode.
    Note: data-testid="browser-custom-layout-toggle" is the <input type="checkbox"> element itself.
