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
 * Reads the new URL state and updates display accordingly.
 *
 * @param {PopStateEvent} event
 */
function _onPopState(event) {
  const pk = _getPkFromPath();
  const filters = _parseUrlParams();
  if (!pk) {
    _showEmptyState();
  }
  // Graph re-fetch on popstate is implemented in the graph rendering iteration.
  // For now, the URL is already correct — the page will reload on hard navigation.
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

/**
 * Main entry point — called on DOMContentLoaded.
 * Reads PK, normalises URL params, fetches graph if PK present.
 */
function _init() {
  const pk = _getPlaybookPk();
  const phases = _getPlaybookPhases();
  const filters = _parseUrlParams();
  // Normalise and rewrite URL (drop invalid types, drop stale phase IDs)
  _normaliseFilters(filters, phases);
  if (!pk) {
    _showEmptyState();
  }
  // Graph fetch and Cytoscape init are implemented in the graph rendering iteration.
}

// Expose instance globally for Playwright E2E tests.
// window.cy is set to the Cytoscape instance once graph is initialised
// (implemented in the graph rendering iteration). Set null here so
// tests can assert absence without ReferenceError.
window.cy = null;

document.addEventListener('DOMContentLoaded', _init);
window.addEventListener('popstate', _onPopState);
