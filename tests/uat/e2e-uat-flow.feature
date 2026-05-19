@manual @uat @e2e-uat-flow
Feature: Mimir E2E UAT — strict linear operator script (browser + CallMcpTool replay)

  Not collected by pytest. Execute in file order: Journey 1→2→3, then UAT-04-00/04-01/04-02 (MCP on Draft), then UAT-05-00/05-01 (release v1.0), then **UAT-04-03** (Released mutation guard), then PIP journeys UAT-06-xx and UAT-07-xx. Exception: `UAT-04-03` is numbered 04 but intentionally runs after Journey 5.

  ==============================================================================
  JOURNEY MAP (docs/features/user_journey.md ↔ this file)
  ==============================================================================
    | Journey | Intended acts | Scenario IDs |
    | J1 | Act 0–1 + profile | UAT-01-00 … UAT-01-04, UAT-01-01b, UAT-01-03b |
    | J2 | Act 12 MCP bootstrap | UAT-02-01 … UAT-02-03 |
    | J3 | Acts 2–8 + nav/search | UAT-03-00 … UAT-03-04 (+ split CRUDL) |
    | J4 | MCP tooling + sandbox | UAT-04-00, UAT-04-01, UAT-04-02 |
    | J5 | Release v1.0 | UAT-05-00, UAT-05-01 |
    | J4-post | Released MCP guard | UAT-04-03 immediately after J5 |
    | J6 | Act 9 PIPs | UAT-06-00 … UAT-06-06 |
    | J7 | Act 9 admin + verify | UAT-07-01 … UAT-07-03 (optional UAT-07-04 in Appendix D) |

  ==============================================================================
  OPERATOR SCRIPT CONTRACT
  ==============================================================================
    STEP — short title (in `# STEP` comment block)
    DO — one Browser navigation OR one CallMcpTool invocation (BASE_URL prefixed URLs)
    SEE — one observable: exact Django flash string, `[data-testid=\"…\"]`, MCP JSON invariant
    RECORD — annotate placeholder filled from SEE for downstream substitution
    IF DIFFER — file defect citing Scenario + STEP id (`Expected …; got …`)
    BUG TEMPLATE — reuse IF DIFFER line in tracker title/body
    BASE_URL — http://127.0.0.1:8000
    SELECTOR PRIORITY — data-testid → name/id attribute → readable label substring
    FLASH — Django messages use `[data-testid=\"alert-message\"]` wrapper in ``base.html``

  ==============================================================================
  DEVIATIONS (user journey narrative ↔ shipped MVP)
  ==============================================================================
    | Narrative expectation | MVP truth for this replay |
    | Congratulations + MCP token onboarding page after verify | Token only on `/auth/user/profile/` (UAT-01-04). |
    | Guided MCP onboarding screen | Operators paste Docker JSON manually (UAT-02-01). |
    | Activate playbook tile | Out of scope — skip. |
    | Notifications / Teams / GUI import/export | Skip or assert disabled only. |
    | Family/Homebase playbook sharing GUI | Metadata only; wizard visibility help + MCP owner-only guard (UAT-03-04). |
    | Submit PIP UX lock until changes | Browser may allow click; SEE server `Add at least one Change before submitting.` |

  ==============================================================================
  PLACEHOLDER REGISTRY
  ==============================================================================
    <UAT_EMAIL> <UAT_USERNAME> <UAT_PASSWORD> — operator / UAT-01-01
    <UAT_TOKEN> — UAT-01-04 profile RECORD
    <ADMIN_TOKEN> — admin user token ONLY for MCP swap during UAT-03-04
    <GUI_PLAYBOOK_ID> <GUI_WORKFLOW_ID> — wizard UAT-03-01
    <GUI_PHASE_PK> <ACT_ALPHA_PK> <ACT_BETA_PK> <GUI_AGENT_PK>
    <GUI_SKILL_PK> <GUI_ARTIFACT_PK> <GUI_RULE_PK> — GUI CRUDL splits
    <ARTIFACT_INPUT_PK> — MCP link RECORD (UAT-04-01)
    <PIP_NEG_PK> optional throwaway negatives (UAT-06-01-neg)
    <PIP_GUI_PK> <PIP_MCP_PK> — accepted journey PIPs
    <PIP_DISPOSABLE_PK> <DISPOSABLE_CHANGE_PK> — MCP cancel/remove drill
    <PIP_NEG_DRAFT_PB_ID> — MCP draft-only playbook for UAT-06-03-neg (never release)
    <MCP_EXPORT_DIR> — host temp dir (e.g. `/tmp/mimir-uat-export`)
    <MCP_SANDBOX_*>, <MCP_ACT1_PK>, <MCP_ACT2_PK>, … — sandbox marathon (UAT-04-02)

  SHARED ACTORS: uat_user (primary GUI/MCP TOKEN); admin (Django admin + optional MCP admin TOKEN).

  PRECONDITIONS: runserver reachable; SES if verifying Gmail paths; createsuperuser `admin`; ``GALDR_EAGER=True`` recommended.

  OUT OF SCOPE: teams UI, bell notifications, MCP snippet designer page, import-playbook MVP,
  activate playbook, corruption recovery tooling, exhaustive API-only sharing paths.

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

