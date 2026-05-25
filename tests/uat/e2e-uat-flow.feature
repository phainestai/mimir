@manual @uat @e2e-uat-flow
Feature: Mimir E2E UAT — browser-only flow (registration → GUI CRUDL → release → PIP GUI → admin finalize)

  BROWSER STEPS ONLY — no CallMcpTool calls in this file.
  All MCP tool scenarios live in tests/uat/mcp-uat-flow.feature (run in agent mode).

  Execution order:
    1. J1 here  (register + token RECORD)
    2. mcp-uat-flow.feature MCP-00  (wire Docker token → smoke)
    3. J3 here  (GUI CRUDL)
    4. mcp-uat-flow.feature MCP-01/02/03  (MCP read/write against GUI playbook)
    5. J5 here  (release via GUI)
    6. mcp-uat-flow.feature MCP-06/07  (release + post-release guard)
    7. J6 browser here  (PIP UI)
    8. mcp-uat-flow.feature MCP-08/08b/08c/09  (PIP MCP lifecycle)
    9. J7 here  (admin finalize + GUI verify)
   10. mcp-uat-flow.feature MCP-11  (post-finalize inventory)

  ==============================================================================
  JOURNEY MAP
  ==============================================================================
    | Journey | Scenarios in THIS file                               | MCP counterpart (mcp-uat-flow.feature) |
    | J1      | UAT-01-00 … UAT-01-04, 01-01b, 01-03b               | MCP-00 (token wire)                    |
    | J3      | UAT-03-00 … UAT-03-03 + CRUDL splits                 | MCP-01/02/03                           |
    | J3B     | UAT-03-05, UAT-03-05b (GUI visibility isolation)     | MCP-01b (MCP author-scoping proof)     |
    | J5      | UAT-05-00, UAT-05-01                                 | MCP-06 (release), MCP-07 (guard)       |
    | J6 GUI  | UAT-06-00, UAT-06-01-neg, UAT-06-02, UAT-06-06      | MCP-08/08b/08c/09                      |
    | J7      | UAT-07-01, UAT-07-02                                 | MCP-11 (post-finalize inventory)       |

  ==============================================================================
  OPERATOR SCRIPT CONTRACT
  ==============================================================================
    STEP — short title (in `# STEP` comment block)
    DO — one browser navigation or form interaction (BASE_URL prefixed URLs)
    SEE — one observable: exact Django flash string or `[data-testid="…"]`
    RECORD — annotate placeholder filled from SEE for downstream steps
    IF DIFFER — file defect citing Scenario + STEP id (`Expected …; got …`)
    BUG TEMPLATE — reuse IF DIFFER line in tracker title/body
    BASE_URL — http://127.0.0.1:8000
    SELECTOR PRIORITY — data-testid → name/id attribute → readable label substring
    FLASH — Django messages use `[data-testid="alert-message"]` wrapper in ``base.html``
    CURSOR_PROMPT — manual one-time IDE action; agent STOPS and waits for confirmation

  ==============================================================================
  DEVIATIONS (user journey narrative ↔ shipped MVP)
  ==============================================================================
    | Narrative expectation | MVP truth for this replay |
    | Congratulations + MCP token onboarding page after verify | Token only on `/auth/user/profile/` (UAT-01-04). |
    | Guided MCP onboarding screen | Agent runs mcp-uat-flow MCP-00 after UAT-01-04. |
    | Activate playbook tile | Out of scope — skip. |
    | Notifications / Teams / GUI import/export | Skip or assert disabled only. |
    | Family/Homebase playbook sharing GUI | Deferred; FOB MVP uses Private vs Public. |
    | Submit PIP UX lock until changes | Browser may allow click; SEE server `Add at least one Change before submitting.` |

  ==============================================================================
  PLACEHOLDER REGISTRY
  ==============================================================================
    <UAT_EMAIL> <UAT_USERNAME> <UAT_PASSWORD> — operator / UAT-01-01
    <UAT_TOKEN>           — UAT-01-04 profile RECORD; passed to mcp-uat-flow MCP-00
    <ADMIN_TOKEN>         — admin DRF token (UAT-03-05b GUI toggle + mcp-uat-flow MCP-01b token swap)
    <ADMIN_PUBLIC_PB_ID>  — public playbook created by admin in UAT-03-05 (used in MCP-01b)
    <ADMIN_PRIVATE_PB_ID> — private playbook created by admin in UAT-03-05
    <GUI_PLAYBOOK_ID> <GUI_WORKFLOW_ID> — wizard UAT-03-01
    <GUI_PHASE_PK> <ACT_ALPHA_PK> <ACT_BETA_PK> <GUI_AGENT_PK>
    <GUI_SKILL_PK> <GUI_SKILL_PK_2> <GUI_ARTIFACT_PK> <GUI_RULE_PK> — GUI CRUDL splits
    <PIP_NEG_PK>          — throwaway PIP for UAT-06-01-neg editor validations
    <PIP_GUI_PK>          — browser PIP RECORD (UAT-06-02)
    <PIP_MCP_PK>          — MCP PIP RECORD from mcp-uat-flow MCP-08 (used in UAT-06-06/07-01/07-02)

  SHARED ACTORS: uat_user (browser); admin (Django admin J7). MCP actor in mcp-uat-flow.feature.

  PRECONDITIONS: runserver reachable; SES if verifying Gmail; createsuperuser `admin`; GALDR_EAGER=True recommended.

  OUT OF SCOPE (this file): all CallMcpTool invocations, token swap, MCP sandbox, export/import,
  PIP MCP lifecycle, MCP isolation tests — all in mcp-uat-flow.feature.
