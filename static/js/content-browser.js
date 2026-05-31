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
      layout: { name: 'dagre', rankDir: 'TB', nodeSep: 50, rankSep: 70, edgeSep: 10, ranker: 'network-simplex', padding: 30 },
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

  // Wire node tap → detail panel.
  window.cy.on('tap', 'node', function(evt) { _openDetailPanel(evt.target); });
  // Canvas background tap → close panel; edges do nothing.
  window.cy.on('tap', function(evt) {
    if (evt.target === window.cy) { _closeDetailPanel(); }
  });
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

// ─── Detail panel state ───────────────────────────────────────────────────────
let _currentPanelNode = null;   // Cytoscape node currently shown in panel

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

  // Update selection ring: clear previous, apply to current node.
  if (window.cy) {
    window.cy.nodes().style({ 'border-width': 0, 'opacity': 0.4 });
    node.style({ 'border-width': 3, 'border-color': '#dc3545', 'opacity': 1 });
  }
  _currentPanelNode = node;

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
    window.cy.nodes().style({ 'border-width': 0, 'opacity': 1 });
  }
  _currentPanelNode = null;
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
  _closePicker();
  _pushPlaybookUrl(pk, { types: [], phases: [] });
  // Reset phases (playbook-scoped) before fetch
  const root = document.getElementById('browser-root');
  if (root) { root.dataset.playbookPk = String(pk); root.dataset.playbookPhases = '[]'; }
  _fetchGraph(pk);
}

/**
 * Update playbook name and status badge in left panel header.
 * Called after graph data arrives.
 * @param {string|number} pk
 * @param {string} name
 * @param {string} status
 */
function _updatePlaybookHeader(pk, name, status) {
  const nameEl = document.querySelector('[data-testid="browser-playbook-name"]');
  if (nameEl) nameEl.textContent = name;
  const statusEl = document.querySelector('[data-testid="browser-playbook-status"]');
  if (statusEl) { statusEl.textContent = status; statusEl.className = 'badge bg-secondary small'; }

  // Ensure Change Playbook button is visible; swap Select → Change if needed.
  const select = document.querySelector('[data-testid="browser-select-playbook"]');
  if (select) { select.setAttribute('data-testid', 'browser-change-playbook'); select.textContent = 'Change Playbook'; select.className = 'btn btn-sm btn-outline-secondary mb-2'; }
}

/**
 * Toggle left panel collapsed / expanded.
 */
function _toggleLeftPanel() {
  const panel = document.getElementById('browser-left-panel');
  const toggle = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (!panel) return;
  const collapsed = panel.classList.toggle('browser-collapsed');
  panel.style.width = collapsed ? '0' : '280px';
  panel.style.minWidth = collapsed ? '0' : '280px';
  const content = document.getElementById('browser-left-panel-content');
  if (content) content.style.display = collapsed ? 'none' : '';
  if (toggle) toggle.textContent = collapsed ? '›' : '‹';
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