#############################################################################
# Journey 2 — MCP TOKEN wiring + smoke negatives
############################################################################

  @manual @uat @act-12-setup
  Scenario: UAT-02-01 Cursor / IDE MCP snippet (REFERENCE — operator pastes TOKEN)
    # DO: update MCP server args block per README facade pattern with `-e TOKEN=<UAT_TOKEN>` and matching BASE_URL routing (`host.docker.internal` vs `localhost`)
    # SEE: IDE reconnect acknowledges server without crashing transport handler
    # REFERENCE_TEMPLATE (preserve literal tokens — paste into MCP config as raw JSON):
    # {
    #   "mcpServers": {
    #     "mimir": {
    #       "command": "docker",
    #       "args": [
    #         "run", "--rm", "-i",
    #         "-e", "BASE_URL=http://host.docker.internal:8000",
    #         "-e", "TOKEN=<UAT_TOKEN>",
    #         "-e", "MCP_TRANSPORT=stdio",
    #         "public.ecr.aws/h1b6q4p0/mimir-mcp-facade:latest"
    #       ]
    #     }
    #   }
    # }

  @manual @uat @act-12-setup
  Scenario: UAT-02-02 MCP list_playbooks draft + all statuses
    # STEP drafted
    # DO: CallMcpTool `"user-mimir"` toolName `"list_playbooks"` arguments `{"status":"draft"}`
    # SEE: tool JSON payload parses to array element structure (no MCP-level fatal auth error payload)
    # STEP all statuses
    # DO: `"list_playbooks"` arguments `{"status":"all"}`
    # SEE: still success array (possibly longer)

  @manual @uat @act-12-setup
  Scenario: UAT-02-03 MCP TOKEN sabotage diagnostics
    # DO: deliberately mis-set TOKEN=`invalid`; invoke `list_playbooks`
    # SEE: client reports auth/transport failure substring (facet-specific → RECORD actual substring inside run-notes IF DIFFER)

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
    # SEE: `[data-testid=\"visibility-help\"]` explains owner-only; Family/Local options disabled `coming soon` per template semantics
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
    # SEE: `[data-testid=\"playbook-visibility-select\"]` with selected `Private (only me)`; `_visibility_field_help.html` `[data-testid=\"visibility-help\"]` warns owner-only semantics; dormant Family/local entries disabled hints

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
    # SEE: quick stats still ≥2 Activities until later MCP merges (post PIP bumps)

  @manual @uat @mcp-owner
  Scenario: UAT-03-04 Admin MCP cannot read alien playbook RECORD swap + rollback
    # STEP obtain admin token RECORD <ADMIN_TOKEN> (REST / profile regenerate for `admin`).
    # DO: repoint MCP client TOKEN `<ADMIN_TOKEN>` (restart MCP host).
    # DO: CallMcpTool `"get_playbook"` arguments JSON object `{\"playbook_id\":<GUI_PLAYBOOK_ID_INTEGER>}`
    # SEE: ValueError-derived payload includes substring `Playbook <GUI_PLAYBOOK_ID> not found` (privacy semantics).
    # DO: revert MCP TOKEN to `<UAT_TOKEN>` before proceeding Journey 4
    # SEE: `list_playbooks` succeeds again hinting TOKEN restored


