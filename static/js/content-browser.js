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
        .filter(n => Number.isFinite(n) && n > 0)
    : [];

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
  const cleanPhases = filters.phases.filter(id => validPhaseIds.has(id));
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
  const allActive = _ALL_TYPES.every(t => filters.types.includes(t));
  if (!allActive && filters.types.length > 0) {
    parts.push('types=' + filters.types.join(','));
  }
  if (filters.phases.length > 0) {
    parts.push('phases=' + filters.phases.join(','));
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
    const filters = _parseUrlParams();
    _renderGraph(pk, data, filters);
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

  // Degraded mode banner for large graphs.
  const degradedBanner = document.querySelector('[data-testid="browser-degraded-banner"]');
  if (nodes.length > 300) {
    if (degradedBanner) {
      degradedBanner.textContent = `Graph is large (${nodes.length} nodes). Performance may be reduced.`;
      degradedBanner.classList.remove('d-none');
    }
  } else {
    if (degradedBanner) degradedBanner.classList.add('d-none');
  }

  // Node count badge.
  const countBadge = document.querySelector('[data-testid="browser-node-count"]');
  if (countBadge) countBadge.textContent = `${nodes.length} nodes`;

  const elements = [
    ...nodes.map(n => ({ data: n })),
    ...edges.map(e => ({ data: e })),
  ];

  try {
    window.cy = cytoscape({
      container,
      elements,
      style: _cytoscapeStyle(),
      layout: { name: 'dagre', rankDir: 'TB', nodeSep: 30, rankSep: 50, padding: 20 },
      minZoom: 0.1,
      maxZoom: 3,
    });
  } catch (layoutErr) {
    // dagre layout unavailable — fall back to built-in breadthfirst layout.
    window.cy = cytoscape({
      container,
      elements,
      style: _cytoscapeStyle(),
      layout: { name: 'breadthfirst', directed: true, padding: 20, spacingFactor: 1.5 },
      minZoom: 0.1,
      maxZoom: 3,
    });
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

  _applyFilters(filters);
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
      style: { ..._nodeBase, 'background-color': '#0d6efd', 'shape': 'round-rectangle', 'width': 130, 'height': 44, 'font-size': 12 } },
    { selector: 'node[type = "activity"]',
      style: { ..._nodeBase, 'background-color': '#198754', 'shape': 'round-rectangle' } },
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
    // Edges
    { selector: 'edge[relationship = "contains"]',
      style: { 'line-color': '#0d6efd', 'target-arrow-color': '#0d6efd', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'width': 2 } },
    { selector: 'edge[relationship = "predecessor"]',
      style: { 'line-color': '#198754', 'target-arrow-color': '#198754', 'target-arrow-shape': 'triangle', 'line-style': 'dashed', 'curve-style': 'bezier', 'width': 1, 'opacity': 0.7 } },
    { selector: 'edge[relationship = "produces"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle', 'line-style': 'dashed', 'curve-style': 'bezier', 'width': 1.5 } },
    { selector: 'edge[relationship = "consumes"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle', 'line-style': 'dashed', 'curve-style': 'bezier', 'width': 1.5, 'opacity': 0.8 } },
    { selector: 'edge[relationship = "uses_skill"]',
      style: { 'line-color': '#fd7e14', 'target-arrow-color': '#fd7e14', 'target-arrow-shape': 'triangle', 'line-style': 'dotted', 'curve-style': 'bezier', 'width': 1.5 } },
    { selector: 'edge[relationship = "assigned_agent"]',
      style: { 'line-color': '#0dcaf0', 'target-arrow-color': '#0dcaf0', 'target-arrow-shape': 'triangle', 'line-style': 'dotted', 'curve-style': 'bezier', 'width': 1.5 } },
    { selector: 'edge[relationship = "governed_by_rule"]',
      style: { 'line-color': '#6c757d', 'target-arrow-color': '#6c757d', 'target-arrow-shape': 'triangle', 'line-style': 'dotted', 'curve-style': 'bezier', 'width': 1.5 } },
  ];
}

/**
 * Dim nodes whose type is not in the active filter set.
 * Only affects opacity — all nodes remain in the DOM.
 *
 * @param {{ types: string[], phases: number[] }} filters
 */
function _applyFilters(filters) {
  if (!window.cy) return;
  const activeTypes = new Set(filters.types);
  window.cy.nodes().forEach(node => {
    node.style('opacity', activeTypes.has(node.data('type')) ? 1 : 0.15);
  });
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

/**
 * Main entry point — called on DOMContentLoaded.
 * Reads PK, normalises URL params, fetches graph if PK present.
 */
function _init() {
  const pk = _getPlaybookPk();
  const phases = _getPlaybookPhases();
  const filters = _parseUrlParams();
  _normaliseFilters(filters, phases);

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

  _fetchGraph(pk);
}

// Expose instance globally for Playwright E2E tests.
window.cy = null;

document.addEventListener('DOMContentLoaded', _init);
window.addEventListener('popstate', _onPopState);
