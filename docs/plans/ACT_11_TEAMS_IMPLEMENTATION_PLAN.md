# ACT-11 Teams — Implementation Plan
**BPE-01 output · Feature: FOB-TEAMS-* (all four feature files)**

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `methodology/models/playbook.py` | 1–80 | Follow this exact model pattern: `ForeignKey(User)`, `choices` lists, `CharField`/`TextField`, `__str__`, `Meta.ordering` |
| `methodology/services/pip_notification_service.py` | 1–75 | Pattern for transactional email: `send_mail` + `render_to_string`, env-driven `EMAIL_BACKEND`, no direct boto3 |
| `methodology/services/pip_service.py` | 1–65 | Service pattern: plain functions or thin class, shared by views **and** MCP, all ORM direct, no mocking |
| `methodology/models/__init__.py` | 1–35 | Register every new model here and add to `__all__` |
| `mimir/urls.py` | 57–100 | Add `from methodology import team_views` and `path("teams/", …)` entries following the pip_views pattern |

---

## Do Not Do

- **Do NOT create a new Django app** — all Team models go in `methodology/`
- **Do NOT add a repository/manager layer** — services call the ORM directly (no `TeamRepository`)
- **Do NOT add MCP-specific logic to services** — services are shared; MCP wrappers serialize and check permissions on top
- **Do NOT use direct boto3 for email** — use `send_mail` / `EMAIL_BACKEND`; tests capture mail via `django.core.mail.outbox`
- **Do NOT add async views** — Django sync views throughout, consistent with all existing views
- **Do NOT put team views in `methodology/views.py`** — create `methodology/team_views.py` (follows the `pip_views.py` / `agent_views.py` pattern)
- **Do NOT add a separate `teams` app** — `methodology` is the single app for all domain models

---

## SAO.md Sections That Apply

- **§Services Layer** (`SAO §1708`): services are shared by MCP and Web UI; no MCP-specific logic in services
- **§Repository Pattern** (`SAO §156`): services call ORM directly; no extra repo layer
- **§Web UI Architecture / Django Implementation Details** (`SAO §780`): login_required on all views, HTMX for dynamic interactions, Bootstrap 5.3+, `data-testid` on every interactive element
- **§CRUDLF Pattern** (`SAO §1365`): List, Create, Read, Update, Delete, Find — follow for team CRUD views
- **§Email Architecture** (`SAO §2307`): `EMAIL_BACKEND` strategy; dev=console, test=locmem, prod=SES
- **§BDD Feature Files & UI Specifications** (`SAO §1338`): feature files are authoritative; mockups are reference only

---

## Work Packages

The 70 scenarios across four feature files are grouped into **8 sequential work packages** (WP). Each WP maps to one GitHub issue and one branch.

---

### WP-1 · Core Models + Admin Registration
**Branch**: `feature/teams-models`
**Scenarios addressed**: foundational for all other WPs

#### Models to create

**`methodology/models/team.py`**
```
Team
  name: CharField(max_length=100, unique=True)
  description: TextField(blank=True)
  visibility: CharField(choices=[Public, Hidden])
  join_policy: CharField(choices=[Auto-approve, Requires Approval, Invite Only])
  category: CharField(choices=[Engineering, Design, Research, Product, Private, Other])
  admin: ForeignKey(User, related_name="administered_teams")
  created_at: DateTimeField(auto_now_add=True)
  updated_at: DateTimeField(auto_now=True)
  __str__: return self.name
```

**`methodology/models/team_membership.py`**
```
TeamMembership
  team: ForeignKey(Team, related_name="memberships")
  user: ForeignKey(User, related_name="team_memberships")
  role: CharField(choices=[admin, member])
  joined_at: DateTimeField(auto_now_add=True)
  Meta: unique_together = (team, user)
```

**`methodology/models/join_request.py`**
```
JoinRequest
  team: ForeignKey(Team, related_name="join_requests")
  user: ForeignKey(User, related_name="join_requests")
  source: CharField(choices=[self, invited, invited_new])
  requested_at: DateTimeField(auto_now_add=True)
  status: CharField(choices=[pending, approved, rejected])
  Meta: unique_together = (team, user, status=pending) — enforced in service
```

