@manual @uat @mcp-uat-flow
Feature: Mimir MCP UAT — all 63 tools exercised end-to-end in agent mode

  Execute in AGENT MODE only. CallMcpTool is only available to the parent agent
  (Cursor IDE context). Do NOT delegate these scenarios to a browser-use subagent.

  ==============================================================================
  PRECONDITIONS
  ==============================================================================
    - Browser UAT (e2e-uat-flow.feature, Journey 1) completed:
        <UAT_USERNAME> registered, email verified, logged in, <UAT_TOKEN> recorded.
    - Django dev server running at http://host.docker.internal:8000 (Docker network)
      or http://127.0.0.1:8000 (non-Docker). Adjust BASE_URL accordingly.
    - Docker available on host (docker pull will run automatically on first use).
    - admin superuser exists in DB (`python manage.py createsuperuser`).
    - GALDR_EAGER=True set in environment or settings (speeds up PIP processing).
    - Writable temp directory available (e.g. /tmp/mimir-mcp-uat).

  ==============================================================================
  OPERATOR SCRIPT CONTRACT
  ==============================================================================
    STEP — short title
    DO   — one CallMcpTool invocation OR one Shell command OR one browser navigation
    SEE  — observable: MCP JSON key/value invariant, stdout substring, HTTP status
    RECORD — capture placeholder value from SEE output for downstream steps
    IF DIFFER — file defect; cite Scenario + STEP id
    CURSOR_PROMPT — manual one-time IDE action; agent STOPS and waits for confirmation

  ==============================================================================
  TOOL COVERAGE MAP  (all 63 tools — tick [x] during replay)
  ==============================================================================
    Playbooks   : [ ] create  [ ] list  [ ] get  [ ] update  [ ] delete
    Workflows   : [ ] create  [ ] list×2  [ ] get×2  [ ] update  [ ] delete
                  (list×2 / get×2: own playbook MCP-03 + cross-user public playbook MCP-01c)
    Phases      : [ ] create×2  [ ] list×2  [ ] get  [ ] update  [ ] reorder  [ ] delete×2
                  (list×2: own MCP-03 + cross-user public MCP-01c)
    Activities  : [ ] create×2  [ ] list  [ ] get  [ ] update  [ ] set_predecessor  [ ] delete×2
    Skills      : [ ] create  [ ] list×2  [ ] get  [ ] update  [ ] link  [ ] unlink  [ ] set_activity_skills  [ ] delete
                  (list×2: own MCP-03 + cross-user public MCP-01c)
    Agents      : [ ] create  [ ] list×2  [ ] get  [ ] update  [ ] link  [ ] unlink  [ ] delete
                  (list×2: own MCP-03 + cross-user public MCP-01c)
    Artifacts   : [ ] create  [ ] list  [ ] get  [ ] update  [ ] link  [ ] unlink  [ ] delete
    Rules       : [ ] create  [ ] list×2  [ ] get  [ ] update  [ ] set_activity_rules  [ ] delete
                  (list×2: own MCP-03 + cross-user public MCP-01c)
    Export/Import: [ ] export_workflow_to_local×2  [ ] import_workflow_from_local  [ ] apply_upload_protocol
    PIPs        : [ ] create×2  [ ] get×3  [ ] list  [ ] preview_pip_diff
                  [ ] add_pip_change×3  [ ] remove_pip_change  [ ] submit_pip×2  [ ] cancel_pip
                  [ ] create_pip_from_protocol
    Feedback    : [ ] report_bug
    (All covered across MCP-00 → MCP-11 in scenarios below)

  ==============================================================================
  PLACEHOLDER REGISTRY
  ==============================================================================
    <UAT_TOKEN>               — from browser UAT-01-04
    <BASE_URL>                — http://host.docker.internal:8000 (Docker) or http://127.0.0.1:8000
    <EXPORT_DIR>              — writable host dir, e.g. /tmp/mimir-mcp-uat
    <MCP_PB_ID>               — playbook  RECORD (MCP-02 step PB-01)
    <MCP_WF_ID>               — workflow  RECORD (MCP-02 step WF-01)
    <MCP_PH_A_PK>             — phase A   RECORD (MCP-02 step PH-01)
    <MCP_PH_B_PK>             — phase B   RECORD (MCP-02 step PH-02)
    <MCP_ACT1_PK>             — activity 1 RECORD (MCP-02 step ACT-01)
    <MCP_ACT2_PK>             — activity 2 RECORD (MCP-02 step ACT-02)
    <MCP_SKILL_PK>            — skill     RECORD (MCP-02 step SK-01)
    <MCP_SKILL_PK_2>          — second skill RECORD (MCP-02 step SK-01b)
    <MCP_AGENT_PK>            — agent     RECORD (MCP-02 step AG-01)
    <MCP_ARTIFACT_PK>         — artifact  RECORD (MCP-02 step AR-01)
    <MCP_ARTIFACT_INPUT_PK>   — artifact-activity link RECORD (MCP-02 step AR-02)
    <MCP_RULE_PK>             — rule      RECORD (MCP-02 step RU-01)
    <DRILL_PB_ID>             — delete-drill playbook RECORD (MCP-05)
    <DRILL_WF_ID>             — delete-drill workflow RECORD (MCP-05)
    <DRILL_PH_PK>             — delete-drill phase    RECORD (MCP-05)
    <DRILL_ACT_PK>            — delete-drill activity RECORD (MCP-05)
    <DRILL_SK_PK>             — delete-drill skill    RECORD (MCP-05)
    <DRILL_AG_PK>             — delete-drill agent    RECORD (MCP-05)
    <DRILL_AR_PK>             — delete-drill artifact RECORD (MCP-05)
    <DRILL_AR_INPUT_PK>       — delete-drill artifact link RECORD (MCP-05)
    <DRILL_R_PK>              — delete-drill rule     RECORD (MCP-05)
    <EXPORT_SUBDIR>           — subdirectory path from export_workflow_to_local (MCP-04)
    <EXPORT_SUBDIR_2>         — second export for create_pip_from_protocol (MCP-09)
    <PIP_MAIN_PK>             — main PIP  RECORD (MCP-08 step PM-01)
    <PIP_MAIN_CH1_PK>         — main PIP change 1 RECORD (MCP-08 step PM-02)
    <PIP_MAIN_CH2_PK>         — main PIP change 2 RECORD (MCP-08 step PM-03)
    <PIP_DISP_PK>             — disposable PIP RECORD (MCP-08b step PD-01)
    <PIP_DISP_CH_PK>          — disposable change RECORD (MCP-08b step PD-02)
    <PIP_PROTO_PK>            — protocol PIP RECORD (MCP-09 step PP-02)
    <DRAFT_NEG_PB_ID>         — draft playbook for negative PIP test (MCP-08c)
    <ADMIN_PUBLIC_WF_ID>      — any workflow id inside <ADMIN_PUBLIC_PB_ID> (MCP-01c; read from list_workflows)