#############################################################################
# Journey 1 — Registration + verify + profile token
############################################################################

  @manual @uat @act-0
  Scenario: UAT-01-00 Login failure banner (wrong credentials)
    # STEP 1 — Reach login surface
    # DO: browser GET BASE_URL`/auth/user/login/` (anonymous session)
    # SEE: `[data-testid=\"login-form\"]`
    # IF DIFFER: UAT-01-00 STEP1
    # STEP 2 — Bad credential POST
    # DO: `[data-testid=\"login-username-input\"]` typed value (non-empty); `[data-testid=\"login-password-input\"]` known-wrong literal `xbadpasswordx`; click `[data-testid=\"login-submit-button\"]`
    # SEE: `[data-testid=\"login-error-message\"]` renders `Login failed:` AND `Invalid username or password. Please try again.` together
    # IF DIFFER: UAT-01-00 STEP2

  @manual @uat @act-1
  Scenario: UAT-01-01 Register accepting ToS flash
    # STEP 1 — Open register
    # DO: GET `/auth/user/register/`
    # SEE: `[data-testid=\"register-form\"]`
    # STEP 2 — Mandatory fields BEFORE ToS
    # DO: fill `[data-testid=\"register-first-name\"]` `UAT`; `[data-testid=\"register-last-name\"]` `Journey`; `[data-testid=\"register-username-input\"]` `<UAT_USERNAME>`; `[data-testid=\"register-email-input\"]` `<UAT_EMAIL>`; `[data-testid=\"register-password-input\"]` + `[data-testid=\"register-password-confirm-input\"]` `<UAT_PASSWORD>`
    # SEE: `[data-testid=\"register-submit-button\"]` DISABLED prior ToS (`register-tos-checkbox` unchecked)
    # STEP 3 — ToS acceptance
    # DO: `[data-testid=\"register-tos-checkbox\"]` checked true; click `[data-testid=\"register-submit-button\"]`
    # SEE: URL `/auth/user/login/` immediately after redirect; Django messages first `[data-testid=\"alert-message\"]` text EXACT `Account created. Please check your inbox and verify your email before logging in.`

  @manual @uat @act-1
  Scenario: UAT-01-01b Second registration duplicates username
    # DO: repeat Journey 01-01 body with identical `<UAT_USERNAME>`
    # SEE: `[data-testid=\"register-error-message\"]` includes prefix `Registration failed:` AND body `An error occurred during registration. Please try again.` OR surfaced field duplicate validators

  @manual @uat @act-1
  Scenario: UAT-01-02 Not verified banner on login POST
    # DO: login form POST `[data-testid=\"login-submit-button\"]`
    # SEE: `[data-testid=\"login-unverified-banner\"]` substring `verify your email` AND `[data-testid=\"login-resend-btn\"]`

  @manual @uat @act-1 @email
  Scenario: UAT-01-03 Gmail verification link redirects with success flash
    # DO (Gmail operator): inbox `<UAT_EMAIL>`; open subject containing `Verify`; follow href whose pathname matches `/auth/user/verify-email/*`
    # SEE: GET redirect chain ends `/auth/user/login/`; flash `[data-testid=\"alert-message\"]` EXACT `Your email has been verified. You can sign in now.`

  @manual @uat @act-1 @email
  Scenario: UAT-01-03b Expired / invalid verification token page
    # DO: deliberately open VERIFY url with malformed or expired tail until view `verify_email_result.html` renders expire branch
    # SEE: `[data-testid=\"verify-email-expired-alert\"]` substring `This verification link has expired.` plus `[data-testid=\"verify-email-resend-form\"]`

  @manual @uat @profile
  Scenario: UAT-01-04 Verified login lands dashboard + PROFILE token RECORD + regen FAIL
    # STEP A — Credential success
    # DO: POST `[data-testid=\"login-form\"]` with `<UAT_USERNAME>` + `<UAT_PASSWORD>`
    # SEE: response URL `/dashboard/` AND hidden sentinel `[data-testid=\"dashboard-loaded\"]`
    # STEP B — Profile drill
    # DO: navbar `[data-testid=\"user-display\"]` expands; `[data-testid=\"nav-view-profile\"]`
    # SEE: `/auth/user/profile/` AND `[data-testid=\"profile-page\"]`; `[data-testid=\"profile-email\"]` textual equals `<UAT_EMAIL>`
    # STEP C RECORD <UAT_TOKEN>
    # DO: optional toggles `[data-testid=\"profile-token-toggle\"]`, `[data-testid=\"profile-token-copy\"]`
    # SEE: `[data-testid=\"profile-token-field\"]` holds token string RECORD `<UAT_TOKEN>`
    # STEP D — regenerate wrong-password branch
    # DO: fill `[data-testid=\"profile-token-regenerate-password\"]` literal `incorrect-password-uat`; submit `[data-testid=\"profile-token-regenerate-submit\"]`
    # SEE: flash `[data-testid=\"alert-message\"]` EXACT `Incorrect password. Your API token was not changed.`

  @manual @uat @act-0 @profile
  Scenario: UAT-01-05 Logged-in user cannot access login or register (guest-only guard)
    # Pre: `<UAT_USERNAME>` session still active from UAT-01-04 (do NOT logout)
    # STEP A — Login page guard
    # DO: GET `/auth/user/login/` while authenticated
    # SEE: redirect URL `/auth/user/profile/`; `[data-testid=\"profile-page\"]` visible; NO `[data-testid=\"login-form\"]`
    # IF DIFFER: UAT-01-05 STEP A
    # STEP B — Register page guard
    # DO: GET `/auth/user/register/` while authenticated
    # SEE: redirect URL `/auth/user/profile/`; `[data-testid=\"profile-page\"]` visible; NO `[data-testid=\"register-form\"]`
    # IF DIFFER: UAT-01-05 STEP B
    # STEP C — POST login guard (no re-auth)
    # DO: POST `/auth/user/login/` with any credentials while still authenticated
    # SEE: redirect `/auth/user/profile/`; navbar `[data-testid=\"user-display\"]` still shows `<UAT_USERNAME>`
    # IF DIFFER: UAT-01-05 STEP C
