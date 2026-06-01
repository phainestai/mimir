/**
 * content-browser.js — Content Browser client-side logic.
 *
 * Responsibilities:
 *   1. Read playbook PK from DOM on init
 *   2. Manage URL state via History API (pushState / replaceState)
 *   3. Normalise URL params on load (drop unknown types, drop stale phase IDs)
 *   4. Fetch graph data from /api/playbooks/<pk>/graph/ (implemented in graph iteration)
 *   5. Initialise Cytoscape.js and render graph (implemented in graph iteration)
 *
 * This file is plain browser JS. No build step, no framework, no import/export.
 * Loaded via <script> tag in browser_graph.html after CDN guard check.
 */

'use strict';

const _ALL_TYPES = ['workflow', 'activity', 'skill', 'agent', 'artifact', 'rule', 'phase'];

// ─── Module-level filter + search state ──────────────────────────────────────
// Mutated by _applyFilters / _applySearch; read by _openDetailPanel / _closeDetailPanel.
let _currentFilters = { types: _ALL_TYPES.slice(), phases: [] };

/**
 * Full graph element snapshot from the last successful API fetch.
 * Used as the authoritative source when rebuilding cy after entity-type filter changes.
 * Shape: { nodes: object[], edges: object[] }
 *
 * @type {{ nodes: object[], edges: object[] } | null}
 */
let _fullGraphData = null;
let _currentSearchTerm = '';
let _searchDebounceTimer = null;
let _currentLayout = 'layered'; // 'layered' | 'mrtree'

/**
 * Read the playbook PK from the #browser-root data attribute.
 * Returns null if no PK is set (empty state: /browser/).
 *
 * @returns {number|null}
 */
function _getPlaybookPk() {
  const root = document.getElementById('browser-root');
  const raw = root ? root.dataset.playbookPk : '';
  return raw ? parseInt(raw, 10) : null;
}

/**
 * Read the phase list from the #browser-root data-playbook-phases attribute.
 * Returns an array of {id, name} objects.
 *
 * @returns {{ id: number, name: string }[]}
 */
function _getPlaybookPhases() {
  const root = document.getElementById('browser-root');
  try {
    return JSON.parse(root ? root.dataset.playbookPhases || '[]' : '[]');
  } catch (_) {
    return [];
  }
}

/**
 * Parse URL query params into a structured filters object.
 * Normalises on read:
 *   - Unknown type values are discarded
 *   - Empty types param → all entity types active (not zero)
 *   - Phase IDs that are not positive integers are discarded
 *
 * @returns {{ types: string[], phases: number[] }}
 */
function _parseUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const typesRaw = params.get('types');
  const phasesRaw = params.get('phases');
  const layoutRaw = params.get('layout');

  let types;
  if (typesRaw === null || typesRaw === '') {
    types = _ALL_TYPES.slice();
  } else {
    types = typesRaw.split(',').filter(t => _ALL_TYPES.includes(t));
    if (types.length === 0) types = _ALL_TYPES.slice();
  }

  const phases = phasesRaw
    ? phasesRaw.split(',')
        .map(s => parseInt(s, 10))
        .filter(n => Number.isFinite(n) && n >= 0)
    : [];

  if (layoutRaw === 'mrtree' || layoutRaw === 'layered') {
    _currentLayout = layoutRaw;
  }

  return { types, phases };
}

/**
 * Validate parsed filters against the loaded playbook data.
 * Drops phase IDs not present in the playbook's phases array.
 * Rewrites the URL to canonical form (removes invalid/default params).
 *
 * @param {{ types: string[], phases: number[] }} filters
 * @param {{ id: number, name: string }[]} playbookPhases
 * @returns {{ types: string[], phases: number[] }} validated filters
 */
function _normaliseFilters(filters, playbookPhases) {
  const validPhaseIds = new Set(playbookPhases.map(p => p.id));
  // 0 is the "Unphased" sentinel — always valid when the playbook has ≥1 phase.
  const hasPhases = playbookPhases.length > 0;
  const cleanPhases = filters.phases.filter(id => (id === 0 && hasPhases) || validPhaseIds.has(id));
  const normalised = { types: filters.types, phases: cleanPhases };
  _replaceCanonicalUrl(_getPlaybookPk(), normalised);
  return normalised;
}

/**
 * Serialise a filters object back to URL query string.
 * Clean URL rules: omit types param if all entity types are active;
 * omit phases param if no phase filter is active.
 *
 * @param {{ types: string[], phases: number[] }} filters
 * @returns {string} query string including leading '?' or '' if empty
 */