#############################################################################
# MCP-00 — Configure mcp.json → Docker container with UAT token
############################################################################

  @manual @uat @mcp-setup
  Scenario: MCP-00 Wire mcp.json to Docker container with UAT token
    # STEP wire
    # DO: Shell → cd /Users/denispetelin/GitHub/mimir && python scripts/mcp_token_swap.py --token <UAT_TOKEN> --docker --server <BASE_URL>
    # SEE: stdout contains "mimir MCP server → docker image=" and "ACTION REQUIRED: Toggle"
    # IF DIFFER: MCP-00 wire
    # CURSOR_PROMPT: "Toggle the 'mimir' MCP server OFF then ON in Cursor → Settings → MCP Servers. Confirm when done."
    #
    # STEP smoke
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status": "all"}
    # SEE: response is a JSON array (may be empty); no auth error
    # IF DIFFER: MCP-00 smoke — verify Docker is running and <BASE_URL> is reachable from container


#############################################################################
# MCP-01 — Negative guards
############################################################################

  @manual @uat @mcp-neg
  Scenario: MCP-01 Negative guards — not-found + bad token + released mutation guard
    # STEP bad-token-401
    # DO: Shell → curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Token invalid" <BASE_URL>/api/playbooks/
    # SEE: stdout is exactly `401`
    # IF DIFFER: MCP-01 bad-token-401
    #
    # STEP get-playbook-not-found
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": 999999}
    # SEE: error payload contains substring `999999 not found`
    # IF DIFFER: MCP-01 get-playbook-not-found
    #
    # STEP update-activity-not-found
    # DO: CallMcpTool server "user-mimir" toolName "update_activity" arguments {"activity_id": 990000001, "guidance": "## phantom"}
    # SEE: error payload contains substring `990000001 not found`
    # IF DIFFER: MCP-01 update-activity-not-found


#############################################################################
# MCP-01b — MCP list/get follow can_view (same as web: public released cross-user; draft/other rules)
#############################################################################

  @manual @uat @mcp-visibility
  Scenario: MCP-01b MCP list_playbooks and get_playbook follow Playbook.can_view (not author-only)
    # Aligns MCP with GUI: any authenticated user may list and get another user's playbook when
    # visibility=public AND status is not draft. Public+draft from others stays hidden; private
    # from others is denied (get → not found style error).
    #
    # Pre: <ADMIN_PUBLIC_PB_ID> — admin-owned, visibility public, status released (e2e UAT-03-05).
    # Optional Pre: <ADMIN_PUBLIC_DRAFT_PB_ID> — admin-owned, visibility public, status draft (for negative get).
    # MCP token is <UAT_TOKEN> (uat_user).
    #
    # STEP list-includes-admin-public-released
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status": "all"}
    # SEE: result contains an entry with `id` equal to <ADMIN_PUBLIC_PB_ID> and `visibility` `public`
    # IF DIFFER: MCP-01b list-includes-admin-public-released
    #
    # STEP get-admin-public-released-ok
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: JSON `id` = <ADMIN_PUBLIC_PB_ID>; `visibility` = `public`; `status` is not `draft`
    # IF DIFFER: MCP-01b get-admin-public-released-ok
    #
    # STEP get-admin-public-draft-not-found (skip if optional pre missing)
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <ADMIN_PUBLIC_DRAFT_PB_ID>}
    # SEE: error payload contains substring `not found`
    # IF DIFFER: MCP-01b get-admin-public-draft-not-found
    #
    # STEP create-uat-public-draft
    # DO: CallMcpTool server "user-mimir" toolName "create_playbook" arguments {"name": "UAT Public Visibility Test", "description": "Temporary playbook for MCP can_view UAT.", "category": "development", "visibility": "public"}
    # SEE: JSON `status` = `draft`; `visibility` = `public`; RECORD `<UAT_PUBLIC_PB_ID>` from `.id`
    # IF DIFFER: MCP-01b create-uat-public-draft
    #
    # STEP get-own-public-draft-ok
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <UAT_PUBLIC_PB_ID>}
    # SEE: `id` equals <UAT_PUBLIC_PB_ID>; owner always passes can_view
    # IF DIFFER: MCP-01b get-own-public-draft-ok
    #
    # STEP admin-token-get-uat-public-draft-not-found
    # DO: Shell → python scripts/mcp_token_swap.py --token <ADMIN_TOKEN> --server http://localhost:8000
    # DO: CURSOR_PROMPT: toggle mimir MCP OFF → ON to reload with admin token; confirm when done
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <UAT_PUBLIC_PB_ID>}
    # SEE: error payload contains substring `not found` (non-owner cannot view others' public draft)
    # IF DIFFER: MCP-01b admin-token-get-uat-public-draft-not-found
    #
    # STEP admin-token-list-includes-uat-when-released (optional follow-up)
    # After uat_user releases <UAT_PUBLIC_PB_ID> via GUI/PIP (not in this flow), admin token should
    # list/get that playbook; out of scope if still draft.
    #
    # STEP restore-uat-token
    # DO: Shell → python scripts/mcp_token_swap.py --token <UAT_TOKEN> --server http://localhost:8000
    # DO: CURSOR_PROMPT: toggle mimir MCP OFF → ON to reload with UAT token; confirm when done
    # IF DIFFER: MCP-01b restore-uat-token
    #
    # STEP cleanup-delete-uat-public
    # DO: CallMcpTool server "user-mimir" toolName "delete_playbook" arguments {"playbook_id": <UAT_PUBLIC_PB_ID>}
    # SEE: `deleted`: true
    # IF DIFFER: MCP-01b cleanup-delete-uat-public