**`methodology/models/team_playbook.py`**
```
TeamPlaybook  (M2M through-table)
  team: ForeignKey(Team)
  playbook: ForeignKey(Playbook)
  added_at: DateTimeField(auto_now_add=True)
  added_by: ForeignKey(User)
  Meta: unique_together = (team, playbook)
```

#### Steps
1. Create `methodology/models/team.py` + migration
2. Create `methodology/models/team_membership.py` + migration
3. Create `methodology/models/join_request.py` + migration
4. Create `methodology/models/team_playbook.py` + migration
5. Register all four in `methodology/models/__init__.py` + `__all__`
6. Register in `methodology/admin.py` with list_display, search_fields, list_filter
7. Run `pytest tests/unit/test_team_model.py` — unit tests: field defaults, __str__, unique constraints, choices validation

**Checkpoint**: `pytest tests/unit/test_team_model.py -x`

---

### WP-2 · TeamService (business logic)
**Branch**: `feature/teams-service`
**Scenarios**: CREATE-03/04/05/06/07/08, MANAGE-15/16/17/18, VIEW-13/14/15

#### `methodology/services/team_service.py`

```python
class TeamService:
    def create_team(user, name, description, visibility, join_policy, category) -> Team
    def update_team(team, actor, **fields) -> Team           # admin-only
    def delete_team(team, actor) -> None                     # admin-only
    def get_teams_visible_to(user) -> QuerySet               # public + member's hidden
    def get_team_or_404(pk, user) -> Team                    # 404 for hidden non-members
    def add_member(team, user, role="member") -> TeamMembership
    def remove_member(team, actor, target_user) -> None      # admin-only, not self
    def transfer_admin(team, actor, new_admin) -> None
    def leave_team(team, user) -> None                       # blocks if last admin
    def get_member_role(team, user) -> str | None
```

#### Steps
1. Write unit tests (red) — all methods above, happy path + guard conditions
2. Implement `create_team` → test passes
3. Implement `update_team` / `delete_team` → tests pass
4. Implement `get_teams_visible_to` → tests pass
5. Implement membership methods → tests pass
6. Commit: `feat(teams): add TeamService with create/update/delete/membership ops`

**Checkpoint**: `pytest tests/unit/test_team_service.py -x`

---

### WP-3 · Browse + Create Views
**Branch**: `feature/teams-browse-create`
**Scenarios**: BROWSE-01…14, CREATE-01…09

#### Files to create
- `methodology/team_views.py` — `teams_browse`, `teams_create` views
- `templates/teams/browse.html`
- `templates/teams/create.html`
- `mimir/urls.py` — add `path("teams/", include("methodology.team_urls"))` + new `methodology/team_urls.py`

#### View sketches
```python
@login_required
def teams_browse(request):
    """FOB-TEAMS-BROWSE-*: list public + user's hidden teams, search, filter."""

@login_required
def teams_create(request):
    """FOB-TEAMS-CREATE-*: create team form + POST handler."""
```

#### Template requirements (per feature + IA guidelines)
- `data-testid="teams-browse-page"` on root container
- `data-testid="teams-search-input"` — live search (HTMX `hx-get` + partial)
- `data-testid="teams-category-filter"` — category select
- `data-testid="team-card-{slug}"` on each card
- `data-testid="create-team-btn"` + `data-testid="browse-teams-btn"` on dashboard
- `data-testid="team-create-form"`, `data-testid="team-create-submit"` on form
- Empty state: `data-testid="teams-empty-state"` with Clear Search + Create New Team
- Inline validation errors per field

#### Steps
1. Create `methodology/team_urls.py`
2. Wire into `mimir/urls.py` + add `[Browse Teams]` / `[Create Team]` buttons to dashboard template
3. Write integration tests: `tests/integration/test_team_browse_views.py`, `tests/integration/test_team_create_views.py`
4. Implement views + templates
5. Commit: `feat(teams): add teams browse and create views`

**Checkpoint**: `pytest tests/integration/test_team_browse_views.py tests/integration/test_team_create_views.py -x`

---

### WP-4 · Team Detail + Join / Leave
**Branch**: `feature/teams-detail-join-leave`
**Scenarios**: VIEW-01…17

#### Files
- `methodology/team_views.py` — `teams_detail` view
- `templates/teams/detail.html` — info card, tabs (Playbooks, Members), action buttons