#############################################################################
# Journey 4A — MCP precondition diagnostics + GUI-tool pass prelude
############################################################################

  @manual @uat @mcp-full
  Scenario: UAT-04-00 MCP not-found rejects (uat_user TOKEN)
    # STEP missing playbook
    # DO: CallMcpTool `"get_playbook"` arguments `{\"playbook_id\":999999}`
    # SEE: error text `Playbook 999999 not found`
    # STEP missing activity mutation
    # DO: `"update_activity"` arguments `{\"activity_id\":990000001,\"guidance\":\"## phantom\"}`
    # SEE: error substring `990000001 not found`

  @manual @uat @mcp-full @act-12
  Scenario: UAT-04-01 MCP verbs against GUI playbook (RECORD <ARTIFACT_INPUT_PK>)
    # Preconditions: MCP TOKEN restored `<UAT_TOKEN>` owns GUI entities; writable `<MCP_EXPORT_DIR>` path exists OS-level.

    # STEP GUI-01
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `id`: `<GUI_PLAYBOOK_ID>` numeric; `name` `UAT Journey Playbook`
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-01`

    # STEP GUI-02
    # DO: CallMcpTool server "user-mimir" toolName "list_workflows" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: list includes wf id/name `UAT Workflow`
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-02`

    # STEP GUI-03
    # DO: CallMcpTool server "user-mimir" toolName "list_activities" arguments {"workflow_id":"<GUI_WORKFLOW_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: entries for Alpha + Beta placeholders
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-03`

    # STEP GUI-04
    # DO: CallMcpTool server "user-mimir" toolName "get_activity" arguments {"activity_id":"<ACT_ALPHA_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: keys `agent`,`skill`,`output_artifacts`
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-04`

    # STEP GUI-05
    # DO: CallMcpTool server "user-mimir" toolName "update_activity" arguments {"activity_id":"<ACT_ALPHA_PK>","guidance":"## Alpha\\n\\nMCP-updated guidance (pre-PIP)."}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `id`: `<ACT_ALPHA_PK>` persistence
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-05`

    # STEP GUI-06
    # DO: CallMcpTool server "user-mimir" toolName "set_predecessor" arguments {"activity_id":"<ACT_BETA_PK>","predecessor_id":"<ACT_ALPHA_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `updated`: true
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-06`

    # STEP GUI-07
    # DO: CallMcpTool server "user-mimir" toolName "list_phases" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `id` `<GUI_PHASE_PK>` present
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-07`

    # STEP GUI-08
    # DO: CallMcpTool server "user-mimir" toolName "list_skills" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: skill pk
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-08`

    # STEP GUI-09
    # DO: CallMcpTool server "user-mimir" toolName "list_agents" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: agent pk
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-09`

    # STEP GUI-10
    # DO: CallMcpTool server "user-mimir" toolName "list_artifacts" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: artifact pk
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-10`

    # STEP GUI-11
    # DO: CallMcpTool server "user-mimir" toolName "list_rules" arguments {"playbook_id":"<GUI_PLAYBOOK_ID>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: rule pk
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-11`

    # STEP GUI-12
    # DO: CallMcpTool server "user-mimir" toolName "link_skill_to_activity" arguments {"activity_id":"<ACT_ALPHA_PK>","skill_id":"<GUI_SKILL_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: link ok
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-12`

    # STEP GUI-13
    # DO: CallMcpTool server "user-mimir" toolName "unlink_skill_from_activity" arguments {"activity_id":"<ACT_ALPHA_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: echo activity Alpha
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-13`

    # STEP GUI-14
    # DO: CallMcpTool server "user-mimir" toolName "link_agent_to_activity" arguments {"activity_id":"<ACT_ALPHA_PK>","agent_id":"<GUI_AGENT_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: accepted
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-14`

    # STEP GUI-15
    # DO: CallMcpTool server "user-mimir" toolName "unlink_agent_from_activity" arguments {"activity_id":"<ACT_ALPHA_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: ok
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-15`

    # STEP GUI-16
    # DO: CallMcpTool server "user-mimir" toolName "link_artifact_to_activity" arguments {"artifact_id":"<GUI_ARTIFACT_PK>","activity_id":"<ACT_BETA_PK>","is_required":true}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: RECORD `<ARTIFACT_INPUT_PK>` JSON field `id`
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-16`

    # STEP GUI-17
    # DO: CallMcpTool server "user-mimir" toolName "unlink_artifact_from_activity" arguments {"artifact_input_id":"<ARTIFACT_INPUT_PK>"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-17`

    # STEP GUI-18
    # DO: CallMcpTool server "user-mimir" toolName "set_activity_rules" arguments {"activity_id":"<ACT_ALPHA_PK>","rule_ids":["<GUI_RULE_PK>"]}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `activity_id` Alpha
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-18`

    # STEP GUI-19
    # DO: CallMcpTool server "user-mimir" toolName "export_workflow_to_local" arguments {"workflow_id":"<GUI_WORKFLOW_ID>","target_directory":"<MCP_EXPORT_DIR>/gui-workflow"}
    # NOTE: substitute angle-bracket placeholders with integers in JSON.
    # SEE: `files_written` or `export_path` present
    # IF DIFFER: Bug — cite UAT-04-01 `GUI-19`

  @manual @uat @mcp-full @sandbox
  Scenario: UAT-04-02 MCP sandbox playbook — 53 lifecycle tools + export/import + teardown deletes sandbox only
    # Preconditions / cautions — TOKEN `<UAT_TOKEN>` MUST remain isolated to disposable IDs below; canonical GUI playbook survives post-run.
    # Operator ensures `<MCP_EXPORT_DIR>` directory exists writable on host invoking MCP facade.

    # STEP SB-01
    # DO: CallMcpTool server "user-mimir" toolName "create_playbook" arguments {"name":"MCP Sandbox Playbook","description":"Disposable UAT sandbox","category":"development"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: JSON `status`=`draft`; RECORD `<MCP_SANDBOX_PB_ID>` from `.id` integer
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-01`

    # STEP SB-02
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status":"draft"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: array rows include playbook id numeric match after substitution
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-02`

    # STEP SB-03
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `name`: `MCP Sandbox Playbook`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-03`

    # STEP SB-04
    # DO: CallMcpTool server "user-mimir" toolName "update_playbook" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","description":"Updated sandbox"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `id` equals substituted sandbox pk
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-04`

    # STEP SB-05
    # DO: CallMcpTool server "user-mimir" toolName "create_workflow" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","name":"MCP Sandbox Workflow","description":"Sandbox wf"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_SANDBOX_WF_ID>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-05`

    # STEP SB-06
    # DO: CallMcpTool server "user-mimir" toolName "list_workflows" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: includes workflow id placeholder
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-06`

    # STEP SB-07
    # DO: CallMcpTool server "user-mimir" toolName "get_workflow" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: name canonical
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-07`

    # STEP SB-08
    # DO: CallMcpTool server "user-mimir" toolName "update_workflow" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>","description":"Updated wf"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-08`

    # STEP SB-09
    # DO: CallMcpTool server "user-mimir" toolName "create_phase" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","name":"MCP Phase A","description":"A"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_PHASE_A_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-09`

    # STEP SB-10
    # DO: CallMcpTool server "user-mimir" toolName "create_phase" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","name":"MCP Phase B","description":"B"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_PHASE_B_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-10`

    # STEP SB-11
    # DO: CallMcpTool server "user-mimir" toolName "list_phases" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: both sandbox phase ids enumerated
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-11`

    # STEP SB-12
    # DO: CallMcpTool server "user-mimir" toolName "get_phase" arguments {"phase_id":"<MCP_PHASE_A_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `id`: `<MCP_PHASE_A_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-12`

    # STEP SB-13
    # DO: CallMcpTool server "user-mimir" toolName "update_phase" arguments {"phase_id":"<MCP_PHASE_A_PK>","description":"Updated phase"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-13`

    # STEP SB-14
    # DO: CallMcpTool server "user-mimir" toolName "reorder_phases" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","phase_order":["<MCP_PHASE_B_PK>","<MCP_PHASE_A_PK>"]}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `reordered`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-14`

    # STEP SB-15
    # DO: CallMcpTool server "user-mimir" toolName "create_activity" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>","name":"MCP Act 1","guidance":"g1","phase_id":"<MCP_PHASE_A_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_ACT1_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-15`

    # STEP SB-16
    # DO: CallMcpTool server "user-mimir" toolName "create_activity" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>","name":"MCP Act 2","guidance":"g2","predecessor_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_ACT2_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-16`

    # STEP SB-17
    # DO: CallMcpTool server "user-mimir" toolName "list_activities" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ≥2 rows with both activity ids substituted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-17`

    # STEP SB-18
    # DO: CallMcpTool server "user-mimir" toolName "get_activity" arguments {"activity_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: keys contain `agent`, `skill`, `output_artifacts`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-18`

    # STEP SB-19
    # DO: CallMcpTool server "user-mimir" toolName "update_activity" arguments {"activity_id":"<MCP_ACT1_PK>","guidance":"Updated g1"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: persistent change
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-19`

    # STEP SB-20
    # DO: CallMcpTool server "user-mimir" toolName "set_predecessor" arguments {"activity_id":"<MCP_ACT2_PK>","predecessor_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `updated`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-20`

    # STEP SB-21
    # DO: CallMcpTool server "user-mimir" toolName "create_skill" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","title":"MCP Skill","content":"c","capability_domain":"GUI_FORM","technology_stack":"React"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_SKILL_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-21`

    # STEP SB-22
    # DO: CallMcpTool server "user-mimir" toolName "list_skills" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: contains skill pk
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-22`

    # STEP SB-23
    # DO: CallMcpTool server "user-mimir" toolName "get_skill" arguments {"skill_id":"<MCP_SKILL_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-23`

    # STEP SB-24
    # DO: CallMcpTool server "user-mimir" toolName "update_skill" arguments {"skill_id":"<MCP_SKILL_PK>","content":"Updated skill"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-24`

    # STEP SB-25
    # DO: CallMcpTool server "user-mimir" toolName "link_skill_to_activity" arguments {"activity_id":"<MCP_ACT1_PK>","skill_id":"<MCP_SKILL_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `activity_id` equals `<MCP_ACT1_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-25`

    # STEP SB-26
    # DO: CallMcpTool server "user-mimir" toolName "unlink_skill_from_activity" arguments {"activity_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: unlink ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-26`

    # STEP SB-27
    # DO: CallMcpTool server "user-mimir" toolName "delete_skill" arguments {"skill_id":"<MCP_SKILL_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-27`

    # STEP SB-28
    # DO: CallMcpTool server "user-mimir" toolName "create_agent" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","name":"MCP Agent","description":"d"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_AGENT_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-28`

    # STEP SB-29
    # DO: CallMcpTool server "user-mimir" toolName "list_agents" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: contains agent pk
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-29`

    # STEP SB-30
    # DO: CallMcpTool server "user-mimir" toolName "get_agent" arguments {"agent_id":"<MCP_AGENT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-30`

    # STEP SB-31
    # DO: CallMcpTool server "user-mimir" toolName "update_agent" arguments {"agent_id":"<MCP_AGENT_PK>","description":"Updated agent"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-31`

    # STEP SB-32
    # DO: CallMcpTool server "user-mimir" toolName "link_agent_to_activity" arguments {"activity_id":"<MCP_ACT1_PK>","agent_id":"<MCP_AGENT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-32`

    # STEP SB-33
    # DO: CallMcpTool server "user-mimir" toolName "unlink_agent_from_activity" arguments {"activity_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-33`

    # STEP SB-34
    # DO: CallMcpTool server "user-mimir" toolName "delete_agent" arguments {"agent_id":"<MCP_AGENT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-34`

    # STEP SB-35
    # DO: CallMcpTool server "user-mimir" toolName "create_artifact" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","produced_by_id":"<MCP_ACT1_PK>","name":"MCP Artifact","description":"d","type":"Document","is_required":true}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_ARTIFACT_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-35`

    # STEP SB-36
    # DO: CallMcpTool server "user-mimir" toolName "list_artifacts" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: artifact row present
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-36`

    # STEP SB-37
    # DO: CallMcpTool server "user-mimir" toolName "get_artifact" arguments {"artifact_id":"<MCP_ARTIFACT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-37`

    # STEP SB-38
    # DO: CallMcpTool server "user-mimir" toolName "update_artifact" arguments {"artifact_id":"<MCP_ARTIFACT_PK>","description":"Updated artifact"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-38`

    # STEP SB-39
    # DO: CallMcpTool server "user-mimir" toolName "link_artifact_to_activity" arguments {"artifact_id":"<MCP_ARTIFACT_PK>","activity_id":"<MCP_ACT2_PK>","is_required":true}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_ARTIFACT_INPUT_PK>` JSON `.id`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-39`

    # STEP SB-40
    # DO: CallMcpTool server "user-mimir" toolName "unlink_artifact_from_activity" arguments {"artifact_input_id":"<MCP_ARTIFACT_INPUT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-40`

    # STEP SB-41
    # DO: CallMcpTool server "user-mimir" toolName "delete_artifact" arguments {"artifact_id":"<MCP_ARTIFACT_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-41`

    # STEP SB-42
    # DO: CallMcpTool server "user-mimir" toolName "create_rule" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>","title":"MCP Rule","content":"Rule content","always_apply":true}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: RECORD `<MCP_RULE_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-42`

    # STEP SB-43
    # DO: CallMcpTool server "user-mimir" toolName "list_rules" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: contains rule pk
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-43`

    # STEP SB-44
    # DO: CallMcpTool server "user-mimir" toolName "get_rule" arguments {"rule_id":"<MCP_RULE_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: ok
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-44`

    # STEP SB-45
    # DO: CallMcpTool server "user-mimir" toolName "update_rule" arguments {"rule_id":"<MCP_RULE_PK>","content":"Updated rule"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: accepted
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-45`

    # STEP SB-46
    # DO: CallMcpTool server "user-mimir" toolName "set_activity_rules" arguments {"activity_id":"<MCP_ACT1_PK>","rule_ids":["<MCP_RULE_PK>"]}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: echo `<MCP_ACT1_PK>`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-46`

    # STEP SB-47
    # DO: CallMcpTool server "user-mimir" toolName "delete_rule" arguments {"rule_id":"<MCP_RULE_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-47`

    # STEP SB-48
    # DO: CallMcpTool server "user-mimir" toolName "export_workflow_to_local" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>","target_directory":"<MCP_EXPORT_DIR>/sandbox"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: directory with markdown tree; RECORD `<MCP_SANDBOX_EXPORT_SUBDIR>` path having `_Upload_Protocol.md`
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-48`

    # STEP SB-49
    # DO: CallMcpTool server "user-mimir" toolName "import_workflow_from_local" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>","source_directory":"<MCP_SANDBOX_EXPORT_SUBDIR>","auto_apply":false}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `changes_count` or diff keys
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-49`

    # STEP SB-50
    # DO: CallMcpTool server "user-mimir" toolName "apply_upload_protocol" arguments {"protocol_file":"<MCP_SANDBOX_EXPORT_SUBDIR>/_Upload_Protocol.md"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `changes_applied` or analogous success markers
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-50`

    # STEP SB-51
    # DO: CallMcpTool server "user-mimir" toolName "delete_activity" arguments {"activity_id":"<MCP_ACT2_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-51`

    # STEP SB-52
    # DO: CallMcpTool server "user-mimir" toolName "delete_activity" arguments {"activity_id":"<MCP_ACT1_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-52`

    # STEP SB-53
    # DO: CallMcpTool server "user-mimir" toolName "delete_phase" arguments {"phase_id":"<MCP_PHASE_A_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-53`

    # STEP SB-54
    # DO: CallMcpTool server "user-mimir" toolName "delete_phase" arguments {"phase_id":"<MCP_PHASE_B_PK>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-54`

    # STEP SB-55
    # DO: CallMcpTool server "user-mimir" toolName "delete_workflow" arguments {"workflow_id":"<MCP_SANDBOX_WF_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-55`

    # STEP SB-56
    # DO: CallMcpTool server "user-mimir" toolName "delete_playbook" arguments {"playbook_id":"<MCP_SANDBOX_PB_ID>"}
    # NOTE: replace `<…PK/B_ID…>` tokens in JSON with bare integer literals before calling.
    # SEE: `deleted`: true — GUI canonical playbook unaffected
    # IF DIFFER: Bug — snapshot MCP JSON/error; cite UAT-04-02 `SB-56`

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
# Journey 4B — Post-release MCP denial (execute after UAT-05-01)
############################################################################

  @manual @uat @act-12 @mcp-full
  Scenario: UAT-04-03 Released playbook mutation MCP denial
    # DO: MCP TOKEN `<UAT_TOKEN>`
    # DO: CallMcpTool `"update_activity"` JSON (substitute ints) `{\"activity_id\":<ACT_ALPHA_PK>,\"guidance\":\"## post-release illicit edit\"}`
    # SEE: MCP tool error substring `Cannot modify released playbook` AND `Use create_pip instead`