#############################################################################
# MCP-01c — Resource access parity: public playbook resources readable cross-user (bug #115)
#############################################################################

  @manual @uat @mcp-visibility
  Scenario: MCP-01c list_workflows / list_skills / list_agents / list_rules / list_phases work for public released playbooks owned by another user
    # Regression guard for bug #115:
    #   list_playbooks returned public playbooks from other users but all
    #   subsequent resource list/get calls silently returned empty results.
    #
    # Pre: <ADMIN_PUBLIC_PB_ID> — admin-owned, visibility=public, status=released.
    #      It must already have at least one workflow, skill, agent, and rule
    #      (e.g. the FeatureFactory playbook or any seeded demo playbook).
    # MCP token is <UAT_TOKEN> (uat_user — does NOT own <ADMIN_PUBLIC_PB_ID>).
    #
    # STEP cross-list-playbooks — confirm playbook still visible
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status": "all"}
    # SEE: result contains entry with `id` = <ADMIN_PUBLIC_PB_ID>
    # IF DIFFER: MCP-01c cross-list-playbooks — playbook missing; verify it is released + public
    #
    # STEP cross-list-workflows — bug #115: was returning count:0
    # DO: CallMcpTool server "user-mimir" toolName "list_workflows" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: result is a non-empty array; RECORD first entry `.id` as `<ADMIN_PUBLIC_WF_ID>`
    # IF DIFFER: MCP-01c cross-list-workflows — empty result is bug #115 regression
    #
    # STEP cross-get-workflow
    # DO: CallMcpTool server "user-mimir" toolName "get_workflow" arguments {"workflow_id": <ADMIN_PUBLIC_WF_ID>}
    # SEE: JSON `.id` = `<ADMIN_PUBLIC_WF_ID>`; no 404 / not-found error
    # IF DIFFER: MCP-01c cross-get-workflow
    #
    # STEP cross-list-phases
    # DO: CallMcpTool server "user-mimir" toolName "list_phases" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: HTTP 200; result is a JSON array (may be empty if playbook has no phases — that is OK;
    #      the key check is status 200, not a specific count)
    # IF DIFFER: MCP-01c cross-list-phases
    #
    # STEP cross-list-skills
    # DO: CallMcpTool server "user-mimir" toolName "list_skills" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: result is a JSON array; if <ADMIN_PUBLIC_PB_ID> is FeatureFactory it should be non-empty
    # IF DIFFER: MCP-01c cross-list-skills — empty result when owner has skills is bug #115 regression
    #
    # STEP cross-list-agents
    # DO: CallMcpTool server "user-mimir" toolName "list_agents" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: result is a JSON array (non-empty for FeatureFactory)
    # IF DIFFER: MCP-01c cross-list-agents
    #
    # STEP cross-list-rules
    # DO: CallMcpTool server "user-mimir" toolName "list_rules" arguments {"playbook_id": <ADMIN_PUBLIC_PB_ID>}
    # SEE: result is a JSON array (non-empty for FeatureFactory)
    # IF DIFFER: MCP-01c cross-list-rules
    #
    # STEP cross-mutation-denied — read-only enforcement must hold
    # DO: CallMcpTool server "user-mimir" toolName "update_workflow" arguments {"workflow_id": <ADMIN_PUBLIC_WF_ID>, "name": "Should fail — not owner"}
    # SEE: error payload (403 or similar); name must NOT change
    # IF DIFFER: MCP-01c cross-mutation-denied — visitor must NOT be able to write to others' playbook