#############################################################################
# Journey 2 — MCP token wiring + smoke negatives → see mcp-uat-flow.feature
#############################################################################
  # MCP-00: wire mcp.json with UAT token (scripts/mcp_token_swap.py)
  # MCP-01: list_playbooks smoke + bad-token HTTP diagnostics
  # Run mcp-uat-flow.feature MCP-00 and MCP-01 before proceeding to Journey 3.
#############################################################################
# Journey 3 — Playbook wizard + split GUI CRUDL + nav smoke + MCP owner denial
############################################################################

  @manual @uat @act-2 @wizard-negative
  Scenario: UAT-03-00 Wizard step1 rejects empty name AND short description
    # STEP name blank (disable HTML5 if needed)
    # DO: POST step1 omitting usable name hitting server validators
    # SEE: `Name is required. Must be 3-100 characters.` (see ``PlaybookBasicInfoForm``)
    # STEP desc too short — name `XYZ`, description literal nine chars only
    # DO: submit wizard step1
    # SEE: validation references `Must be 10-500 characters`.

  @manual @uat @act-2
  Scenario: UAT-03-01 Wizard creates Draft playbook RECORD playbook + workflow pk
    # STEP reach wizard
    # DO: navbar `[data-testid=\"nav-playbooks\"]` then GET `/playbooks/create/`
    # SEE: `[data-testid=\"wizard-step-1\"]`
    # STEP fill fundamentals
    # DO: `[data-testid=\"name-input\"]` `UAT Journey Playbook`; `[data-testid=\"description-input\"]` ≥40 char narrative; `[data-testid=\"category-select\"]` `development`; `[data-testid=\"visibility-select\"]` `private`
    # SEE: `[data-testid=\"visibility-help\"]` explains Private vs Public (authenticated readers for Public); options `private` + `public` only
    # STEP advance workflows
    # DO: click Next control whose label mentions adding workflows (`Next: Add Workflows`)
    # SEE: URL `/playbooks/create/step2/`
    # STEP capture workflow scaffold
    # DO: `[data-testid=\"workflow-name-input\"]` `UAT Workflow`; `[data-testid=\"workflow-description-input\"]` `Primary UAT workflow`; click `[data-testid=\"add-workflow\"]` to reach Publishing
    # SEE: `/playbooks/create/step3/` + `[data-testid=\"summary-card\"]`
    # STEP publish draft tier
    # DO: choose Publication radio `draft`; submit `Create Playbook` bootstrap button (`btn-success` banner)
    # SEE: playbook detail `[data-testid=\"playbook-detail\"]` renders AND `[data-testid=\"status-badge\"]` text `Draft`
    # RECORD numeric `<GUI_PLAYBOOK_ID>` from URL + `<GUI_WORKFLOW_ID>` from workflows table `[data-testid=\"workflows-table\"]`

  @manual @uat @act-2
  Scenario: UAT-03-01b Visibility helper on edit shell
    # DO: GET `/playbooks/<GUI_PLAYBOOK_ID>/edit/`
    # SEE: `[data-testid=\"playbook-visibility-select\"]` selected `Private`; `[data-testid=\"visibility-help\"]` matches Private/Public semantics (no Family/Local rows)

  @manual @uat @act-4
  Scenario: UAT-03-02a Phase create + `/phases/` global RECORD
    # DO: playbook detail `[data-testid=\"tab-phases\"]`, `[data-testid=\"create-phase-btn\"]`, form `[data-testid=\"phase-create-form\"]` name `UAT Phase`, textarea `[data-testid=\"description-input\"]` `Planning`; submit `[data-testid=\"submit-button\"]`
    # SEE: playbook phases tab evidences inserted row/link
    # RECORD `<GUI_PHASE_PK>`
    # DO: navbar `[data-testid=\"nav-phases\"]`
    # SEE: `[data-testid=\"phases-list-global\"]` contains textual `UAT Phase`

  @manual @uat @act-5
  Scenario: UAT-03-02b Activity Alpha RECORD
    # DO: `/playbooks/<GUI_PLAYBOOK_ID>/workflows/<GUI_WORKFLOW_ID>/activities/create/` showing `[data-testid=\"activity-create\"]`
    # DO: `[data-testid=\"name-input\"]` `Activity Alpha`; `[data-testid=\"guidance-input\"]` paste markdown body EXACTLY lines: `## Alpha` blank line `Initial guidance for Activity Alpha.`
    # DO: optionally map `[data-testid=\"phase-select\"]` to `UAT Phase`; click `[data-testid=\"save-btn\"]`
    # RECORD `<ACT_ALPHA_PK>` from redirect/detail URL slug

  @manual @uat @act-5
  Scenario: UAT-03-02c Activity Beta + Alter Alpha guidance + globals
    # DO: repeat `/activities/create/` scaffold with name `Activity Beta` + markdown containing `Beta` guidance snippet; save RECORD `<ACT_BETA_PK>`
    # DO: `/activities/<ACT_ALPHA_PK>/edit/` append additional sentence `GUI-updated guidance.` into `[data-testid=\"guidance-input\"]`, submit `[data-testid=\"save-btn\"]`
    # SEE: updated detail excerpt visible
    # DO: navbar `[data-testid=\"nav-activities\"]` verifying `[data-testid=\"activities-global-list\"]` mentions both canonical activity names

  @manual @uat @act-7
  Scenario: UAT-03-02d Agent create RECORD
    # DO: playbook detail Agents tab `[data-testid=\"tab-agents\"]` `[data-testid=\"create-agent-btn\"]` OR direct `/agents/create/<GUI_PLAYBOOK_ID>/`
    # SEE: `[data-testid=\"agent-create\"]`
    # DO: `[data-testid=\"agent-name-input\"]` `UAT Agent`; `[data-testid=\"agent-description-input\"]` `Test agent persona`; `[data-testid=\"create-agent-btn\"]` submits `Create Agent`
    # RECORD `<GUI_AGENT_PK>`
    # DO: `[data-testid=\"nav-agents\"]` global verifying presence

  @manual @uat @act-8
  Scenario: UAT-03-02e Skill create RECORD (domains / stack literals)
    # DO: `/playbooks/<GUI_PLAYBOOK_ID>/skills/create/` path (`[data-testid=\"skill-create\"]`)
    # DO: `[data-testid=\"title-input\"]` `UAT Skill`; `[data-testid=\"domain-input\"]` `GUI_FORM`; `[data-testid=\"stack-input\"]` `Django+HTMX`; `[data-testid=\"content-input\"]` Markdown `## Skill steps`
    # SEE: `[data-testid=\"save-btn\"]` success path
    # RECORD `<GUI_SKILL_PK>`; navbar `[data-testid=\"nav-skills\"]`
    # DO: create second skill `UAT Skill Two` with domain `DEPLOY` stack `AWS+Beanstalk`
    # RECORD `<GUI_SKILL_PK_2>`

  @manual @uat @act-8
  Scenario: UAT-03-02e2 Activity edit links multiple skills (M2M)
    # DO: `/activities/<ACT_ALPHA_PK>/edit/` on `[data-testid=\"activity-edit\"]`
    # DO: check `[data-testid=\"skill-checkbox-<GUI_SKILL_PK>\"]` and `[data-testid=\"skill-checkbox-<GUI_SKILL_PK_2>\"]`
    # DO: `[data-testid=\"save-btn\"]`
    # SEE: activity detail `[data-testid=\"activity-skills-list\"]` shows both skill titles
    # DO: return to edit; uncheck only `<GUI_SKILL_PK>`; save
    # SEE: detail lists only `UAT Skill Two`

  @manual @uat @artifacts
  Scenario: UAT-03-02f Artifact create + global registry
    # DO: `/playbooks/<GUI_PLAYBOOK_ID>/artifacts/create/` `[data-testid=\"artifact-create\"]` `[data-testid=\"artifact-form\"]`
    # DO: name `UAT Artifact`; `[data-testid=\"type-select\"]` `Document`; `[data-testid=\"producer-select\"]` row referencing `Activity Alpha`; ensure `[data-testid=\"required-checkbox\"]` toggled meaningful; `[data-testid=\"save-btn\"]` submits
    # RECORD `<GUI_ARTIFACT_PK>`
    # DO: `[data-testid=\"nav-artifacts\"]` verifies listing text

  @manual @uat @rules
  Scenario: UAT-03-02g Canonical rule vs disposable deletion modal
    # DO: `/playbooks/<GUI_PLAYBOOK_ID>/rules/create/` `[data-testid=\"rule-create\"]` with `[data-testid=\"rule-title-input\"]` `UAT Rule` plus `[data-testid=\"rule-content-input\"]` `Always apply in UAT`
    # RECORD `<GUI_RULE_PK>`
    # DO: create ephemeral `UAT Rule Disposable`; initiate delete UX until Bootstrap modal `[data-testid=\"rule-delete-modal\"]` and confirm `[data-testid=\"confirm-delete-rule-btn\"]`
    # SEE: disposable vanished while `UAT Rule` survives

  @manual @uat @act-3
  Scenario: UAT-03-02h Workflows matrix + `/workflows/` global parity
    # DO: playbook detail `[data-testid=\"tab-workflows\"]`
    # SEE: `[data-testid=\"workflows-table\"]` row text `UAT Workflow`
    # DO: navbar `[data-testid=\"nav-workflows\"]` verifies global mirrored label

  @manual @uat @negatives-split
  Scenario: UAT-03-02-neg Activity blank name AND Skill blank title POST
    # DO: circumvent HTML `required` and POST activity create omitting `[data-testid=\"name-input\"]` text
    # SEE: server invalid-feedback for name surfaced (or browser stops — document IF DIFFER)
    # DO: POST skill create omitting `[data-testid=\"title-input\"]`
    # SEE: `[data-testid=\"title-error\"]` after round-trip rendering

  @manual @uat @dashboard
  Scenario: UAT-03-03 Dashboard, global search hints, `/pips/` header, playbook card stats
    # DO: `[data-testid=\"nav-dashboard\"]`
    # SEE: `/dashboard/` with `[data-testid=\"dashboard-loaded\"]`
    # DO: `[data-testid=\"global-search-input\"]` substring `UAT Journey`; `[data-testid=\"global-search-form\"]` submits (GET `/search/` path or HTMX partial `[data-testid=\"global-search-suggestions\"]`)
    # SEE: target playbook surfaced in textual results grouping
    # DO: navbar `[data-testid=\"nav-pips\"]` → `/pips/`
    # SEE: `[data-testid=\"pip-list-page\"]`; optional badge `[data-testid=\"pip-list-count\"]` textual `PIPs (`
    # DO: playbook list locate `[data-testid=\"playbook-book-card-<GUI_PLAYBOOK_ID>\"]`
    # SEE: quick stats still ≥2 Activities (post-PIP bumps come after mcp-uat-flow MCP-08)