#### Context variants (driven by `join_state`)
| State | Condition | Action shown |
|---|---|---|
| `join` | non-member, not invite-only | `[Join Team]` button |
| `pending` | pending join request | disabled `Request Pending` |
| `leave` | member, not admin | `[Leave Team]` button + confirm modal |
| `manage` | admin | `[Manage Team]` button |
| `invite_only` | non-member, Invite Only policy | invite-only notice, no button |

Leave confirm modal: "Leave team 'X'? You will lose access to playbooks shared by this team."
Admin-cannot-leave guard: service raises `ValidationError`; view renders warning modal.
Hidden team: `get_team_or_404` returns 404 for non-members.

#### Steps
1. Write integration tests covering all 17 scenarios (join states, tab content, 404 for hidden)
2. Implement `teams_detail` view
3. Implement `templates/teams/detail.html` with all required `data-testid`s
4. Commit: `feat(teams): add team detail view with join/leave/manage actions`

**Checkpoint**: `pytest tests/integration/test_team_detail_views.py -x`

---

### WP-5 · Team Manage Panel (Members + Join Requests + Playbooks + Settings)
**Branch**: `feature/teams-manage`
**Scenarios**: MANAGE-01…20

#### Files
- `methodology/team_views.py` — `teams_manage` view
- `templates/teams/manage.html` — 4 tabs: Members, Join Requests, Playbooks, Settings

#### Tab details
| Tab | Key actions | `data-testid` |
|---|---|---|
| Members | Remove member (confirm modal), Transfer admin (confirm modal) | `team-tab-members`, `remove-member-{username}`, `transfer-admin-{username}` |
| Join Requests | Approve, Reject; empty state | `team-tab-join-requests`, `approve-request-{username}`, `reject-request-{username}` |
| Playbooks | Add (modal picker — released only), Remove (confirm modal) | `team-tab-playbooks`, `team-add-playbook-btn` |
| Settings | Edit name/desc/visibility/join_policy/category, Save; Danger Zone delete | `team-settings-tab`, `settings-save-btn`, `delete-team-btn` |

Access control: non-admin redirected to `/teams/<pk>/` with warning banner (MANAGE-19). Unauthenticated → login (MANAGE-20).

#### Steps
1. Extend `TeamService`: `get_team_playbooks`, `add_playbook_to_team`, `remove_playbook_from_team`, `approve_join_request`, `reject_join_request`
2. Write integration tests for all MANAGE-01…20 scenarios
3. Implement `teams_manage` view (tab routing via `?tab=` param)
4. Implement `templates/teams/manage.html` with all modals
5. Commit: `feat(teams): add team management panel (members, requests, playbooks, settings)`

**Checkpoint**: `pytest tests/integration/test_team_manage_views.py -x`

---

### WP-6 · Email Notifications
**Branch**: `feature/teams-email`
**Scenarios**: VIEW-18, VIEW-19, MANAGE-03 (approved), MANAGE-04 (rejected), MANAGE-07 (removed), MANAGE-10 (transfer admin)

#### File: `methodology/services/team_notification_service.py`

```python
def send_auto_join_confirmation(membership: TeamMembership) -> None:
    """VIEW-18: Confirmation email to user after auto-join."""
    # Subject: "You've joined the {team.name} team"
    # Template: templates/teams/email_joined.txt + .html
    # Link: /teams/<pk>/

def send_join_request_to_admin(join_request: JoinRequest) -> None:
    """VIEW-19: Email to team admin when join request submitted."""
    # Subject: "New join request for your team \"{team.name}\""
    # Template: templates/teams/email_join_request.txt + .html
    # Link: /teams/<pk>/manage/?tab=join-requests
    # NOTE: no one-click approve/reject — all actions require login

def send_request_approved(join_request: JoinRequest) -> None:
    """MANAGE-03: Email to user when their request is approved."""

def send_request_rejected(join_request: JoinRequest) -> None:
    """MANAGE-04: Email to user when their request is rejected."""

def send_member_removed(membership: TeamMembership) -> None:
    """MANAGE-07: Email to user when removed from team."""

def send_admin_transferred(team: Team, new_admin, old_admin) -> None:
    """MANAGE-10: Email to new admin on transfer."""
```