#############################################################################
# MCP-02 — Build complete playbook via MCP (all create/update/link tools)
############################################################################

  @manual @uat @mcp-build
  Scenario: MCP-02 Create and populate MCP UAT Playbook (create + update + link tools)
    # STEP PB-01 create_playbook
    # DO: CallMcpTool server "user-mimir" toolName "create_playbook" arguments {"name": "MCP UAT Playbook", "description": "End-to-end MCP UAT — all tools exercised.", "category": "development", "visibility": "private"}
    # SEE: JSON `.status` = `draft`; RECORD `.id` as `<MCP_PB_ID>`
    # IF DIFFER: MCP-02 PB-01
    #
    # STEP PB-02 update_playbook
    # DO: CallMcpTool server "user-mimir" toolName "update_playbook" arguments {"playbook_id": <MCP_PB_ID>, "description": "Updated: end-to-end MCP UAT — all tools exercised."}
    # SEE: JSON `.id` = `<MCP_PB_ID>`
    # IF DIFFER: MCP-02 PB-02
    #
    # STEP WF-01 create_workflow
    # DO: CallMcpTool server "user-mimir" toolName "create_workflow" arguments {"playbook_id": <MCP_PB_ID>, "name": "MCP UAT Workflow", "description": "Primary UAT workflow."}
    # SEE: RECORD `.id` as `<MCP_WF_ID>`
    # IF DIFFER: MCP-02 WF-01
    #
    # STEP WF-02 update_workflow
    # DO: CallMcpTool server "user-mimir" toolName "update_workflow" arguments {"workflow_id": <MCP_WF_ID>, "description": "Updated: primary UAT workflow."}
    # SEE: `.id` = `<MCP_WF_ID>`
    # IF DIFFER: MCP-02 WF-02
    #
    # STEP PH-01 create_phase A
    # DO: CallMcpTool server "user-mimir" toolName "create_phase" arguments {"playbook_id": <MCP_PB_ID>, "name": "Phase Alpha", "description": "First phase."}
    # SEE: RECORD `.id` as `<MCP_PH_A_PK>`
    # IF DIFFER: MCP-02 PH-01
    #
    # STEP PH-02 create_phase B
    # DO: CallMcpTool server "user-mimir" toolName "create_phase" arguments {"playbook_id": <MCP_PB_ID>, "name": "Phase Beta", "description": "Second phase."}
    # SEE: RECORD `.id` as `<MCP_PH_B_PK>`
    # IF DIFFER: MCP-02 PH-02
    #
    # STEP PH-03 reorder_phases — put Beta before Alpha
    # DO: CallMcpTool server "user-mimir" toolName "reorder_phases" arguments {"playbook_id": <MCP_PB_ID>, "phase_order": [<MCP_PH_B_PK>, <MCP_PH_A_PK>]}
    # SEE: JSON `.reordered` = true OR success indicator
    # IF DIFFER: MCP-02 PH-03
    #
    # STEP PH-04 update_phase
    # DO: CallMcpTool server "user-mimir" toolName "update_phase" arguments {"phase_id": <MCP_PH_A_PK>, "description": "Updated: first phase."}
    # SEE: `.id` = `<MCP_PH_A_PK>`
    # IF DIFFER: MCP-02 PH-04
    #
    # STEP ACT-01 create_activity 1
    # DO: CallMcpTool server "user-mimir" toolName "create_activity" arguments {"workflow_id": <MCP_WF_ID>, "name": "MCP Activity One", "guidance": "## MCP Activity One\n\nInitial guidance for activity one.", "phase_id": <MCP_PH_A_PK>}
    # SEE: RECORD `.id` as `<MCP_ACT1_PK>`
    # IF DIFFER: MCP-02 ACT-01
    #
    # STEP ACT-02 create_activity 2
    # DO: CallMcpTool server "user-mimir" toolName "create_activity" arguments {"workflow_id": <MCP_WF_ID>, "name": "MCP Activity Two", "guidance": "## MCP Activity Two\n\nInitial guidance for activity two.", "phase_id": <MCP_PH_B_PK>}
    # SEE: RECORD `.id` as `<MCP_ACT2_PK>`
    # IF DIFFER: MCP-02 ACT-02
    #
    # STEP ACT-03 update_activity
    # DO: CallMcpTool server "user-mimir" toolName "update_activity" arguments {"activity_id": <MCP_ACT1_PK>, "guidance": "## MCP Activity One\n\nUpdated guidance — MCP write verified."}
    # SEE: `.id` = `<MCP_ACT1_PK>`
    # IF DIFFER: MCP-02 ACT-03
    #
    # STEP ACT-04 set_predecessor — Act2 comes after Act1
    # DO: CallMcpTool server "user-mimir" toolName "set_predecessor" arguments {"activity_id": <MCP_ACT2_PK>, "predecessor_id": <MCP_ACT1_PK>}
    # SEE: JSON `.updated` = true OR success echo
    # IF DIFFER: MCP-02 ACT-04
    #
    # STEP SK-01 create_skill
    # DO: CallMcpTool server "user-mimir" toolName "create_skill" arguments {"playbook_id": <MCP_PB_ID>, "title": "MCP UAT Skill", "content": "## Skill\n\nDo the thing.", "capability_domain": "Backend", "technology_stack": "Django+Python"}
    # SEE: RECORD `.id` as `<MCP_SKILL_PK>`
    # IF DIFFER: MCP-02 SK-01
    #
    # STEP SK-02 update_skill
    # DO: CallMcpTool server "user-mimir" toolName "update_skill" arguments {"skill_id": <MCP_SKILL_PK>, "content": "## Skill\n\nUpdated skill content."}
    # SEE: `.id` = `<MCP_SKILL_PK>`
    # IF DIFFER: MCP-02 SK-02
    #
    # STEP SK-03 link_skill_to_activity (first skill)
    # DO: CallMcpTool server "user-mimir" toolName "link_skill_to_activity" arguments {"skill_id": <MCP_SKILL_PK>, "activity_id": <MCP_ACT1_PK>}
    # SEE: JSON `.skill_ids` contains `<MCP_SKILL_PK>`
    # IF DIFFER: MCP-02 SK-03
    #
    # STEP SK-03b link second skill (M2M add)
    # DO: CallMcpTool server "user-mimir" toolName "create_skill" arguments {"playbook_id": <MCP_PB_ID>, "title": "MCP UAT Skill Two", "content": "## Alt\n", "capability_domain": "DEPLOY", "technology_stack": "AWS+EKS"}
    # SEE: RECORD `.id` as `<MCP_SKILL_PK_2>`
    # DO: CallMcpTool server "user-mimir" toolName "link_skill_to_activity" arguments {"skill_id": <MCP_SKILL_PK_2>, "activity_id": <MCP_ACT1_PK>}
    # SEE: JSON `.skill_ids` length = 2
    # IF DIFFER: MCP-02 SK-03b
    #
    # STEP SK-03c set_activity_skills replace set
    # DO: CallMcpTool server "user-mimir" toolName "set_activity_skills" arguments {"activity_id": <MCP_ACT1_PK>, "skill_ids": [<MCP_SKILL_PK_2>]}
    # SEE: JSON `.skill_ids` = [<MCP_SKILL_PK_2>]
    # IF DIFFER: MCP-02 SK-03c
    #
    # STEP AG-01 create_agent
    # DO: CallMcpTool server "user-mimir" toolName "create_agent" arguments {"playbook_id": <MCP_PB_ID>, "name": "MCP UAT Agent", "description": "Test agent persona for MCP UAT."}
    # SEE: RECORD `.id` as `<MCP_AGENT_PK>`
    # IF DIFFER: MCP-02 AG-01
    #
    # STEP AG-02 update_agent
    # DO: CallMcpTool server "user-mimir" toolName "update_agent" arguments {"agent_id": <MCP_AGENT_PK>, "description": "Updated agent description."}
    # SEE: `.id` = `<MCP_AGENT_PK>`
    # IF DIFFER: MCP-02 AG-02
    #
    # STEP AG-03 link_agent_to_activity
    # DO: CallMcpTool server "user-mimir" toolName "link_agent_to_activity" arguments {"agent_id": <MCP_AGENT_PK>, "activity_id": <MCP_ACT1_PK>}
    # SEE: success response
    # IF DIFFER: MCP-02 AG-03
    #
    # STEP AR-01 create_artifact
    # DO: CallMcpTool server "user-mimir" toolName "create_artifact" arguments {"playbook_id": <MCP_PB_ID>, "name": "MCP UAT Artifact", "description": "Output document.", "type": "Document", "is_required": true, "produced_by_id": <MCP_ACT1_PK>}
    # SEE: RECORD `.id` as `<MCP_ARTIFACT_PK>`
    # IF DIFFER: MCP-02 AR-01
    #
    # STEP AR-02 update_artifact
    # DO: CallMcpTool server "user-mimir" toolName "update_artifact" arguments {"artifact_id": <MCP_ARTIFACT_PK>, "description": "Updated output document."}
    # SEE: `.id` = `<MCP_ARTIFACT_PK>`
    # IF DIFFER: MCP-02 AR-02
    #
    # STEP AR-03 link_artifact_to_activity (Act2 consumes artifact from Act1)
    # DO: CallMcpTool server "user-mimir" toolName "link_artifact_to_activity" arguments {"artifact_id": <MCP_ARTIFACT_PK>, "activity_id": <MCP_ACT2_PK>, "is_required": true}
    # SEE: RECORD `.id` as `<MCP_ARTIFACT_INPUT_PK>`
    # IF DIFFER: MCP-02 AR-03
    #
    # STEP RU-01 create_rule  (no slug supplied — server auto-generates from title)
    # DO: CallMcpTool server "user-mimir" toolName "create_rule" arguments {"playbook_id": <MCP_PB_ID>, "title": "MCP UAT Rule", "content": "Always verify MCP writes.", "always_apply": true}
    # SEE: JSON `.slug` is non-empty (e.g. `mcp-uat-rule`); RECORD `.id` as `<MCP_RULE_PK>`
    # IF DIFFER: MCP-02 RU-01 — slug missing means RuleViewSet.create() is not delegating to RuleService
    #
    # STEP RU-02 update_rule
    # DO: CallMcpTool server "user-mimir" toolName "update_rule" arguments {"rule_id": <MCP_RULE_PK>, "content": "Updated: always verify MCP writes."}
    # SEE: `.id` = `<MCP_RULE_PK>`
    # IF DIFFER: MCP-02 RU-02
    #
    # STEP RU-03 set_activity_rules — assign rule to Act1
    # DO: CallMcpTool server "user-mimir" toolName "set_activity_rules" arguments {"activity_id": <MCP_ACT1_PK>, "rule_ids": [<MCP_RULE_PK>]}
    # SEE: JSON `.activity_id` = `<MCP_ACT1_PK>`
    # IF DIFFER: MCP-02 RU-03