#############################################################################
# Journey 6 — PIPs UI + MCP drill + Galdr badges
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

  @manual @uat @mcp-pip-neg
  Scenario: UAT-06-03-neg MCP lifecycle negatives on ephemeral draft playbook
    # Pre: create MCP `create_playbook` disposable name `PIP Neg Draft MCP` RECORD `<PIP_NEG_DRAFT_PB_ID>` NEVER release it.
    # DO: MCP `create_pip` playbook_id substituted `<PIP_NEG_DRAFT_PB_ID>`
    # SEE: ValueError / tool error substring `PIP targets must be Released playbooks.`
    # DO: MCP `cancel_pip` against random unrelated id belonging to stranger (if obtainable) documenting permission text — optional skip documenting reason
    #
    Cleanup: MCP `delete_playbook` targeting `<PIP_NEG_DRAFT_PB_ID>` WHEN safe (no dependents). IF blocked, leave note manual admin cleanup.


  @manual @uat @mcp-pip-positive
  Scenario: UAT-06-04 MCP PIP ALTER Beta + ADD MCP-Gamma path RECORD <PIP_MCP_PK>
    # DO: MCP `create_pip` arguments `{\"playbook_id\":<GUI_PLAYBOOK_ID>,\"title\":\"Act 9 acceptance — MCP ALTER Beta + ADD MCP-Gamma\",\"summary\":\"Second PIP via Mimir MCP tools.\"}`
    # RECORD `.pip[\"id\"] as <PIP_MCP_PK>`
    # DO: MCP `add_pip_change` ALTER Activity Beta guidance `## MCP ALTER\n\nBeta guidance updated via MCP.`
    # DO: MCP `add_pip_change` ADD Activity name `Activity MCP-Gamma`; parent_workflow_id `<GUI_WORKFLOW_ID>`; append_to_playbook_end true ; guidance ascii snippet `MCP-Gamma`
    # DO: MCP `get_pip` verifies status draft + TWO changes pending
    # DO: MCP `list_pips` scope `mine` includes `<PIP_MCP_PK>`
    # DO: MCP `submit_pip` queues Galdr pipeline
    # SEE: stabilized status eventually `processing_galdr`/`reviewed` respecting `GALDR_EAGER` — track via MCP `get_pip` repetitions documenting timeline

  @manual @uat @mcp-pip-modify-cancel
  Scenario: UAT-06-05 MCP remove_pip_change + cancel_pip on disposable RECORD ids
    # DO: MCP `create_pip` title `UAT disposable draft PIP`; summary filler
    # RECORD `<PIP_DISPOSABLE_PK>`
    # DO: MCP `add_pip_change` ADD Activity placeholder `Throwaway` minimal body binding parent workflow numeric `<GUI_WORKFLOW_ID>` append end true RECORD `<DISPOSABLE_CHANGE_PK>`
    # DO: MCP `remove_pip_change` pip/disposable change pair
    # DO: MCP `cancel_pip` withdrawn state
    # SEE: MCP `get_pip` afterward raises not-found OR status withdrawn per service semantics

  @manual @uat @act-9-galdr-detail
  Scenario: UAT-06-06 Detail Galdr + admin accordion instrumentation (dual PIPs)
    # DO: visit `/pips/<PIP_MCP_PK>/` after Galdr settles (fallback Appendix B manual promote)
    # SEE: accordion `[data-testid=\"pip-change-1\"]` etc exposes `[data-testid=\"galdr-verdict-1\"]` when populated OR absence documented; status banner transitions `Reviewed — awaiting Administrator decision.` when matched
    # DO: symmetrical pass `/pips/<PIP_GUI_PK>/`