#### Email templates
```
templates/teams/
  email_joined.txt + .html
  email_join_request.txt + .html
  email_request_approved.txt + .html
  email_request_rejected.txt + .html
  email_member_removed.txt + .html
  email_admin_transferred.txt + .html
```

#### Email backend wiring
- Test: `locmem` backend — assert `len(mail.outbox)`, subject, recipient, body keywords
- Dev: `console` backend (prints to stdout, `USE_SES_IN_DEV=0`)
- Prod: `SESBackend`
- Follow exact pattern of `pip_notification_service.py`

#### Steps
1. Write unit tests (locmem) for all 6 notification functions (red)
2. Create email templates (txt + html pairs)
3. Implement `team_notification_service.py`
4. Call notifications from `TeamService` / views at the right points:
   - `add_member` (auto-approve path) → `send_auto_join_confirmation`
   - `create_join_request` → `send_join_request_to_admin`
   - `approve_join_request` → `send_request_approved`
   - `reject_join_request` → `send_request_rejected`
   - `remove_member` → `send_member_removed`
   - `transfer_admin` → `send_admin_transferred`
5. Commit: `feat(teams): add transactional email notifications for team events`

**Checkpoint**: `pytest tests/integration/test_team_email.py -x`

---

### WP-7 · Invite Flow (with auto-registration)
**Branch**: `feature/teams-invite`
**Scenarios**: MANAGE-21…28

#### File: `methodology/services/team_invite_service.py`

```python
def send_invites(team: Team, inviter, emails: list[str], welcome_text: str) -> dict:
    """
    Process comma-separated email invite list.
    Returns {sent: int, created: int, skipped: list[str], invalid: list[str]}.

    For each email:
      1. Validate format — collect invalid list
      2. If already member — add to skipped list
      3. If User exists → create JoinRequest(source="invited") + send_invite_existing
      4. If no User → _auto_register(email) + create JoinRequest(source="invited_new")
                     + send_invite_new_user (activation + invite email)
    """

def _auto_register(email: str) -> User:
    """
    Derive credentials from email and create inactive account.

    username  = local part before @           (alice.roy from alice.roy@acme.com)
    first_name = local part before first "."  (alice)
    last_name  = domain without TLD           (acme from acme.com)
    password   = unusable (set_unusable_password)
    is_active  = False (activation required)
    """

def _parse_emails(raw: str) -> tuple[list[str], list[str]]:
    """Split comma-separated input; return (valid_list, invalid_list)."""
```

#### Additional notification functions (add to `team_notification_service.py`)
```python
def send_invite_existing_user(join_request: JoinRequest, welcome_text: str) -> None:
    """MANAGE-23: Invite email to an existing user."""
    # Subject: "You've been invited to join the {team} team on Mimir"

def send_invite_new_user(join_request: JoinRequest, activation_token: str, welcome_text: str) -> None:
    """MANAGE-24: Activation + invite email to a newly registered user."""
    # Subject: "You've been invited to Mimir and the {team} team"
    # Link: /auth/activate/{token}/ (reuse accounts activation flow)
```

#### Template additions
```
templates/teams/
  email_invite_existing.txt + .html
  email_invite_new_user.txt + .html
```

#### View extension (Invite tab POST handler in `teams_manage`)
- Parse emails from textarea
- Call `send_invites`
- On validation errors: re-render Invite tab with inline error banner
- On success: re-render with success banner + counts ("3 invites sent. 1 new account created.")
- `data-testid="team-invite-submit"`, `data-testid="invite-emails-input"`, `data-testid="invite-welcome-input"`

#### Join Requests tab extension
- Add `source` column with badge: `Self-request` / `Invited` / `Invited (new)` per `join_request.source`
- `data-testid="join-request-source-{username}"`

#### Steps
1. Write unit tests for `_parse_emails`, `_auto_register`, `send_invites` (red)
2. Implement `_parse_emails` → test passes
3. Implement `_auto_register` → test passes
4. Implement `send_invites` → test passes (locmem, check `mail.outbox`)
5. Implement invite notification functions + templates
6. Wire POST handler into `teams_manage` view
7. Extend Join Requests tab template with source column
8. Commit: `feat(teams): add invite-by-email flow with auto-registration`