#############################################################################
# MCP-03 — Read-back verification (all list/get tools)
############################################################################

  @manual @uat @mcp-read
  Scenario: MCP-03 Read-back all entities (list + get tools)
    # STEP list_playbooks
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status": "draft"}
    # SEE: array contains entry with `.id` = `<MCP_PB_ID>` and `.name` = `MCP UAT Playbook`
    # IF DIFFER: MCP-03 list_playbooks
    #
    # STEP get_playbook
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: `.status` = `draft`; `.name` = `MCP UAT Playbook`
    # IF DIFFER: MCP-03 get_playbook
    #
    # STEP list_workflows
    # DO: CallMcpTool server "user-mimir" toolName "list_workflows" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains entry with `.id` = `<MCP_WF_ID>`
    # IF DIFFER: MCP-03 list_workflows
    #
    # STEP get_workflow
    # DO: CallMcpTool server "user-mimir" toolName "get_workflow" arguments {"workflow_id": <MCP_WF_ID>}
    # SEE: `.name` = `MCP UAT Workflow`
    # IF DIFFER: MCP-03 get_workflow
    #
    # STEP list_phases
    # DO: CallMcpTool server "user-mimir" toolName "list_phases" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains both `<MCP_PH_A_PK>` and `<MCP_PH_B_PK>`; Beta appears before Alpha (reorder verified)
    # IF DIFFER: MCP-03 list_phases
    #
    # STEP get_phase
    # DO: CallMcpTool server "user-mimir" toolName "get_phase" arguments {"phase_id": <MCP_PH_A_PK>}
    # SEE: `.name` = `Phase Alpha`
    # IF DIFFER: MCP-03 get_phase
    #
    # STEP list_activities
    # DO: CallMcpTool server "user-mimir" toolName "list_activities" arguments {"workflow_id": <MCP_WF_ID>}
    # SEE: array contains `<MCP_ACT1_PK>` and `<MCP_ACT2_PK>`; Act2 predecessor = Act1 (set_predecessor verified)
    # IF DIFFER: MCP-03 list_activities
    #
    # STEP get_activity
    # DO: CallMcpTool server "user-mimir" toolName "get_activity" arguments {"activity_id": <MCP_ACT1_PK>}
    # SEE: `.name` = `MCP Activity One`; guidance contains `Updated guidance — MCP write verified`; `.skills` array contains linked skill; agent/rule present
    # IF DIFFER: MCP-03 get_activity
    #
    # STEP list_skills
    # DO: CallMcpTool server "user-mimir" toolName "list_skills" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains `<MCP_SKILL_PK>`
    # IF DIFFER: MCP-03 list_skills
    #
    # STEP get_skill
    # DO: CallMcpTool server "user-mimir" toolName "get_skill" arguments {"skill_id": <MCP_SKILL_PK>}
    # SEE: `.title` = `MCP UAT Skill`
    # IF DIFFER: MCP-03 get_skill
    #
    # STEP list_agents
    # DO: CallMcpTool server "user-mimir" toolName "list_agents" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains `<MCP_AGENT_PK>`
    # IF DIFFER: MCP-03 list_agents
    #
    # STEP get_agent
    # DO: CallMcpTool server "user-mimir" toolName "get_agent" arguments {"agent_id": <MCP_AGENT_PK>}
    # SEE: `.name` = `MCP UAT Agent`
    # IF DIFFER: MCP-03 get_agent
    #
    # STEP list_artifacts
    # DO: CallMcpTool server "user-mimir" toolName "list_artifacts" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains `<MCP_ARTIFACT_PK>`
    # IF DIFFER: MCP-03 list_artifacts
    #
    # STEP get_artifact
    # DO: CallMcpTool server "user-mimir" toolName "get_artifact" arguments {"artifact_id": <MCP_ARTIFACT_PK>}
    # SEE: `.name` = `MCP UAT Artifact`
    # IF DIFFER: MCP-03 get_artifact
    #
    # STEP list_rules
    # DO: CallMcpTool server "user-mimir" toolName "list_rules" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: array contains `<MCP_RULE_PK>`
    # IF DIFFER: MCP-03 list_rules
    #
    # STEP get_rule
    # DO: CallMcpTool server "user-mimir" toolName "get_rule" arguments {"rule_id": <MCP_RULE_PK>}
    # SEE: `.title` = `MCP UAT Rule`
    # IF DIFFER: MCP-03 get_rule


#############################################################################
# MCP-04 — Export / import round-trip (export + import + apply_upload_protocol)
############################################################################

  @manual @uat @mcp-export
  Scenario: MCP-04 Export workflow → import change detection → apply upload protocol
    # STEP EX-01 export_workflow_to_local
    # DO: Shell → mkdir -p <EXPORT_DIR>
    # DO: CallMcpTool server "user-mimir" toolName "export_workflow_to_local" arguments {"workflow_id": <MCP_WF_ID>, "target_directory": "<EXPORT_DIR>"}
    # SEE: response contains `files_written` > 0 OR `export_path`; RECORD the exported subdirectory path as `<EXPORT_SUBDIR>`
    # IF DIFFER: MCP-04 EX-01
    #
    # STEP EX-02 import_workflow_from_local (no changes — verifies round-trip parity)
    # DO: CallMcpTool server "user-mimir" toolName "import_workflow_from_local" arguments {"workflow_id": <MCP_WF_ID>, "source_directory": "<EXPORT_SUBDIR>", "auto_apply": false}
    # SEE: JSON `.changes_count` = 0 (clean round-trip; section terminators + null-guidance normalization fixed)
    #      `_Upload_Protocol.md` path present in response
    # IF DIFFER: MCP-04 EX-02 — changes_count > 0 is a regression in _detect_changes or _parse_activity_md
    #
    # STEP EX-03 apply_upload_protocol (0-change apply is a valid no-op)
    # DO: CallMcpTool server "user-mimir" toolName "apply_upload_protocol" arguments {"protocol_file": "<EXPORT_SUBDIR>/_Upload_Protocol.md"}
    # SEE: JSON `.changes_applied` = 0 AND no error
    # IF DIFFER: MCP-04 EX-03


