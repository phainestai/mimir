"""Shared Playwright fixtures for Content Browser e2e tests (Act-16 Phase B6)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from e2e_helpers import enable_custom_layout, login, open_content_browser
from methodology.models import Activity, Agent, Playbook, Rule, Skill, Workflow

User = get_user_model()


@pytest.fixture
def cb_user(transactional_db):
    """Authenticated user for content-browser e2e scenarios."""
    user = User.objects.create_user(
        username="cb_e2e_user",
        email="cb_e2e@test.com",
        password="testpass123",
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def cb_playbook(cb_user, transactional_db):
    """Released playbook with graph content, predecessor edge, and resources."""
    pb = Playbook.objects.create(
        name="CB E2E Playbook",
        description="Deterministic content-browser e2e fixture",
        category="development",
        status="released",
        version="1.0",
        source="owned",
        author=cb_user,
        visibility="public",
    )
    wf = Workflow.objects.create(
        name="CB Workflow", description="WF", playbook=pb, order=1
    )
    wf2 = Workflow.objects.create(
        name="CB Workflow 2", description="WF2", playbook=pb, order=2
    )
    skill = Skill.objects.create(playbook=pb, title="CB Skill")
    agent = Agent.objects.create(playbook=pb, name="CB Agent")
    rule = Rule.objects.create(playbook=pb, title="CB Rule")
    act1 = Activity.objects.create(name="CB Plan", workflow=wf, order=1)
    act2 = Activity.objects.create(
        name="CB Implement",
        workflow=wf,
        order=2,
        predecessor=act1,
        agent=agent,
    )
    act2.skills.add(skill)
    act2.rules.add(rule)
    Activity.objects.create(name="CB Solo", workflow=wf2, order=1)
    return {
        "user": cb_user,
        "username": "cb_e2e_user",
        "password": "testpass123",
        "pb": pb,
        "wf": wf,
        "wf2": wf2,
        "act1": act1,
        "act2": act2,
    }


@pytest.fixture
def cb_graph_page(page: Page, live_server, cb_playbook) -> Page:
    """Logged-in browser page on cb_playbook with Cytoscape ready."""
    data = cb_playbook
    login(page, live_server.url, data["username"], data["password"])
    open_content_browser(page, live_server.url, data["pb"].pk)
    return page


@pytest.fixture
def cb_custom_graph_page(cb_graph_page: Page) -> Page:
    """cb_graph_page with FOB-63 custom layout mode enabled."""
    enable_custom_layout(cb_graph_page)
    return cb_graph_page