#############################################################################
# Journey 3B — Visibility isolation: public vs private playbooks in GUI
#############################################################################

  @manual @uat @act-2 @visibility
  Scenario: UAT-03-05 Other-user public vs private playbook appears/blocked in GUI list + detail
    # Pre: admin is a separate Django user (createsuperuser). UAT user is logged in as uat_user.
    # STEP admin-create-public
    # DO: in a separate browser session, login as admin; GET `/playbooks/create/`
    # DO: name `Admin Public Playbook`; description ≥40 chars; visibility `public`; complete wizard as Draft first
    # DO: release the playbook to v1.0 via `[data-testid="open-release-modal"]` (draft public is owner-only)
    # RECORD `<ADMIN_PUBLIC_PB_ID>` from detail URL; confirm `[data-testid="status-badge"]` `Released`
    # STEP admin-create-private
    # DO: still as admin, create another playbook: name `Admin Private Playbook`; visibility `private`
    # RECORD `<ADMIN_PRIVATE_PB_ID>` from detail URL
    # STEP list-public-visible
    # DO: as uat_user, GET `/playbooks/`
    # SEE: `[data-testid="playbooks-list-section"]` contains `[data-testid="public-playbook-card-<ADMIN_PUBLIC_PB_ID>"]` referencing `Admin Public Playbook`
    # SEE: `[data-testid="playbooks-empty-state"]` is NOT present
    # IF DIFFER: UAT-03-05 list-public-visible
    # STEP list-private-absent
    # SEE: `Admin Private Playbook` is absent from entire page
    # IF DIFFER: UAT-03-05 list-private-absent
    # STEP public-detail-200
    # DO: GET `/playbooks/<ADMIN_PUBLIC_PB_ID>/`
    # SEE: playbook detail renders (HTTP 200); `[data-testid="edit-playbook-btn"]` and `[data-testid="delete-playbook-btn"]` are NOT present (read-only view for non-owner)
    # IF DIFFER: UAT-03-05 public-detail-200
    # STEP public-workflow-200
    # DO: GET the URL of a workflow inside `<ADMIN_PUBLIC_PB_ID>` (from workflows table on detail page)
    # SEE: workflow detail renders (HTTP 200)
    # IF DIFFER: UAT-03-05 public-workflow-200
    # STEP private-detail-404
    # DO: GET `/playbooks/<ADMIN_PRIVATE_PB_ID>/`
    # SEE: HTTP 404 (or Django permission redirect — document actual response IF DIFFER)
    # IF DIFFER: UAT-03-05 private-detail-404
    # STEP private-workflow-404
    # DO: GET any workflow URL inside `<ADMIN_PRIVATE_PB_ID>` (construct from known PK pattern if needed)
    # SEE: HTTP 404
    # IF DIFFER: UAT-03-05 private-workflow-404

  @manual @uat @act-2 @visibility
  Scenario: UAT-03-05b Toggle own playbook Private → Public → Private; nested routes follow visibility
    # Pre: uat_user owns `<GUI_PLAYBOOK_ID>` (currently Private Draft from UAT-03-01).
    # STEP toggle-to-public
    # DO: GET `/playbooks/<GUI_PLAYBOOK_ID>/edit/`; change `[data-testid="playbook-visibility-select"]` to `public`; submit
    # SEE: playbook detail `[data-testid="visibility-badge"]` (or equivalent) shows `Public`
    # STEP release-for-public-browse
    # DO: release `<GUI_PLAYBOOK_ID>` to v1.0 (draft public is owner-only for other users)
    # SEE: `[data-testid="status-badge"]` `Released`
    # IF DIFFER: UAT-03-05b release-for-public-browse
    # STEP admin-sees-public-detail
    # DO: in admin browser session, GET `/playbooks/<GUI_PLAYBOOK_ID>/`
    # SEE: HTTP 200, playbook detail renders; no Edit/Delete controls visible for admin (non-owner)
    # IF DIFFER: UAT-03-05b admin-sees-public-detail
    # STEP admin-sees-public-workflow
    # DO: admin browser GET URL of `UAT Workflow` inside `<GUI_PLAYBOOK_ID>`
    # SEE: HTTP 200
    # IF DIFFER: UAT-03-05b admin-sees-public-workflow
    # STEP revert-to-private
    # DO: as uat_user, edit `<GUI_PLAYBOOK_ID>` → visibility `private`; submit
    # SEE: visibility badge confirms `Private`
    # IF DIFFER: UAT-03-05b revert-to-private
    # STEP admin-blocked-after-revert
    # DO: admin browser GET `/playbooks/<GUI_PLAYBOOK_ID>/`
    # SEE: HTTP 404 (non-owner cannot access private playbook)
    # IF DIFFER: UAT-03-05b admin-blocked-after-revert
    # STEP admin-workflow-404-after-revert
    # DO: admin browser GET the workflow URL inside `<GUI_PLAYBOOK_ID>`
    # SEE: HTTP 404
    # IF DIFFER: UAT-03-05b admin-workflow-404-after-revert
    # STEP delete-warning-modal-cancel
    # DO: as uat_user (playbook now Private), open delete modal via `[data-testid="delete-playbook-btn"]`
    # SEE: `[data-testid="delete-modal"]` (or equivalent) renders with warning text referencing cascading deletion
    # DO: click Cancel; playbook detail still visible; playbook not deleted
    # NOTE: leave `<GUI_PLAYBOOK_ID>` as Private for Journey 5 (release flow)

  # → MCP author-scoping proof (list_playbooks/get_playbook ignore GUI visibility)
  #   is covered by mcp-uat-flow.feature MCP-01b.