#############################################################################
# MCP-05 — Delete drill (dedicated mini-playbook; tests all delete/unlink tools)
############################################################################

  @manual @uat @mcp-delete
  Scenario: MCP-05 Delete drill — create mini-playbook, unlink all, delete all
    # Create a throwaway playbook solely to exercise delete operations.
    #
    # STEP DL-01 create drill playbook
    # DO: CallMcpTool server "user-mimir" toolName "create_playbook" arguments {"name": "MCP Delete Drill", "description": "Throwaway — deleted at end of this scenario.", "category": "development"}
    # SEE: RECORD `.id` as `<DRILL_PB_ID>`
    # IF DIFFER: MCP-05 DL-01
    #
    # STEP DL-02 create drill workflow
    # DO: CallMcpTool server "user-mimir" toolName "create_workflow" arguments {"playbook_id": <DRILL_PB_ID>, "name": "Drill WF", "description": "d"}
    # SEE: RECORD `.id` as `<DRILL_WF_ID>`
    # IF DIFFER: MCP-05 DL-02
    #
    # STEP DL-03 create drill phase
    # DO: CallMcpTool server "user-mimir" toolName "create_phase" arguments {"playbook_id": <DRILL_PB_ID>, "name": "Drill Phase", "description": "d"}
    # SEE: RECORD `.id` as `<DRILL_PH_PK>`
    # IF DIFFER: MCP-05 DL-03
    #
    # STEP DL-04 create drill activity
    # DO: CallMcpTool server "user-mimir" toolName "create_activity" arguments {"workflow_id": <DRILL_WF_ID>, "name": "Drill Act", "guidance": "d"}
    # SEE: RECORD `.id` as `<DRILL_ACT_PK>`
    # IF DIFFER: MCP-05 DL-04
    #
    # STEP DL-05 create drill skill
    # DO: CallMcpTool server "user-mimir" toolName "create_skill" arguments {"playbook_id": <DRILL_PB_ID>, "title": "Drill Skill", "content": "d", "capability_domain": "Backend", "technology_stack": "Python"}
    # SEE: RECORD `.id` as `<DRILL_SK_PK>`
    # IF DIFFER: MCP-05 DL-05
    #
    # STEP DL-06 create drill agent
    # DO: CallMcpTool server "user-mimir" toolName "create_agent" arguments {"playbook_id": <DRILL_PB_ID>, "name": "Drill Agent", "description": "d"}
    # SEE: RECORD `.id` as `<DRILL_AG_PK>`
    # IF DIFFER: MCP-05 DL-06
    #
    # STEP DL-07 create drill artifact
    # DO: CallMcpTool server "user-mimir" toolName "create_artifact" arguments {"playbook_id": <DRILL_PB_ID>, "name": "Drill Artifact", "description": "d", "type": "Document", "is_required": false, "produced_by_id": <DRILL_ACT_PK>}
    # SEE: RECORD `.id` as `<DRILL_AR_PK>`
    # IF DIFFER: MCP-05 DL-07
    #
    # STEP DL-08 create drill rule  (no slug supplied — auto-generated)
    # DO: CallMcpTool server "user-mimir" toolName "create_rule" arguments {"playbook_id": <DRILL_PB_ID>, "title": "Drill Rule", "content": "d", "always_apply": false}
    # SEE: JSON `.slug` is non-empty; RECORD `.id` as `<DRILL_R_PK>`
    # IF DIFFER: MCP-05 DL-08
    #
    # STEP DL-09 link skill + agent + artifact + rule to drill activity
    # DO: CallMcpTool server "user-mimir" toolName "link_skill_to_activity" arguments {"skill_id": <DRILL_SK_PK>, "activity_id": <DRILL_ACT_PK>}
    # SEE: success
    # DO: CallMcpTool server "user-mimir" toolName "link_agent_to_activity" arguments {"agent_id": <DRILL_AG_PK>, "activity_id": <DRILL_ACT_PK>}
    # SEE: success
    # DO: CallMcpTool server "user-mimir" toolName "link_artifact_to_activity" arguments {"artifact_id": <DRILL_AR_PK>, "activity_id": <DRILL_ACT_PK>, "is_required": false}
    # SEE: RECORD `.id` as `<DRILL_AR_INPUT_PK>`
    # DO: CallMcpTool server "user-mimir" toolName "set_activity_rules" arguments {"activity_id": <DRILL_ACT_PK>, "rule_ids": [<DRILL_R_PK>]}
    # SEE: success
    # IF DIFFER: MCP-05 DL-09
    #
    # STEP DL-10 unlink all from drill activity
    # DO: CallMcpTool server "user-mimir" toolName "unlink_skill_from_activity" arguments {"activity_id": <DRILL_ACT_PK>, "skill_id": <DRILL_SK_PK>}
    # SEE: success
    # DO: CallMcpTool server "user-mimir" toolName "unlink_agent_from_activity" arguments {"activity_id": <DRILL_ACT_PK>}
    # SEE: success
    # DO: CallMcpTool server "user-mimir" toolName "unlink_artifact_from_activity" arguments {"artifact_input_id": <DRILL_AR_INPUT_PK>}
    # SEE: JSON `.deleted` = true
    # IF DIFFER: MCP-05 DL-10
    #
    # STEP DL-11 delete leaf entities
    # DO: CallMcpTool server "user-mimir" toolName "delete_artifact" arguments {"artifact_id": <DRILL_AR_PK>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_skill" arguments {"skill_id": <DRILL_SK_PK>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_agent" arguments {"agent_id": <DRILL_AG_PK>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_rule" arguments {"rule_id": <DRILL_R_PK>}
    # SEE: JSON `.deleted` = true
    # IF DIFFER: MCP-05 DL-11
    #
    # STEP DL-12 delete structural entities
    # DO: CallMcpTool server "user-mimir" toolName "delete_activity" arguments {"activity_id": <DRILL_ACT_PK>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_phase" arguments {"phase_id": <DRILL_PH_PK>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_workflow" arguments {"workflow_id": <DRILL_WF_ID>}
    # SEE: JSON `.deleted` = true
    # DO: CallMcpTool server "user-mimir" toolName "delete_playbook" arguments {"playbook_id": <DRILL_PB_ID>}
    # SEE: JSON `.deleted` = true
    # IF DIFFER: MCP-05 DL-12


#############################################################################
# MCP-06 — GUI: Release MCP UAT Playbook v1.0 (no release_playbook MCP tool)
############################################################################

  @manual @uat @mcp-release @browser
  Scenario: MCP-06 Release MCP UAT Playbook via GUI (browser step)
    # STEP open release modal
    # DO: browser GET <BASE_URL>/playbooks/<MCP_PB_ID>/
    # SEE: `[data-testid="playbook-detail"]` AND `[data-testid="status-badge"]` text `Draft`
    # DO: click `[data-testid="open-release-modal"]`
    # SEE: Bootstrap modal `[data-testid="release-modal"]`
    #
    # STEP confirm release
    # DO: fill `[data-testid="release-description-input"]` `MCP UAT release — v1.0 baseline.`; click `[data-testid="release-confirm"]`
    # SEE: `[data-testid="status-badge"]` text `Released` AND `[data-testid="version-badge"]` text `v1.0`
    # IF DIFFER: MCP-06 release