function _filtersToQueryString(filters) {
  const parts = [];
  const FILTERABLE = ['workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
  const allActive = FILTERABLE.every(t => filters.types.includes(t));
  if (!allActive && filters.types.length > 0) {
    const encodable = filters.types.filter(t => FILTERABLE.includes(t));
    if (encodable.length > 0 && encodable.length < FILTERABLE.length) {
      parts.push('types=' + encodable.join(','));
    }
  }
  if (filters.phases.length > 0) {
    parts.push('phases=' + filters.phases.join(','));
  }
  if (_currentLayout !== 'layered') {
    parts.push('layout=' + _currentLayout);
  }
  return parts.length ? '?' + parts.join('&') : '';
}

/**
 * Update the browser URL when the active playbook changes.
 * Uses pushState so the back button returns to the previous playbook.
 * Resets phase filters on switch (phase IDs are playbook-scoped).
 *
 * @param {number} pk - New playbook PK
 * @param {{ types: string[], phases: number[] }} filters - Current filter state
 */
function _pushPlaybookUrl(pk, filters) {
  const resetFilters = { types: filters.types, phases: [] };
  const qs = _filtersToQueryString(resetFilters);
  const url = '/browser/' + pk + '/' + qs;
  history.pushState({ pk: pk, filters: resetFilters }, '', url);
}

/**
 * Replace the current URL with the canonical form of the current state.
 * Used during init to clean up invalid params without creating a history entry.
 *
 * @param {number|null} pk
 * @param {{ types: string[], phases: number[] }} filters
 */
function _replaceCanonicalUrl(pk, filters) {
  const qs = _filtersToQueryString(filters);
  const url = pk ? '/browser/' + pk + '/' + qs : '/browser/';
  history.replaceState({ pk: pk, filters: filters }, '', url);
}

/**
 * Handle browser back/forward navigation (popstate event).
 * Reads the new URL state and re-fetches graph or shows empty state.
 *
 * @param {PopStateEvent} event
 */
function _onPopState(event) {
  const pk = _getPkFromPath();
  if (!pk) {
    _showEmptyState();
    return;
  }
  const filters = _parseUrlParams();
  _fetchGraph(pk).then(() => _applyFilters(filters));
}

/**
 * Extract playbook PK from the current URL path.
 * @returns {number|null}
 */
function _getPkFromPath() {
  const match = window.location.pathname.match(/^\/browser\/(\d+)\/$/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Show the empty state canvas card (no playbook selected).
 */
function _showEmptyState() {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (empty) empty.classList.remove('d-none');
  if (loading) loading.classList.add('d-none');
  if (error) error.classList.add('d-none');
}

/**
 * Show the loading spinner on the canvas.
 */
function _showLoadingState() {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (empty) empty.classList.add('d-none');
  if (loading) loading.classList.remove('d-none');
  if (error) error.classList.add('d-none');
}

/**
 * Show the error state canvas card with an optional message.
 *
 * @param {string} [message='Could not load graph data.']
 */
function _showErrorState(message) {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const errorEl = document.querySelector('[data-testid="browser-error-state"]');
  const msgEl = errorEl ? errorEl.querySelector('p') : null;
  if (empty) empty.classList.add('d-none');
  if (loading) loading.classList.add('d-none');
  if (errorEl) {
    errorEl.classList.remove('d-none');
    if (msgEl) msgEl.textContent = message || 'Could not load graph data.';
  }
}

// AbortController for in-flight graph fetch — aborted on playbook switch.
let _currentAbortController = null;

/**
 * Fetch graph data from the API, show loading state first, render on success.
 * Handles: 401 (session expired → redirect to login), 404, network errors.
 *
 * @param {number} pk
 */
async function _fetchGraph(pk) {
  if (_currentAbortController) {
    _currentAbortController.abort();
  }
  _currentAbortController = new AbortController();
  _showLoadingState();

  try {
    const response = await fetch(`/api/playbooks/${pk}/graph/`, {
      signal: _currentAbortController.signal,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      // Non-JSON response usually means Django returned a login redirect page.
      window.location.href = '/auth/login/?next=' + encodeURIComponent('/browser/' + pk + '/');
      return;
    }
    if (response.status === 404) {
      _showErrorState('This playbook is no longer available.');
      return;
    }
    if (!response.ok) {
      _showErrorState('Could not load graph data.');
      return;
    }

    const data = await response.json();
    _fullGraphData = { nodes: data.nodes || [], edges: data.edges || [] };
    const filters = _parseUrlParams();
    _renderGraph(pk, data, filters);
    _updatePlaybookHeader(pk, data.playbook_name || '', data.playbook_status || '');
  } catch (err) {
    if (err.name === 'AbortError') return;
    _showErrorState('Could not load graph data.');
  }
}

/**
 * Initialise (or re-initialise) Cytoscape with fetched graph data.
 * Destroys any existing cy instance before mounting a new one.
 *
 * @param {number} pk - Playbook PK (used for "Go to Playbook" link)
 * @param {{ nodes: object[], edges: object[], phases: object[] }} graphData
 * @param {{ types: string[], phases: number[] }} filters
 */
function _renderGraph(pk, graphData, filters) {
  if (window.cy) {
    window.cy.destroy();
    window.cy = null;
  }

  const container = document.getElementById('cy');
  if (!container) return;

  const { nodes, edges } = graphData;

  // Empty playbook — show no-content state, not the canvas.
  if (nodes.length === 0) {
    _showNoContentState(pk);
    return;
  }

  // Node count badge (always shows total, not filtered).
  const countBadge = document.querySelector('[data-testid="browser-node-count"]');
  if (countBadge) countBadge.textContent = `${nodes.length} nodes`;

  // Build initial elements respecting URL type-filter params so the first render
  // is already correct — avoids a redundant remove+re-add cycle after cy creation.
  _currentFilters = filters;
  const elements = _buildFilteredElements(new Set(filters.types));

  const elkLayout = {
    name: 'elk',
    elk: {
      algorithm: _currentLayout,
      'elk.direction': 'DOWN',
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
      'elk.spacing.nodeNode': 50,
      'elk.layered.spacing.nodeNodeBetweenLayers': 70,
      'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
    },
    padding: 30,
  };
  const dagreLayout = {
    name: 'dagre', rankDir: 'TB', nodeSep: 50, rankSep: 70,
    edgeSep: 10, ranker: 'network-simplex', padding: 30,
  };
  const breadthfirstLayout = { name: 'breadthfirst', directed: true, padding: 20, spacingFactor: 1.5 };

  const tryLayout = (layout) => cytoscape({ container, elements, style: _cytoscapeStyle(), layout, minZoom: 0.1, maxZoom: 3 });

  try {
    window.cy = tryLayout(elkLayout);
  } catch (_elkErr) {
    try {
      window.cy = tryLayout(dagreLayout);
    } catch (_dagreErr) {
      window.cy = tryLayout(breadthfirstLayout);
    }
  }

  // Hide overlay states, make canvas visible.
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const noContent = document.querySelector('[data-testid="browser-no-content-state"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (loading) loading.classList.add('d-none');
  if (empty) empty.classList.add('d-none');
  if (noContent) noContent.classList.add('d-none');
  if (error) error.classList.add('d-none');

  // Wire node tap → detail panel.
  window.cy.on('tap', 'node', function(evt) { _openDetailPanel(evt.target); });
  // Canvas background tap → close panel; edges do nothing.
  window.cy.on('tap', function(evt) {
    if (evt.target === window.cy) { _closeDetailPanel(); }
  });
  // Track layout completion count (used by E2E tests to wait for ELK to finish).
  window.cy.on('layoutstop', function() {
    window._elkLayoutCount = (window._elkLayoutCount || 0) + 1;
  });

  // Apply phase/search dim (no type rebuild — cy was created with correct elements).
  _refreshVisualState();

  // Render entity-type filter toolbar after graph loads (counts won't change).
  _renderFilterToolbar(filters);
}

/**
 * Return the Cytoscape stylesheet array.
 * Node labels are set via 'content' property (plain text — no innerHTML).
 *
 * @returns {object[]}
 */
function _cytoscapeStyle() {
  const _nodeBase = {
    'label': 'data(label)',
    'text-valign': 'center',
    'text-halign': 'center',
    'font-size': 11,
    'text-wrap': 'wrap',
    'text-max-width': 110,
    'width': 120,
    'height': 40,
    'color': '#fff',
  };
  return [
    { selector: 'node[type = "workflow"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const abbr = ele.data('meta') && ele.data('meta').abbreviation;
                 return abbr ? `${abbr}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': '#0d6efd', 'shape': 'round-rectangle',
               'width': 130, 'height': 50, 'font-size': 10 } },
    { selector: 'node[type = "activity"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const code = ele.data('meta') && ele.data('meta').display_code;
                 return code ? `${code}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': '#198754', 'shape': 'round-rectangle',
               'height': 50, 'font-size': 10, 'text-max-width': 110 } },
    { selector: 'node[type = "artifact"]',
      style: { ..._nodeBase, 'background-color': '#ffc107', 'shape': 'ellipse', 'color': '#212529' } },
    { selector: 'node[type = "skill"]',
      style: { ..._nodeBase, 'background-color': '#fd7e14', 'shape': 'ellipse' } },
    { selector: 'node[type = "agent"]',
      style: { ..._nodeBase, 'background-color': '#0dcaf0', 'shape': 'ellipse', 'color': '#212529' } },
    { selector: 'node[type = "rule"]',
      style: { ..._nodeBase, 'background-color': '#6c757d', 'shape': 'ellipse' } },
    { selector: 'node:selected',
      style: { 'border-width': 3, 'border-color': '#dc3545' } },
    // Edges — taxi (right-angle) routing for clean hierarchical layout.
    // 'contains' and 'predecessor' use downward/auto taxi; resource edges use
    // a shorter turn so they branch off activities cleanly.
    { selector: 'edge[relationship = "contains"]',
      style: { 'line-color': '#0d6efd', 'target-arrow-color': '#0d6efd', 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%', 'width': 2 } },
    { selector: 'edge[relationship = "predecessor"]',
      style: { 'line-color': '#198754', 'target-arrow-color': '#198754', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'auto', 'taxi-turn': '50%',
               'width': 1, 'opacity': 0.7 } },
    { selector: 'edge[relationship = "sequence"]',
      style: { 'line-color': '#343a40', 'target-arrow-color': '#343a40', 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%',
               'width': 2, 'opacity': 0.55 } },
    { selector: 'edge[relationship = "produces"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "consumes"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5, 'opacity': 0.8 } },
    { selector: 'edge[relationship = "uses_skill"]',
      style: { 'line-color': '#fd7e14', 'target-arrow-color': '#fd7e14', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "assigned_agent"]',
      style: { 'line-color': '#0dcaf0', 'target-arrow-color': '#0dcaf0', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "governed_by_rule"]',
      style: { 'line-color': '#6c757d', 'target-arrow-color': '#6c757d', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
  ];
}

/**
 * Apply filter state to the graph.
 * Stores state to _currentFilters and calls _refreshVisualState.
 * Also closes detail panel if the currently-selected node's type is now hidden.
 *
 * @param {{ types: string[], phases: number[] }} filters
 */
function _applyFilters(filters) {
  _currentFilters = filters;
  _applyTypeRebuild(new Set(filters.types));
  _refreshVisualState();
  // Close panel if the selected node's type is now excluded.
  if (_currentPanelNode) {
    const activeTypes = new Set(filters.types);
    if (!activeTypes.has(_currentPanelNode.data('type'))) {
      _closeDetailPanel();
    }
  }
}

/**
 * Rebuild the Cytoscape element set to include only nodes of the active types,
 * plus any edges whose both endpoints are in the active set.
 * After rebuilding, automatically re-runs the current ELK layout.
 *
 * Only entity-type filtering causes a rebuild. Phase filter and search use
 * the dim model (_refreshVisualState) and do NOT trigger a rebuild.
 *
 * @param {Set<string>} activeTypes - set of type strings that should be present in cy
 */
function _applyTypeRebuild(activeTypes) {
  if (!window.cy || !_fullGraphData) return;
  const elements = _buildFilteredElements(activeTypes);
  window.cy.remove(window.cy.elements());
  window.cy.add(elements);
  _runElkLayout();
}

/**
 * From _fullGraphData, return the Cytoscape element array (nodes + edges) for
 * the given set of active types. Orphaned resource nodes (nodes whose type is
 * active but whose Activity parent was excluded) are also removed.
 *
 * @param {Set<string>} activeTypes
 * @returns {{ data: object }[]}
 */
function _buildFilteredElements(activeTypes) {
  if (!_fullGraphData) return [];
  const { nodes, edges } = _fullGraphData;
  const resourceTypes = new Set(['skill', 'agent', 'rule', 'artifact']);

  // Step 1: Keep nodes whose type is active.
  const typeFilteredNodes = nodes.filter(n => activeTypes.has(n.type));
  const typeFilteredIds = new Set(typeFilteredNodes.map(n => n.id));

  // Step 2: Filter edges — both endpoints must remain.
  const filteredEdges = edges.filter(e => typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target));

  // Step 3: Find all node IDs that have at least one edge.
  const connectedIds = new Set();
  filteredEdges.forEach(e => { connectedIds.add(e.source); connectedIds.add(e.target); });

  // Step 4: Remove orphaned resource nodes (active type but no remaining edges).
  const finalNodes = typeFilteredNodes.filter(n => !resourceTypes.has(n.type) || connectedIds.has(n.id));
  const finalIds = new Set(finalNodes.map(n => n.id));

  // Step 5: Re-filter edges for the final node set.
  const finalEdges = filteredEdges.filter(e => finalIds.has(e.source) && finalIds.has(e.target));

  return [
    ...finalNodes.map(n => ({ data: n })),
    ...finalEdges.map(e => ({ data: e })),
  ];
}

/**
 * Apply the combined visual state (entity type visibility, phase dim, search dim)
 * to all canvas nodes and edges. Also re-renders the structural tree and phase filter
 * controls so they stay in sync with the active filter.
 */
function _refreshVisualState() {
  if (!window.cy) return;
  const activePhases = _currentFilters.phases.length > 0 ? new Set(_currentFilters.phases) : null;
  const searchLower = _currentSearchTerm.toLowerCase().trim();

  // All nodes in cy are of active types (excluded types are removed by _applyTypeRebuild).
  // This pass applies phase-dim and search-dim only.
  window.cy.nodes().forEach(node => {
    const nodeType = node.data('type');
    let dimmed = false;
    // Phase dim — activity nodes only; 0 = unphased sentinel
    if (activePhases && nodeType === 'activity') {
      const meta = node.data('meta') || {};
      const phaseId = meta.phase_id != null ? meta.phase_id : 0;
      if (!activePhases.has(phaseId)) dimmed = true;
    }
    // Search dim — all nodes; edges are NOT dimmed by search (per FOB-12)
    if (searchLower) {
      const label = (node.data('label') || '').toLowerCase();
      if (!label.includes(searchLower)) dimmed = true;
    }
    node.style({ visibility: 'visible', opacity: dimmed ? 0.2 : 1 });
  });

  window.cy.edges().forEach(edge => {
    edge.style('visibility', 'visible');
    // Phase dim on edges connected to phase-dimmed activities (not search)
    if (activePhases) {
      const srcType = edge.source().data('type');
      const tgtType = edge.target().data('type');
      let edgeDimmed = false;
      if (srcType === 'activity') {
        const m = edge.source().data('meta') || {};
        const pid = m.phase_id != null ? m.phase_id : 0;
        if (!activePhases.has(pid)) edgeDimmed = true;
      }
      if (tgtType === 'activity') {
        const m = edge.target().data('meta') || {};
        const pid = m.phase_id != null ? m.phase_id : 0;
        if (!activePhases.has(pid)) edgeDimmed = true;
      }
      edge.style('opacity', edgeDimmed ? 0.2 : 1);
    } else {
      edge.style('opacity', 1);
    }
  });

  // Keep structural tree and phase filter controls in sync.
  _renderStructureTree();
  _renderPhaseFilter();
}

/**
 * Apply a name-based search term. Matching nodes are bright; others dimmed.
 * Edges are unaffected by search (per FOB-12).
 * Uses 250 ms debounce to avoid thrashing during typing.
 *
 * @param {string} term
 */
function _applySearch(term) {
  if (_searchDebounceTimer) clearTimeout(_searchDebounceTimer);
  _searchDebounceTimer = setTimeout(() => {
    _currentSearchTerm = term;
    _refreshVisualState();
  }, 250);
}

/**
 * Render the entity-type filter toolbar on the canvas.
 * One toggle button per type that has nodes; shows total count (static).
 * Called once after graph loads — recreated on playbook switch.
 *
 * @param {{ types: string[], phases: number[] }} filters
 */
function _renderFilterToolbar(filters) {
  const container = document.querySelector('[data-testid="browser-type-filter-row"]');
  if (!container || !window.cy) return;

  const displayTypes = ['workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
  const typeCounts = {};
  displayTypes.forEach(t => { typeCounts[t] = 0; });
  (_fullGraphData ? _fullGraphData.nodes : []).forEach(n => {
    if (n.type in typeCounts) typeCounts[n.type]++;
  });

  container.innerHTML = '';
  displayTypes.forEach(type => {
    if (typeCounts[type] === 0) return;
    const isActive = filters.types.includes(type);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `btn btn-sm ${isActive ? 'btn-secondary' : 'btn-outline-secondary'}`;
    btn.setAttribute('data-testid', 'browser-filter-btn');
    btn.setAttribute('data-filter-type', type);
    btn.title = `Toggle ${type} nodes`;
    const label = type.charAt(0).toUpperCase() + type.slice(1);
    btn.textContent = `${label} (${typeCounts[type]})`;
    btn.addEventListener('click', () => {
      const types = _currentFilters.types.slice();
      const idx = types.indexOf(type);
      if (idx >= 0) {
        types.splice(idx, 1);
      } else {
        types.push(type);
      }
      const newFilters = { ..._currentFilters, types };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
      _renderFilterToolbar(newFilters);
    });
    container.appendChild(btn);
  });
}

/**
 * Render phase filter pills in the canvas filter toolbar (second row).
 * Hidden entirely when the playbook has no phases.
 * Called from _refreshVisualState to stay in sync.
 */
function _renderPhaseFilter() {
  const playbookPhases = _getPlaybookPhases();
  const container = document.querySelector('[data-testid="browser-phase-filter"]');

  if (!container) return;
  if (playbookPhases.length === 0) {
    container.innerHTML = '';
    return;
  }

  const activePhases = new Set(_currentFilters.phases);
  const allPhaseIds = playbookPhases.map(p => p.id);
  // Include 0 (Unphased) as an option
  const phaseOptions = [{ id: 0, name: '(Unphased)' }, ...playbookPhases];

  container.innerHTML = '';
  phaseOptions.forEach(phase => {
    const isActive = activePhases.size === 0 || activePhases.has(phase.id);
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = `btn btn-sm me-1 mb-1 ${isActive ? 'btn-primary' : 'btn-outline-secondary'}`;
    pill.setAttribute('data-testid', 'browser-phase-pill');
    pill.setAttribute('data-phase-id', String(phase.id));
    pill.textContent = phase.name;
    pill.addEventListener('click', () => {
      let phases = _currentFilters.phases.slice();
      if (phases.length === 0) {
        phases = [phase.id];
      } else if (phases.includes(phase.id)) {
        phases = phases.filter(id => id !== phase.id);
        if (phases.length === 0) phases = [];
      } else {
        phases = phases.concat([phase.id]);
        if (phaseOptions.every(p => phases.includes(p.id))) phases = [];
      }
      const newFilters = { ..._currentFilters, phases };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
    });
    container.appendChild(pill);
  });

  // "All" reset button when filter is active
  if (activePhases.size > 0) {
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-sm btn-outline-danger mb-1';
    clearBtn.setAttribute('data-testid', 'browser-phase-clear');
    clearBtn.textContent = 'All';
    clearBtn.addEventListener('click', () => {
      const newFilters = { ..._currentFilters, phases: [] };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
    });
    container.appendChild(clearBtn);
  }
}

/**
 * Show "no content" overlay (empty playbook — graph API returned 0 nodes).
 *
 * @param {number} pk
 */
function _showNoContentState(pk) {
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const noContent = document.querySelector('[data-testid="browser-no-content-state"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (loading) loading.classList.add('d-none');
  if (empty) empty.classList.add('d-none');
  if (error) error.classList.add('d-none');
  if (noContent) {
    // Update the "Go to Playbook" link with the current PK.
    const link = noContent.querySelector('[data-testid="browser-go-to-playbook"]');
    if (link && pk) link.href = `/playbooks/${pk}/`;
    noContent.classList.remove('d-none');
  }
}

// ─── Detail panel state ───────────────────────────────────────────────────────
let _currentPanelNode = null;   // Cytoscape node currently shown in panel

/**
 * Build and render the Workflow → Activity collapsible tree in the left panel.
 * Called after each graph load. Tree rows navigate the canvas on click.
 */
function _renderStructureTree() {
  const container = document.querySelector('[data-testid="browser-structure-tree"]');
  if (!container || !window.cy) return;

  const activePhases = _currentFilters.phases.length > 0 ? new Set(_currentFilters.phases) : null;
  const wfNodes = window.cy.nodes('[type="workflow"]').sort((a, b) => a.data('entity_pk') - b.data('entity_pk'));
  if (wfNodes.length === 0) { container.innerHTML = ''; return; }

  let html = '<div class="small fw-semibold text-muted text-uppercase mb-1 mt-2">Structure</div>';
  wfNodes.forEach(wfNode => {
    const wfId    = wfNode.id();
    const abbr    = (wfNode.data('meta') || {}).abbreviation || '';
    const wfLabel = wfNode.data('label') || wfId;
    const sectionId = 'tree-wf-' + wfNode.data('entity_pk');

    // All activities ordered, then filtered by active phases
    let actNodes = wfNode.outgoers('edge[relationship="contains"]').targets()
      .sort((a, b) => ((a.data('meta') || {}).order || 0) - ((b.data('meta') || {}).order || 0));

    if (activePhases) {
      actNodes = actNodes.filter(actNode => {
        const meta = actNode.data('meta') || {};
        const phaseId = meta.phase_id != null ? meta.phase_id : 0;
        return activePhases.has(phaseId);
      });
      if (actNodes.length === 0) return; // skip this workflow when no activities match
    }

    html += `
      <div class="mb-1">
        <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-tree-row"
             data-node-id="${wfId}" data-testid="browser-tree-row" style="cursor:pointer;">
          <span class="browser-tree-toggle small text-muted" data-section="${sectionId}">▸</span>
          ${abbr ? `<span class="small text-muted" style="min-width:2.2em;">${abbr}</span>` : ''}
          <span class="small fw-semibold text-truncate" title="${wfLabel}">${wfLabel}</span>
        </div>
        <div id="${sectionId}" class="ps-3" style="display:none;">`;

    actNodes.forEach(actNode => {
      const actId    = actNode.id();
      const meta     = actNode.data('meta') || {};
      const code     = meta.display_code || '';
      const colour   = meta.phase_colour || '';
      const actLabel = actNode.data('label') || actId;

      const chip = colour
        ? `<span class="rounded-circle flex-shrink-0"
                style="width:8px;height:8px;background:${colour};display:inline-block;"></span>`
        : '';

      html += `
          <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-tree-row"
               data-node-id="${actId}" data-testid="browser-tree-row" style="cursor:pointer;">
            ${code ? `<span class="small text-muted" style="min-width:2.8em;">${code}</span>` : ''}
            <span class="small text-truncate flex-grow-1" title="${actLabel}">${actLabel}</span>
            ${chip}
          </div>`;
    });

    html += `</div></div>`;
  });

  container.innerHTML = html;

  // Wire clicks: pan/zoom canvas to the node (no detail panel open).
  container.querySelectorAll('[data-node-id]').forEach(row => {
    row.addEventListener('click', function(e) {
      e.stopPropagation();
      const nodeId = this.dataset.nodeId;

      // Toggle collapse for workflow rows only (workflow rows contain a toggle span)
      const toggleSpan = this.querySelector('.browser-tree-toggle');
      if (toggleSpan) {
        const sId = toggleSpan.dataset.section;
        _accordionWorkflow(sId);
        return; // collapse toggle — don't navigate
      }

      // Navigate canvas to this node.
      if (window.cy) {
        const node = window.cy.getElementById(nodeId);
        if (node && node.length) {
          window.cy.animate({ fit: { eles: node, padding: 80 }, duration: 300 });
        }
      }
    });
  });
}

/**
 * Cycle the ELK layout between 'layered' and 'mrtree'.
 * Re-runs layout on the existing cy instance without re-fetching.
 */
function _cycleLayout() {
  _currentLayout = _currentLayout === 'layered' ? 'mrtree' : 'layered';
  _updateLayoutBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  _runElkLayout();
}

/**
 * Run ELK layout on the current cy instance using _currentLayout algorithm.
 * Fits the graph to screen after layout completes.
 */
function _runElkLayout() {
  if (!window.cy) return;
  const layout = window.cy.layout({
    name: 'elk',
    elk: { algorithm: _currentLayout, 'elk.direction': 'DOWN' },
    padding: 30,
  });
  layout.one('layoutstop', () => { window.cy.fit(undefined, 40); });
  layout.run();
}

/**
 * Re-run ELK layout on the current cy instance using visible nodes only.
 * Useful after hiding node types or filtering, so freed space is reclaimed.
 */
function _replot() {
  _runElkLayout();
}

/**
 * Update the layout button label to reflect current mode.
 */
function _updateLayoutBtn() {
  const btn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (!btn) return;
  btn.textContent = _currentLayout === 'layered' ? 'Layered' : 'MTree';
}

/**
 * @param {string} sectionId - The id of the section div to expand (e.g. "tree-wf-3")
 */
function _accordionWorkflow(sectionId) {
  document.querySelectorAll('[data-testid="browser-structure-tree"] .browser-tree-toggle').forEach(span => {
    const sid = span.dataset.section;
    const section = document.getElementById(sid);
    if (!section) return;
    if (sid === sectionId) {
      section.style.display = '';
      span.textContent = '▾';
    } else {
      section.style.display = 'none';
      span.textContent = '▸';
    }
  });
}

/**
 * Highlight the tree row matching `nodeId` (bold + accent).
 * @param {string} nodeId
 */
function _highlightTreeNode(nodeId) {
  document.querySelectorAll('[data-testid="browser-tree-row"]').forEach(row => {
    if (row.dataset.nodeId === nodeId) {
      row.classList.add('fw-bold', 'text-primary', 'bg-primary-subtle');
    } else {
      row.classList.remove('fw-bold', 'text-primary', 'bg-primary-subtle');
    }
  });

  // Accordion: find the section this node belongs to and expand only it.
  const targetRow = document.querySelector(`[data-testid="browser-tree-row"][data-node-id="${nodeId}"]`);
  if (targetRow) {
    // Walk up to find the nearest parent section div (id starts with "tree-wf-")
    let el = targetRow.parentElement;
    while (el) {
      if (el.id && el.id.startsWith('tree-wf-')) {
        _accordionWorkflow(el.id);
        break;
      }
      el = el.parentElement;
    }
  }
}

/**
 * Clear all tree row highlights.
 */
function _clearTreeHighlight() {
  document.querySelectorAll('[data-testid="browser-tree-row"]').forEach(row => {
    row.classList.remove('fw-bold', 'text-primary', 'bg-primary-subtle');
  });
}

// ─── Resource tree ────────────────────────────────────────────────────────────

const _RESOURCE_ICONS = { artifact: '📦', skill: '🔧', agent: '🤖', rule: '📋' };
const _RESOURCE_ORDER = ['artifact', 'skill', 'agent', 'rule'];

/**
 * Render resource tree for a selected Workflow or Activity node.
 * Groups resource nodes by type, deduplicates by entity_pk.
 *
 * @param {cytoscape.NodeSingular} node
 */
function _renderResourceTree(node) {
  const container = document.querySelector('[data-testid="browser-resource-tree"]');
  if (!container || !window.cy) return;

  const nodeType = node.data('type');
  let activityNodes;

  if (nodeType === 'workflow') {
    activityNodes = node.outgoers('edge[relationship="contains"]').targets();
  } else if (nodeType === 'activity') {
    // FOB-28: show resources for the parent Workflow (all siblings), not just this activity.
    const parentWf = node.incomers('edge[relationship="contains"]').sources();
    if (parentWf && parentWf.length) {
      activityNodes = parentWf.outgoers('edge[relationship="contains"]').targets();
    } else {
      activityNodes = node; // fallback if orphaned activity
    }
  } else {
    return; // resource node clicked — keep existing tree (no change)
  }

  // Collect resource nodes connected to each activity; deduplicate by entity_pk within type.
  const grouped = {};
  _RESOURCE_ORDER.forEach(t => { grouped[t] = new Map(); }); // entity_pk → cy node

  activityNodes.forEach(actNode => {
    actNode.outgoers('node').forEach(rNode => {
      const rType = rNode.data('type');
      if (!_RESOURCE_ORDER.includes(rType)) return;
      const epk = rNode.data('entity_pk');
      if (!grouped[rType].has(epk)) grouped[rType].set(epk, rNode);
    });
  });

  const anyResources = _RESOURCE_ORDER.some(t => grouped[t].size > 0);
  if (!anyResources) {
    container.innerHTML = '<span class="small text-muted">No resources linked.</span>';
    return;
  }

  let html = '<div class="small fw-semibold text-muted text-uppercase mb-1">Resources</div>';
  _RESOURCE_ORDER.forEach(rType => {
    if (grouped[rType].size === 0) return;
    const label = rType.charAt(0).toUpperCase() + rType.slice(1) + 's';
    html += `<div class="small text-muted mt-1 mb-1">${label}</div>`;
    grouped[rType].forEach((rNode, _epk) => {
      const icon  = _RESOURCE_ICONS[rType] || '';
      const label = rNode.data('label') || '';
      const nId   = rNode.id();
      html += `
        <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-resource-row"
             data-node-id="${nId}" data-testid="browser-resource-row" style="cursor:pointer;"
             title="${label}">
          <span>${icon}</span>
          <span class="small text-truncate">${label}</span>
        </div>`;
    });
  });

  container.innerHTML = html;

  container.querySelectorAll('[data-node-id]').forEach(row => {
    row.addEventListener('click', function(e) {
      e.stopPropagation();
      const nodeId = this.dataset.nodeId;
      if (window.cy) {
        const rNode = window.cy.getElementById(nodeId);
        if (rNode && rNode.length) _openDetailPanel(rNode);
      }
    });
  });
}

/**
 * Clear the resource tree back to its default placeholder.
 */
function _clearResourceTree() {
  const container = document.querySelector('[data-testid="browser-resource-tree"]');
  if (container) container.innerHTML = '<span class="small text-muted">Select a Workflow to see its resources.</span>';
}

/**
 * Open (or replace content of) the detail panel for a given node.
 * Applies selection ring to the tapped node; dims all others.
 *
 * @param {cytoscape.NodeSingular} node
 */
function _openDetailPanel(node) {
  const panel = document.querySelector('[data-testid="browser-detail-panel"]');
  const panelContent = document.querySelector('[data-testid="browser-panel-content"]');
  const openTabBtn = document.querySelector('[data-testid="browser-panel-open-tab"]');
  const openFullBtn = document.querySelector('[data-testid="browser-panel-open-full"]');
  if (!panel || !panelContent) return;

  // Only apply canvas selection ring + dim when the node is actually visible.
  // FOB-32: resource nodes filtered out (visibility:hidden) open panel without canvas update.
  if (window.cy) {
    const nodeIsVisible = node.style('visibility') !== 'hidden';
    if (nodeIsVisible) {
      window.cy.nodes().forEach(n => {
        n.style('border-width', 0);
        if (n.style('visibility') !== 'hidden') n.style('opacity', 0.4);
      });
      node.style({ 'border-width': 3, 'border-color': '#dc3545', 'opacity': 1 });
    }
  }
  _currentPanelNode = node;

  // FOB-27: only highlight structural tree for Workflow / Activity nodes.
  // Resource entity types (skill, agent, artifact, rule) must NOT highlight tree rows.
  const nodeType = node.data('type');
  if (nodeType === 'workflow' || nodeType === 'activity') {
    _highlightTreeNode(node.id());
  } else {
    _clearTreeHighlight();
  }
  _renderResourceTree(node);

  const embedUrl = node.data('embed_url');
  const detailUrl = node.data('detail_url');

  // Wire header buttons.
  if (openTabBtn) openTabBtn.onclick = () => detailUrl && window.open(detailUrl, '_blank');
  if (openFullBtn) openFullBtn.onclick = () => detailUrl && (window.location.href = detailUrl);

  // Show panel.
  panel.classList.remove('d-none');

  // Load embed content via fetch.
  if (embedUrl) {
    panelContent.innerHTML = '<p class="text-muted p-3 small">Loading…</p>';
    fetch(embedUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.text())
      .then(html => {
        _checkSessionExpiry(html);
        // Only update panel if it's still open (user may have closed it).
        if (_currentPanelNode === node) panelContent.innerHTML = html;
      })
      .catch(() => { panelContent.innerHTML = '<p class="text-danger p-3">Failed to load.</p>'; });
  }
}

/**
 * Close the detail panel and clear selection ring.
 */
function _closeDetailPanel() {
  const panel = document.querySelector('[data-testid="browser-detail-panel"]');
  const panelContent = document.querySelector('[data-testid="browser-panel-content"]');
  if (panel) panel.classList.add('d-none');
  if (panelContent) panelContent.innerHTML = '';
  if (window.cy) {
    window.cy.nodes().style({ 'border-width': 0 });
    // Re-apply filter/search visual state (restores correct opacity + visibility).
    _refreshVisualState();
  }
  _currentPanelNode = null;
  _clearTreeHighlight();
  _clearResourceTree();
}

/**
 * Detect session expiry in HTMX-swapped HTML.
 * If the login page is swapped in, redirect the tab.
 *
 * @param {string} html
 */
function _checkSessionExpiry(html) {
  if (html.includes('id="login-form"') || html.includes('/auth/login/')) {
    const pk = _getPlaybookPk();
    window.location.href = '/auth/login/?next=' + encodeURIComponent('/browser/' + (pk || '') + '/');
  }
}

// ─── Picker state ────────────────────────────────────────────────────────────
let _allPlaybooks = [];   // cached from last GET /api/playbooks/
let _pickerOpen  = false;

/**
 * Open the playbook picker: fetch list, render, show.
 * Auto-expands left panel if it was collapsed.
 */
async function _openPicker() {
  const panel = document.getElementById('browser-left-panel');
  if (panel && panel.classList.contains('browser-collapsed')) {
    _toggleLeftPanel();
  }
  const picker = document.getElementById('browser-picker');
  if (!picker) return;

  if (!_pickerOpen) {
    picker.classList.remove('d-none');
    _pickerOpen = true;
    const search = picker.querySelector('[data-testid="browser-picker-search"]');
    if (search) { search.value = ''; search.focus(); }
  }

  try {
    const resp = await fetch('/api/playbooks/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!resp.ok) return;
    const data = await resp.json();
    _allPlaybooks = data.results || data;
    _renderPickerItems(_allPlaybooks);
  } catch (_) { /* network error — leave list empty */ }
}

/**
 * Render picker rows from a playbooks array.
 * @param {Array} playbooks
 */
function _renderPickerItems(playbooks) {
  const list = document.getElementById('browser-picker-list');
  if (!list) return;
  const currentPk = _getPlaybookPk();
  list.innerHTML = '';
  if (!playbooks.length) {
    list.innerHTML = '<div class="list-group-item text-muted small">No playbooks found.</div>';
    return;
  }
  playbooks.forEach(pb => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('data-testid', 'browser-picker-item');
    btn.setAttribute('data-pk', String(pb.id));
    btn.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center small py-2';
    if (String(pb.id) === String(currentPk)) {
      btn.classList.add('active');
    }
    const nameSpan = document.createElement('span');
    nameSpan.textContent = pb.name;
    const right = document.createElement('span');
    right.className = 'd-flex align-items-center gap-1';
    const badge = document.createElement('span');
    badge.className = 'badge bg-secondary';
    badge.textContent = pb.status;
    right.appendChild(badge);
    if (String(pb.id) === String(currentPk)) {
      const check = document.createElement('i');
      check.className = 'fa-solid fa-check text-white ms-1';
      right.appendChild(check);
    }
    btn.appendChild(nameSpan);
    btn.appendChild(right);
    btn.addEventListener('click', () => _selectPlaybook(pb.id));
    list.appendChild(btn);
  });
}

/**
 * Filter picker items by substring on keyup.
 * @param {string} term
 */
function _filterPickerItems(term) {
  const lower = term.toLowerCase();
  const filtered = lower
    ? _allPlaybooks.filter(pb => pb.name.toLowerCase().includes(lower))
    : _allPlaybooks;
  _renderPickerItems(filtered);
}

/**
 * Close the picker.
 */
function _closePicker() {
  const picker = document.getElementById('browser-picker');
  if (picker) picker.classList.add('d-none');
  _pickerOpen = false;
}

/**
 * Select a playbook: close picker, update URL, update header, fetch graph.
 * @param {number|string} pk
 */
function _selectPlaybook(pk) {
  // FOB-23b: full page navigation so initialisation is identical to opening /browser/<pk>/ directly.
  window.location.href = '/browser/' + pk + '/';
}

/**
 * Update playbook name and status badge in left panel header.
 * Called after graph data arrives.
 * @param {string|number} pk
 * @param {string} name
 * @param {string} status
 */
function _updatePlaybookHeader(pk, name, status) {
  const nameEl = document.querySelector('[data-testid="browser-playbook-title"]');
  if (nameEl) nameEl.textContent = name;
  const statusEl = document.querySelector('[data-testid="browser-playbook-status"]');
  if (statusEl) { statusEl.textContent = status; statusEl.className = 'badge bg-secondary small'; }

  // Ensure Change Playbook button is visible; swap Select → Change if needed.
  const select = document.querySelector('[data-testid="browser-select-playbook"]');
  if (select) { select.setAttribute('data-testid', 'browser-change-playbook'); select.textContent = 'Change Playbook'; select.className = 'btn btn-sm btn-outline-secondary mb-2'; }
}

/**
 * Toggle left panel collapsed / expanded.
 * The toggle button lives outside the panel (sibling in browser-root) so it is
 * never clipped. Its `left` CSS position tracks the panel width.
 */
function _toggleLeftPanel() {
  const panel = document.getElementById('browser-left-panel');
  const toggle = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (!panel) return;
  const collapsed = panel.classList.toggle('browser-collapsed');
  const expandedWidth = '280px';
  panel.style.width = collapsed ? '0' : expandedWidth;
  panel.style.minWidth = collapsed ? '0' : expandedWidth;
  const content = document.getElementById('browser-left-panel-content');
  if (content) content.style.display = collapsed ? 'none' : '';
  if (toggle) {
    toggle.textContent = collapsed ? '›' : '‹';
    toggle.style.left = collapsed ? '0' : expandedWidth;
  }
  if (window.cy) window.cy.resize();
}

/**
 * Main entry point — called on DOMContentLoaded.
 * Reads PK, normalises URL params, fetches graph if PK present.
 */
function _init() {
  const pk = _getPlaybookPk();
  const phases = _getPlaybookPhases();
  const filters = _parseUrlParams();
  _normaliseFilters(filters, phases);

  // Wire panel close button.
  const panelClose = document.querySelector('[data-testid="browser-panel-close"]');
  if (panelClose) panelClose.addEventListener('click', _closeDetailPanel);

  // Wire collapse toggle.
  const toggleBtn = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (toggleBtn) toggleBtn.addEventListener('click', _toggleLeftPanel);

  // Wire picker open — both Change Playbook and Select Playbook buttons.
  document.querySelectorAll('[data-testid="browser-change-playbook"], [data-testid="browser-select-playbook"]').forEach(btn => {
    btn.addEventListener('click', _openPicker);
  });

  // Wire picker search input.
  const pickerSearch = document.querySelector('[data-testid="browser-picker-search"]');
  if (pickerSearch) pickerSearch.addEventListener('input', e => _filterPickerItems(e.target.value));

  // Wire node search input (debounced canvas node name filter).
  const nodeSearch = document.querySelector('[data-testid="browser-search-input"]');
  if (nodeSearch) nodeSearch.addEventListener('input', e => _applySearch(e.target.value));

  if (!pk) {
    _showEmptyState();
    return;
  }

  // Wire zoom controls.
  const zoomIn = document.querySelector('[data-testid="browser-zoom-in"]');
  const zoomOut = document.querySelector('[data-testid="browser-zoom-out"]');
  const zoomFit = document.querySelector('[data-testid="browser-zoom-fit"]');
  if (zoomIn) zoomIn.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() * 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomOut) zoomOut.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() / 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomFit) zoomFit.addEventListener('click', () => window.cy && window.cy.fit());

  // Wire layout switcher.
  const layoutBtn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (layoutBtn) layoutBtn.addEventListener('click', _cycleLayout);
  _updateLayoutBtn();

  // Wire re-plot button.
  const replotBtn = document.querySelector('[data-testid="browser-replot-btn"]');
  if (replotBtn) replotBtn.addEventListener('click', _replot);

  _fetchGraph(pk);
}

// Expose instance globally for Playwright E2E tests.
window.cy = null;

document.addEventListener('DOMContentLoaded', _init);
window.addEventListener('popstate', _onPopState);