#############################################################################
# Journey 4A — MCP tooling against GUI playbook → see mcp-uat-flow.feature
#############################################################################
  # MCP-01: not-found negative guards
  # MCP-02: MCP read/write/link verbs against GUI entities (GUI-01 … GUI-19)
  # MCP-03: read-back verification (list/get all entity types)
  # Run mcp-uat-flow.feature MCP-01/02/03 after completing Journey 3.

  # → MCP full lifecycle sandbox (53 tools + export/import + teardown)
  #   is covered by mcp-uat-flow.feature MCP-02 through MCP-05.
#############################################################################
# Journey 5 — Release GUI playbook v1.0 + Released edit prohibition
############################################################################

  @manual @uat @act-2-release
  Scenario: UAT-05-00 Draft playbook edit path reachable BEFORE releasing
    # DO: while `[data-testid=\"status-badge\"]` still `Draft`, GET `/playbooks/<GUI_PLAYBOOK_ID>/edit/`
    # SEE: edit markup renders WITHOUT immediate redirect flashes error

  @manual @uat @act-2-release
  Scenario: UAT-05-01 Release modal + confirm + post-release edit blocked
    # STEP Modal surface
    # DO: playbook detail `[data-testid=\"open-release-modal\"]`
    # SEE: Bootstrap modal `[data-testid=\"release-modal\"]` with textarea `[data-testid=\"release-description-input\"]`
    # STEP Confirm release baseline v1
    # DO: fill description text `UAT release — v1.0 baseline for PIP testing.`; `[data-testid=\"release-confirm\"]`
    # SEE: detail badges `[data-testid=\"status-badge\"]` `Released`; `[data-testid=\"version-badge\"]` `v1.0`; CTA `[data-testid=\"playbook-submit-pip\"]`
    # STEP Forbidden edit AFTER release canonical message
    # DO: revisit `/playbooks/<GUI_PLAYBOOK_ID>/edit/`
    # SEE: redirects detail with Django flash `[data-testid=\"alert-message\"]` EXACT `You don't have permission to edit this playbook.`