#############################################################################
# MCP-07 — Post-release MCP mutation guard
############################################################################

  @manual @uat @mcp-guard
  Scenario: MCP-07 Released playbook MCP mutation guard
    # STEP mutation-denied
    # DO: CallMcpTool server "user-mimir" toolName "update_activity" arguments {"activity_id": <MCP_ACT1_PK>, "guidance": "## Illicit post-release edit"}
    # SEE: error payload contains substring `Cannot modify released playbook` OR `Use create_pip instead`
    # IF DIFFER: MCP-07 mutation-denied


#############################################################################
# MCP-08 — PIP lifecycle: create → add changes → preview → list → submit
############################################################################

  @manual @uat @mcp-pip
  Scenario: MCP-08 PIP lifecycle — ALTER activity + ADD activity → preview → submit
    # Precondition: MCP UAT Playbook is Released (v1.0) from MCP-06.
    #
    # STEP PM-01 create_pip
    # DO: CallMcpTool server "user-mimir" toolName "create_pip" arguments {"playbook_id": <MCP_PB_ID>, "title": "MCP UAT PIP — ALTER Act1 + ADD Act3", "summary": "Alters activity one guidance and adds a third activity."}
    # SEE: JSON `.status` = `draft`; RECORD `.id` as `<PIP_MAIN_PK>`
    # IF DIFFER: MCP-08 PM-01
    #
    # STEP PM-02 add_pip_change — ALTER Act1 guidance
    # DO: CallMcpTool server "user-mimir" toolName "add_pip_change" arguments {"pip_id": <PIP_MAIN_PK>, "change_type": "ALTER", "entity_type": "Activity", "target_id": <MCP_ACT1_PK>, "content": "## MCP Activity One\n\nPIP-proposed updated guidance."}
    # SEE: RECORD `.id` as `<PIP_MAIN_CH1_PK>`
    # IF DIFFER: MCP-08 PM-02
    #
    # STEP PM-03 add_pip_change — ADD new activity (MCP Activity Three)
    # DO: CallMcpTool server "user-mimir" toolName "add_pip_change" arguments {"pip_id": <PIP_MAIN_PK>, "change_type": "ADD", "entity_type": "Activity", "name": "MCP Activity Three", "content": "## MCP Activity Three\n\nAdded via PIP.", "parent_workflow_id": <MCP_WF_ID>}
    # SEE: RECORD `.id` as `<PIP_MAIN_CH2_PK>`
    # IF DIFFER: MCP-08 PM-03
    #
    # STEP PM-04 get_pip — verify draft with 2 changes
    # DO: CallMcpTool server "user-mimir" toolName "get_pip" arguments {"pip_id": <PIP_MAIN_PK>}
    # SEE: `.status` = `draft`; changes list length = 2
    # IF DIFFER: MCP-08 PM-04
    #
    # STEP PM-05 list_pips — own scope includes PIP
    # DO: CallMcpTool server "user-mimir" toolName "list_pips" arguments {"scope": "mine"}
    # SEE: array contains entry with `.id` = `<PIP_MAIN_PK>`
    # IF DIFFER: MCP-08 PM-05
    #
    # STEP PM-06 preview_pip_diff
    # DO: CallMcpTool server "user-mimir" toolName "preview_pip_diff" arguments {"pip_id": <PIP_MAIN_PK>}
    # SEE: response contains diff structure (keys like `changes`, `before`, `after`, or `diff`)
    # IF DIFFER: MCP-08 PM-06
    #
    # STEP PM-07 submit_pip
    # DO: CallMcpTool server "user-mimir" toolName "submit_pip" arguments {"pip_id": <PIP_MAIN_PK>}
    # SEE: JSON `.status` in [`submitted`, `processing_galdr`, `reviewed`] (depends on GALDR_EAGER setting)
    # IF DIFFER: MCP-08 PM-07


#############################################################################
# MCP-08b — Disposable PIP drill: add change → remove → cancel
############################################################################

  @manual @uat @mcp-pip-disp
  Scenario: MCP-08b Disposable PIP — add_pip_change → remove_pip_change → cancel_pip
    # STEP PD-01 create disposable PIP
    # DO: CallMcpTool server "user-mimir" toolName "create_pip" arguments {"playbook_id": <MCP_PB_ID>, "title": "UAT Disposable PIP — cancel drill", "summary": "Created to test remove_pip_change and cancel_pip."}
    # SEE: `.status` = `draft`; RECORD `.id` as `<PIP_DISP_PK>`
    # IF DIFFER: MCP-08b PD-01
    #
    # STEP PD-02 add_pip_change to disposable
    # DO: CallMcpTool server "user-mimir" toolName "add_pip_change" arguments {"pip_id": <PIP_DISP_PK>, "change_type": "ADD", "entity_type": "Activity", "name": "Throwaway Activity", "content": "Throwaway.", "parent_workflow_id": <MCP_WF_ID>}
    # SEE: RECORD `.id` as `<PIP_DISP_CH_PK>`
    # IF DIFFER: MCP-08b PD-02
    #
    # STEP PD-03 remove_pip_change
    # DO: CallMcpTool server "user-mimir" toolName "remove_pip_change" arguments {"pip_id": <PIP_DISP_PK>, "change_id": <PIP_DISP_CH_PK>}
    # SEE: success (change removed; PIP has 0 changes)
    # IF DIFFER: MCP-08b PD-03
    #
    # STEP PD-04 cancel_pip
    # DO: CallMcpTool server "user-mimir" toolName "cancel_pip" arguments {"pip_id": <PIP_DISP_PK>}
    # SEE: JSON `.status` in [`cancelled`, `withdrawn`]
    # IF DIFFER: MCP-08b PD-04
    #
    # STEP PD-05 get_pip post-cancel confirmation
    # DO: CallMcpTool server "user-mimir" toolName "get_pip" arguments {"pip_id": <PIP_DISP_PK>}
    # SEE: `.status` in [`cancelled`, `withdrawn`]
    # IF DIFFER: MCP-08b PD-05