#############################################################################
# Journey 7 — Admin finalize accepted + MCP/GUI confirmations
############################################################################

  @manual @uat @admin
  Scenario: UAT-07-01 Django admin Accept inline decisions + mass-finalize RECORD emails
    # DO: authenticate admin `/admin/`
    # DO: `/admin/methodology/processimprovementproposal/<PIP_GUI_PK>/change/` set status `Reviewed` if stranded; EACH inline PipChange `admin_decision` Accept SAVE
    # DO: repeat sibling `<PIP_MCP_PK>`
    # DO: `/admin/methodology/processimprovementproposal/` select rows BOTH PIPs ACTION `Finalize reviewed PIPs (apply accepted changes + notify)` Run
    # SEE: success flash lines cite `Finalised PIP-<id>` synonyms
    # DO: Gmail `<UAT_EMAIL>` subject substring referencing PIP title(s)

  @manual @uat @verify-final
  Scenario: UAT-07-02 Released v3 GUI truth + accordion ACCEPT badges + history linkage
    # DO: playbook detail textual heading includes `Released` + `v3.0`; quick-stats `4 Activities`
    # DO: playbook history tab `[data-testid=\"tab-history\"]`
    # SEE: references both PIPs / history rows cross-linking bumped versions narrative
    # DO: BOTH `/pips/<PIP_GUI_PK>/` + `/pips/<PIP_MCP_PK>/` status `Accepted`; badges `[data-testid=\"admin-verdict-<order>\"]`

  @manual @uat @mcp-closure
  Scenario: UAT-07-03 MCP post-final inventories
    # DO: `list_playbooks` released filter verifying major `3.0`
    # DO: `list_activities` verifying ordered names textual includes `Activity Alpha`, `Activity Beta`, `Activity MCP-Gamma`, `Activity Gamma`
    # DO: `get_pip` each `<PIP_GUI_PK>` `<PIP_MCP_PK>` status `accepted`