**Checkpoint**: `pytest tests/integration/test_team_invite.py -x`

---

### WP-8 · Profile — My Teams Section
**Branch**: `feature/teams-profile`
**Scenarios**: (profile extension; no dedicated `.feature` yet)

#### Changes
- `accounts/views.py` → `profile_view`: extend context with `teams = TeamService.get_user_teams(user)`
- `templates/accounts/profile.html` → add "My Teams" section between My PIPs and My Playbooks
- `data-testid="profile-teams-table"`, `data-testid="profile-team-row-{id}"`
- Shows: name, role badge (crown for admin), visibility badge, member count, playbook count, [View] link
- Hidden teams included (user is member, so has access)

#### `TeamService` addition
```python
def get_user_teams(user) -> QuerySet[Team]:
    """All teams where user is admin or member (via TeamMembership)."""
```

#### Steps
1. Add `get_user_teams` to `TeamService` + unit test
2. Write integration test: `tests/integration/test_profile_page.py` (extend existing)
3. Extend `profile_view` context + template
4. Commit: `feat(profile): show team memberships on user profile page`

**Checkpoint**: `pytest tests/integration/test_profile_page.py -x`

---

## Issue Sequence & Labels

| # | WP | Branch | Label | Dependency |
|---|---|---|---|---|
| 1 | WP-1 Core Models | `feature/teams-models` | `feat`, `easy` | none |
| 2 | WP-2 TeamService | `feature/teams-service` | `feat`, `medium` | WP-1 |
| 3 | WP-3 Browse + Create | `feature/teams-browse-create` | `feat`, `medium` | WP-2 |
| 4 | WP-4 Detail + Join/Leave | `feature/teams-detail-join-leave` | `feat`, `medium` | WP-2 |
| 5 | WP-5 Manage Panel | `feature/teams-manage` | `feat`, `hard` | WP-2 |
| 6 | WP-6 Email Notifications | `feature/teams-email` | `feat`, `medium` | WP-2, WP-4, WP-5 |
| 7 | WP-7 Invite Flow | `feature/teams-invite` | `feat`, `hard` | WP-5, WP-6 |
| 8 | WP-8 Profile Teams | `feature/teams-profile` | `feat`, `easy` | WP-2 |

**WP-3, WP-4, WP-5, WP-8** can run in parallel after WP-2 merges.
**WP-6** can start in parallel with WP-4/WP-5 for service + template layer; hook-in at the end.
**WP-7** depends on WP-5 (manage page) + WP-6 (email infra).

---

## Clarification Questions
*(To be resolved before PIN workflow run)*

**Q1 — Playbook access scope**: When a user joins a team, do they see *all* team playbooks in their main playbook list (`/playbooks/`), or only on the Team Detail page? Does this require changes to `PlaybookService.list_playbooks_for_user`?

**Q2 — Team deletion**: On team deletion, are team-owned playbooks also deleted, or just unlinked? (MANAGE settings Danger Zone scenario)

**Q3 — Activation token for auto-registered users**: Reuse the existing `accounts/services/email_service.py` email-verification token mechanism, or create a separate team-invite token?

**Q4 — Notification visibility**: Are team event notifications also shown as in-app notifications (bell icon)? The user_journey.md mentions a notification bell. Is that in scope for this milestone?

**Q5 — MCP tools for teams**: Should basic team-read MCP tools be included (`list_teams`, `get_team`) in this milestone, or deferred?

---

## Feature Files Covered

| File | Scenarios | Status |
|---|---|---|
| `docs/features/act-11-teams/team-create.feature` | CREATE-01…09 (9) | ✅ complete |
| `docs/features/act-11-teams/team-browse.feature` | BROWSE-01…14 (14) | ✅ complete |
| `docs/features/act-11-teams/team-view.feature` | VIEW-01…19 (19) | ✅ complete (VIEW-18/19 added this session) |
| `docs/features/act-11-teams/team-manage.feature` | MANAGE-01…28 (28) | ✅ complete (MANAGE-21…28 added this session) |
| Profile — My Teams | (inline in user_journey.md) | ⚠️ no dedicated `.feature` file yet |

**Total: 70 BDD scenarios → 8 work packages → 8 GitHub issues**