#############################################################################
# Journey 4B — Post-release MCP mutation guard → see mcp-uat-flow.feature
#############################################################################
  # MCP-07: update_activity on released playbook must fail with
  #         "Cannot modify released playbook — use create_pip instead".
  # Run mcp-uat-flow.feature MCP-07 immediately after UAT-05-01.
#############################################################################
# Journey 6 — PIPs browser UI + Galdr badges (MCP PIP lifecycle in mcp-uat-flow.feature)
############################################################################

  @manual @uat @act-9-list
  Scenario: UAT-06-00 `/pips/` list chrome + unread badge behaviour baseline
    # DO: if navbar `[data-testid=\"nav-pips-count\"]` nonzero, inspect before vs after navigating `/pips/`
    # SEE: `[data-testid=\"pip-list-page\"]`, `[data-testid=\"pip-tabs\"]` with `[data-testid=\"tab-my-pips\"]`, `[data-testid=\"pip-new-btn\"]`

  @manual @uat @act-9-create-neg
  Scenario: UAT-06-01-neg PIP create / draft validations + throwaway RECORD <PIP_NEG_PK>
    # TIMING SPLIT: Steps through `invalid playbook param`/`empty GUI title` may run BEFORE Journey 5.
    # Remaining draft-editor validations require Released playbook `<GUI_PLAYBOOK_ID>` PLUS a persisted draft RECORD `<PIP_NEG_PK>` via `/pips/create/?playbook=<GUI_PLAYBOOK_ID>` with throwaway metadata (close editor without submitting final PIP in production DB if undesired burden).
    # STEP invalid playbook param
    # DO: `/pips/create/?playbook=999999`
    # SEE: first matching Django messages alert `[data-testid=\"alert-message\"]` (class `alert-warning`) body includes `Invalid or inaccessible playbook for PIP creation.`
    # STEP empty GUI title bounce
    # DO: Released-target create path with blank `#id_title` after bypassing HTML5 if needed OR rely on constraint message
    # SEE: Django validation `Title is required.` retained OR HTML5 refusal documented
    # STEP draft editor validations (reuse dedicated throwaway RECORD `<PIP_NEG_PK>` targeting `<GUI_PLAYBOOK_ID>` after release)
    # DO: on `/pips/<PIP_NEG_PK>/edit/` attempt ALTER without `target_id`
    # SEE: flash / inline error `ALTER requires target_id.`
    # DO: ADD without name payload
    # SEE: `Name is required for ADD changes.`
    # DO: DROP rationale blank with valid target `<ACT_ALPHA_PK>`
    # SEE: `Rationale is required for DROP changes.`
    # DO: `Submit for review` with zero persisted changes via `[data-testid=\"pip-submit-review\"]`
    # SEE: error `Add at least one Change before submitting.`

  @manual @uat @act-9-happy-browser
  Scenario: UAT-06-02 GUI PIP ALTER Alpha + ADD Gamma + preview + submit Submitted RECORD <PIP_GUI_PK>
    # Given: released playbook `<GUI_PLAYBOOK_ID>` at v1.0 (UAT-05-01)
    # STEP Create draft container
    # DO: `/pips/create/?playbook=<GUI_PLAYBOOK_ID>`
    # SEE: `[data-testid=\"pip-create-page\"]`, `[data-testid=\"pip-create-playbook-hidden\"]`, disabled select labelled released target
    # DO: `#id_title` `Act 9 acceptance — UI draft ALTER Alpha + ADD Gamma`; `#id_summary` paragraph `Browser acceptance PIP for UAT Journey Playbook.`; `[data-testid=\"pip-create-submit\"]`
    # SEE: redirect `/pips/<PIP_GUI_PK>/edit/` with `[data-testid=\"pip-draft-editor\"]`
    # RECORD `<PIP_GUI_PK>`
    # STEP ALTER Alpha change
    # DO: `[data-testid=\"pip-add-change-form\"]` select `change_type=ALTER`; `entity_type=Activity`; textarea `content` multi-line ACCEPTANCE Markdown; numeric `target_id` `<ACT_ALPHA_PK>` literal; `[data-testid=\"pip-add-change-submit\"]`
    # SEE: flash `[data-testid=\"alert-message\"]` `Change added.` AND table row `[data-testid^=\"pip-change-row-\"]`
    # STEP ADD Gamma append workflow
    # DO: selects `change_type=ADD`, `entity_type=Activity`; `name` `Activity Gamma`; guidance includes `Gamma`; `[name=\"parent_workflow\"]` option equals `<GUI_WORKFLOW_ID>`; tick `[name=\"append_end\"]` Append to end; submit add change
    # SEE: TWO rows flagged with `[data-testid^=\"pip-remove-\"]`
    # STEP Preview diff browser tab sanity
    # DO: `[data-testid=\"pip-preview-link\"]` opens new tab
    # SEE: `[data-testid=\"pip-preview-page\"]`
    # STEP Submit awaiting Galdr
    # DO: `[data-testid=\"pip-submit-review\"]` POST form `[data-testid=\"pip-submit-form\"]`
    # SEE: redirected `/pips/<PIP_GUI_PK>/`; banner `[data-testid=\"pip-status-banner\"]` substring `Submitted — awaiting Galdr processing.` (text from ``PIP_DETAIL_STATIC_BANNERS[submitted]``)

  # → MCP PIP lifecycle (create_pip, add_pip_change, get_pip, list_pips, submit_pip,
  #   remove_pip_change, cancel_pip, and negatives) is covered by:
  #   mcp-uat-flow.feature MCP-08 (main PIP MCP flow RECORD <PIP_MCP_PK>)
  #   mcp-uat-flow.feature MCP-08b (disposable PIP drill)
  #   mcp-uat-flow.feature MCP-08c (create_pip on draft → error)
  # Run those scenarios after UAT-06-02.

  @manual @uat @act-9-galdr-detail
  Scenario: UAT-06-06 Detail Galdr + admin accordion instrumentation (dual PIPs)
    # NOTE: <PIP_MCP_PK> is RECORDED in mcp-uat-flow.feature MCP-08 — complete that scenario first.
    # DO: visit `/pips/<PIP_MCP_PK>/` after Galdr settles (fallback Appendix B manual promote)
    # SEE: accordion `[data-testid=\"pip-change-1\"]` etc exposes `[data-testid=\"galdr-verdict-1\"]` when populated OR absence documented; status banner transitions `Reviewed — awaiting Administrator decision.` when matched
    # DO: symmetrical pass `/pips/<PIP_GUI_PK>/`
