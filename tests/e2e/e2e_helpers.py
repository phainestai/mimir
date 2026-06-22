"""Shared E2E helpers for auth and Content Browser flows."""

from __future__ import annotations

import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)

LOGIN_URL_PATH = '/auth/user/login/'


def login(page: Page, live_server_url: str, username: str, password: str) -> None:
    """Log in via the standard auth form; wait until login page is left."""
    logger.info('E2E login: user=%s url=%s', username, live_server_url)
    page.goto(f'{live_server_url}{LOGIN_URL_PATH}')
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_function(
        "() => !window.location.pathname.includes('/auth/user/login')",
        timeout=10_000,
    )
    assert LOGIN_URL_PATH not in page.url, (
        f'Login failed; still on login page. URL: {page.url}'
    )


def wait_for_cy_graph(page: Page, timeout: int = 10_000, min_nodes: int = 1) -> None:
    """Wait until Cytoscape is ready with at least min_nodes on the canvas."""
    page.wait_for_function(
        f'() => window.cy !== null && window.cy.nodes().length >= {min_nodes}',
        timeout=timeout,
    )


def wait_for_cy_edges(page: Page, timeout: int = 10_000, min_edges: int = 1) -> None:
    """Wait until Cytoscape has rendered at least min_edges."""
    page.wait_for_function(
        f'() => window.cy !== null && window.cy.edges().length >= {min_edges}',
        timeout=timeout,
    )


def open_content_browser(
    page: Page,
    live_server_url: str,
    playbook_id: int,
    *,
    wait_graph: bool = True,
    min_nodes: int = 1,
) -> None:
    """Navigate to /browser/<pk>/ and optionally wait for the graph."""
    url = f'{live_server_url}/browser/{playbook_id}/'
    logger.info('E2E open_content_browser: pk=%s url=%s', playbook_id, url)
    page.goto(url)
    if wait_graph:
        wait_for_cy_graph(page, min_nodes=min_nodes)