#############################################################################
# MCP-08c — Negative: create_pip on draft playbook must fail
############################################################################

  @manual @uat @mcp-pip-neg
  Scenario: MCP-08c create_pip on draft playbook fails with correct error
    # STEP PN-01 create temporary draft playbook
    # DO: CallMcpTool server "user-mimir" toolName "create_playbook" arguments {"name": "Draft PIP Target — delete me", "description": "Never released — for negative PIP test only.", "category": "development"}
    # SEE: `.status` = `draft`; RECORD `.id` as `<DRAFT_NEG_PB_ID>`
    # IF DIFFER: MCP-08c PN-01
    #
    # STEP PN-02 create_pip on draft — must fail
    # DO: CallMcpTool server "user-mimir" toolName "create_pip" arguments {"playbook_id": <DRAFT_NEG_PB_ID>, "title": "Should fail"}
    # SEE: error payload contains substring `Released` OR `cannot create PIP` (draft playbooks not eligible)
    # IF DIFFER: MCP-08c PN-02
    #
    # STEP PN-03 cleanup: delete the draft playbook
    # DO: CallMcpTool server "user-mimir" toolName "delete_playbook" arguments {"playbook_id": <DRAFT_NEG_PB_ID>}
    # SEE: JSON `.deleted` = true
    # IF DIFFER: MCP-08c PN-03


#############################################################################
# MCP-09 — create_pip_from_protocol (export released workflow → edit locally → PIP)
############################################################################

  @manual @uat @mcp-pip-proto
  Scenario: MCP-09 create_pip_from_protocol — edit exported markdown → PIP from protocol
    # STEP PP-01 export released workflow to a fresh directory
    # DO: Shell → mkdir -p <EXPORT_DIR>/proto
    # DO: CallMcpTool server "user-mimir" toolName "export_workflow_to_local" arguments {"workflow_id": <MCP_WF_ID>, "target_directory": "<EXPORT_DIR>/proto"}
    # SEE: `files_written` > 0; RECORD exported subdirectory as `<EXPORT_SUBDIR_2>`
    # IF DIFFER: MCP-09 PP-01
    #
    # STEP PP-01b edit one activity markdown to introduce a change
    # DO: Shell → find <EXPORT_SUBDIR_2> -name "*.md" | grep -i act | head -1 → prints a path <ACT_MD_FILE>
    # DO: Shell → echo "\n\nProtocol-PIP addition — appended by MCP-09." >> <ACT_MD_FILE>
    # SEE: exit code 0
    # IF DIFFER: MCP-09 PP-01b
    #
    # STEP PP-01c import to detect the edit and regenerate _Upload_Protocol.md
    # DO: CallMcpTool server "user-mimir" toolName "import_workflow_from_local" arguments {"workflow_id": <MCP_WF_ID>, "source_directory": "<EXPORT_SUBDIR_2>", "auto_apply": false}
    # SEE: JSON `.changes_count` ≥ 1 (the appended line detected)
    # IF DIFFER: MCP-09 PP-01c
    #
    # STEP PP-02 create_pip_from_protocol
    # DO: CallMcpTool server "user-mimir" toolName "create_pip_from_protocol" arguments {"protocol_file": "<EXPORT_SUBDIR_2>/_Upload_Protocol.md", "pip_title": "MCP-09 UAT — PIP from upload protocol"}
    # SEE: JSON `.pip_id` present; RECORD as `<PIP_PROTO_PK>`
    # IF DIFFER: MCP-09 PP-02
    #
    # STEP PP-03 get_pip — verify draft with changes
    # DO: CallMcpTool server "user-mimir" toolName "get_pip" arguments {"pip_id": <PIP_PROTO_PK>}
    # SEE: `.status` = `draft`; changes list length ≥ 1
    # IF DIFFER: MCP-09 PP-03
    #
    # STEP PP-04 submit_pip
    # DO: CallMcpTool server "user-mimir" toolName "submit_pip" arguments {"pip_id": <PIP_PROTO_PK>}
    # SEE: `.status` in [`submitted`, `processing_galdr`, `reviewed`]
    # IF DIFFER: MCP-09 PP-04


#############################################################################
# MCP-10 — GUI: Admin finalize both PIPs (browser step)
############################################################################

  @manual @uat @mcp-admin @browser
  Scenario: MCP-10 Admin accepts and finalizes PIP_MAIN + PIP_PROTO via Django admin
    # STEP admin-login
    # DO: browser GET <BASE_URL>/admin/ → authenticate as `admin`
    # SEE: Django admin dashboard
    #
    # STEP accept-pip-main
    # DO: GET <BASE_URL>/admin/methodology/processimprovementproposal/<PIP_MAIN_PK>/change/
    # DO: set each PipChange inline `admin_decision` to `Accept`; SAVE
    # SEE: page saves without error
    #
    # STEP accept-pip-proto
    # DO: GET <BASE_URL>/admin/methodology/processimprovementproposal/<PIP_PROTO_PK>/change/
    # DO: set each PipChange inline `admin_decision` to `Accept`; SAVE
    # SEE: page saves without error
    #
    # STEP mass-finalize
    # DO: GET <BASE_URL>/admin/methodology/processimprovementproposal/
    # DO: select rows for `<PIP_MAIN_PK>` and `<PIP_PROTO_PK>`; run action `Finalize reviewed PIPs (apply accepted changes + notify)`
    # SEE: success flash lines contain `Finalised PIP-<id>` for both PIPs
    # IF DIFFER: MCP-10 mass-finalize


#############################################################################
# MCP-11 — Post-finalize MCP inventory
############################################################################

  @manual @uat @mcp-final
  Scenario: MCP-11 Post-finalize inventory — playbook bumped + activities present + PIPs accepted
    # STEP FN-01 list_playbooks released — version bumped
    # DO: CallMcpTool server "user-mimir" toolName "list_playbooks" arguments {"status": "released"}
    # SEE: entry with `<MCP_PB_ID>` present; `.version` ≥ `2.0` (two PIPs applied)
    # IF DIFFER: MCP-11 FN-01
    #
    # STEP FN-02 get_playbook — confirm version
    # DO: CallMcpTool server "user-mimir" toolName "get_playbook" arguments {"playbook_id": <MCP_PB_ID>}
    # SEE: `.version` ≥ `2.0`; `.status` = `released`
    # IF DIFFER: MCP-11 FN-02
    #
    # STEP FN-03 list_activities — MCP Activity Three now exists (from PIP_MAIN ADD change)
    # DO: CallMcpTool server "user-mimir" toolName "list_activities" arguments {"workflow_id": <MCP_WF_ID>}
    # SEE: array contains activity with `.name` = `MCP Activity Three`
    # IF DIFFER: MCP-11 FN-03
    #
    # STEP FN-04 get_pip PIP_MAIN — accepted
    # DO: CallMcpTool server "user-mimir" toolName "get_pip" arguments {"pip_id": <PIP_MAIN_PK>}
    # SEE: `.status` = `accepted`
    # IF DIFFER: MCP-11 FN-04
    #
    # STEP FN-05 get_pip PIP_PROTO — accepted
    # DO: CallMcpTool server "user-mimir" toolName "get_pip" arguments {"pip_id": <PIP_PROTO_PK>}
    # SEE: `.status` = `accepted`
    # IF DIFFER: MCP-11 FN-05