#############################################################################
# Journey 7 — Admin finalize accepted + GUI verify (MCP inventory in mcp-uat-flow MCP-11)
############################################################################

  @manual @uat @admin
  Scenario: UAT-07-01 Django admin Accept inline decisions + mass-finalize RECORD emails
    # DO: authenticate admin `/admin/`
    # DO: `/admin/methodology/processimprovementproposal/<PIP_GUI_PK>/change/` set status `Reviewed` if stranded; EACH inline PipChange `admin_decision` Accept SAVE
    # DO: repeat sibling `<PIP_MCP_PK>` (RECORDED in mcp-uat-flow.feature MCP-08)
    # DO: `/admin/methodology/processimprovementproposal/` select rows BOTH PIPs ACTION `Finalize reviewed PIPs (apply accepted changes + notify)` Run
    # SEE: success flash lines cite `Finalised PIP-<id>` synonyms
    # DO: Gmail `<UAT_EMAIL>` subject substring referencing PIP title(s)

  @manual @uat @verify-final
  Scenario: UAT-07-02 Released v3 GUI truth + accordion ACCEPT badges + history linkage
    # DO: playbook detail textual heading includes `Released` + `v3.0`; quick-stats `4 Activities`
    # DO: playbook history tab `[data-testid=\"tab-history\"]`
    # SEE: references both PIPs / history rows cross-linking bumped versions narrative
    # DO: BOTH `/pips/<PIP_GUI_PK>/` + `/pips/<PIP_MCP_PK>/` status `Accepted`; badges `[data-testid=\"admin-verdict-<order>\"]`

  # → Post-finalize MCP inventory (list_playbooks released, list_activities,
  #   get_pip status accepted) is covered by mcp-uat-flow.feature MCP-11.
  # Run mcp-uat-flow.feature MCP-11 after completing UAT-07-02.