#############################################################################
# APPENDIX A — MCP 61-tool checklist (scenario crosswalk)
############################################################################
  # Tick each `[x]` alongside replay. Mirrors ``tests/integration/test_mcp_e2e_all_tools.py`` naming.
  # Playbooks CRUDLF — UAT-04-02 + UAT-04-01 subsets + UAT-04-03 denial + UAT-04-00 negative
  # Workflows CRUDLF — sandbox + GUI read/export
  # Activities CRUF + predecessor — GUI+MCP interplay
  # Phases CRUD reorder — sandbox
  # Skills agents artifacts rules analogous — GUI + sandbox
  # Export/import/apply protocol — sandbox
  # ``create_pip_from_protocol`` — optional post UAT-07-03 exercised manually (released workflow export)
  # PIP MCP eight tools — journeys 06-04 … 06-05 + negatives 06-03-neg


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
  # | UAT-06/07 | docs/features/act-9-pips + act-13-mcp |


#############################################################################
# APPENDIX D — Spec vs implementation note + optional branching
############################################################################
  # When SEE diverges materially, FIRST confirm whether DEVIATIONS block intentionally documents mismatch.
  # Optional exploratory branch AFTER happy path: deliberately reject single change combinations (UAT-07-04) — defer unless stakeholders request destructive admin experiment on disposable clone.