#############################################################################
# APPENDIX A — MCP 61-tool checklist → see mcp-uat-flow.feature
#############################################################################
  # All MCP tool coverage (Playbooks/Workflows/Activities/Phases/Skills/Agents/
  # Artifacts/Rules CRUDLF, export/import/apply, create_pip_from_protocol,
  # PIP 8-tool lifecycle) is exercised in mcp-uat-flow.feature.
  # The browser-only E2E file contains no MCP calls — no checklist needed here.
#############################################################################
# APPENDIX B — Galdr failure / rollback workaround
############################################################################
  # If PIP stalls `Submitted`: set ``GALDR_EAGER=True`` + restart server OR run ``python manage.py run_galdr <pip_pk>``
  # OR Django admin forcibly transitions status `Reviewed` before finalize (annotate runbook).
#############################################################################
# APPENDIX C — Traceability (UAT scenarios → specs)
############################################################################
  # | UAT id | Representative act feature dir |
  # | UAT-01-xx | docs/features/act-0-auth/*.feature |
  # | UAT-03-xx | docs/features/act-2-playbooks + act-4 … act-8 |
  # | UAT-06/07 | docs/features/act-9-pips (browser); act-13-mcp → mcp-uat-flow.feature |
#############################################################################
# APPENDIX D — Spec vs implementation note + optional branching
############################################################################
  # When SEE diverges materially, FIRST confirm whether DEVIATIONS block intentionally documents mismatch.
  # Optional exploratory branch AFTER happy path: deliberately reject single change combinations (UAT-07-04) — defer unless stakeholders request destructive admin experiment on disposable clone.
