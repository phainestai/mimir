Feature: FOB-PIP-ACCEPT-1 Accept PIP — owner or Administrator
  As a playbook owner or Administrator
  I want to review Galdr's per-Change recommendations and make Accept/Reject decisions
  So that only well-reasoned changes are applied to Released playbooks

  # TARGET: After Galdr review, playbook OWNER or ADMINISTRATOR may finalize (accept/reject).
  # Public viewers and other authenticated users cannot finalize PIPs.
  #
  # MVP simplified implementation:
  # - Staff Administrator finalizes via Django Admin (implemented path).
  # - Playbook owner finalizes via FOB web UI (@mvp_gap — first post-MVP feature).
  # - Public viewers: can view the playbook and its PIPs but cannot finalize.

  Status: 🔲 TODO (Admin path); owner path @mvp_gap
  Related: act-9-pips/pips-view.feature, act-9-pips/pips-list.feature

  Background:
    Given user "mike" has the "Administrator" role with PIP Accept/Reject permission
    And Mike is logged into Django Admin at "/admin/"
    And PIP-42 exists with status "Reviewed" and the following Changes:
      | # | type  | entity_type | name / target             | galdr_recommendation | galdr_reasoning                                                                    |
      | 1 | ADD   | Activity    | Accessibility Audit       | ACCEPT               | Consistent with Testing phase goal; no upstream conflicts detected.               |
      | 2 | ALTER | Activity    | Component Testing (id=22) | REJECT               | Proposed content removes Artifact link to "Test Suite", breaking dependencies.    |
    And PIP-35 exists with status "Reviewed" and 1 Change:
      | # | type | entity_type | name / target               | galdr_recommendation | galdr_reasoning                                              |
      | 1 | DROP | Activity    | Write Documentation (id=23) | ACCEPT               | Documentation auto-generated from code; activity redundant. |

  # ============================================================================
  # NAVIGATION
  # ============================================================================

  Scenario: FOB-PIP-ADMIN-01 PIPs changelist appears in Django Admin sidebar
    Given Mike is in Django Admin
    Then he sees "Playbook Improvement Proposals" under the "Methodology" section in the sidebar
    When he clicks it
    Then he sees the PIP changelist at "/admin/methodology/pip/"

  Scenario: FOB-PIP-ADMIN-02 PIP changelist shows Reviewed PIPs by default
    Given Mike opens "/admin/methodology/pip/"
    Then he sees PIP-42 and PIP-35 in the list (both Reviewed)
    And the list columns are: PIP ID, Title, Target Playbook, Submitted By, Changes, Status, Submitted At
    And the default filter shows "Status: Reviewed"

  Scenario: FOB-PIP-ADMIN-03 Admin can filter by any status
    Given Mike is on the PIP changelist
    When he changes the filter to "Status: All"
    Then he sees PIPs in all statuses (Draft, Submitted, Processing, Reviewed, Accepted, Rejected)

  # ============================================================================
  # REVIEW INTERFACE — OPENING A PIP
  # ============================================================================

  Scenario: FOB-PIP-ADMIN-04 Open a Reviewed PIP shows admin review form
    Given Mike is on the PIP changelist
    When he clicks PIP-42 "Add Accessibility Audit"
    Then he navigates to "/admin/methodology/pip/42/change/"
    And he sees the PIP header:
      | field        | value                         |
      | PIP ID       | PIP-42                        |
      | Title        | Add Accessibility Audit       |
      | Target       | React Frontend Dev v1.0 (id=1)|
      | Submitted by | Maria Rodriguez               |
      | Status       | Reviewed                      |
    And he sees the Change inline table with 2 rows

  Scenario: FOB-PIP-ADMIN-05 Change inline shows Galdr recommendation and editable Admin decision
    Given Mike is viewing PIP-42 in Django Admin
    Then the Change inline shows:
      | # | type  | entity / target             | galdr_verdict | galdr_reasoning (truncated)               | admin_decision (dropdown) |
      | 1 | ADD   | Activity: Accessibility Audit | ACCEPT (green)| Consistent with Testing phase goal…       | — (unset)                 |
      | 2 | ALTER | Activity: Component Testing  | REJECT (red)  | Proposed content removes Artifact link… | — (unset)                 |
    And each admin_decision dropdown shows: "— (unset)", "ACCEPT", "REJECT"
    And the Save button is initially disabled until all admin_decision fields are set

  Scenario: FOB-PIP-ADMIN-06 Galdr reasoning expandable inline
    Given Mike is viewing PIP-42 Change #2 in Django Admin
    When he clicks [Read full reasoning] on Change #2
    Then the full Galdr reasoning is shown:
      """
      Proposed content removes the required Artifact link to "Test Suite",
      breaking the artifact dependency chain for Workflow "Testing & Documentation".
      Recommend rejecting until the author re-links the artifact in the change content.
      """

  # ============================================================================
  # MAKING DECISIONS
  # ============================================================================

  Scenario: FOB-PIP-ADMIN-07 Admin accepts all Changes — playbook version bumped
    Given Mike is reviewing PIP-42 in Django Admin
    When he sets admin_decision for Change #1 to "ACCEPT"
    And he sets admin_decision for Change #2 to "ACCEPT"
    And he clicks [Finalize Decision]
    Then a confirmation modal appears:
      """
      You are accepting 2 of 2 changes.
      React Frontend Dev will be updated to v2.0.
      This action cannot be undone.
      """
    When Mike clicks [Confirm]
    Then PIP-42 status becomes "Accepted"
    And the two Changes are applied to playbook id=1
    And playbook id=1 version increments from "1.0" to "2.0"
    And Maria receives an Accepted email

  Scenario: FOB-PIP-ADMIN-08 Admin accepts Change #1 and rejects Change #2
    Given Mike is reviewing PIP-42 in Django Admin
    When he sets admin_decision for Change #1 to "ACCEPT"
    And he sets admin_decision for Change #2 to "REJECT"
    And he clicks [Finalize Decision]
    Then confirmation modal shows:
      """
      You are accepting 1 of 2 changes and rejecting 1.
      React Frontend Dev will be updated to v2.0.
      This action cannot be undone.
      """
    When Mike confirms
    Then PIP-42 status becomes "Accepted" (partial)
    And only Change #1 (ADD Activity "Accessibility Audit") is applied
    And Change #2 is not applied
    And playbook id=1 version increments from "1.0" to "2.0"
    And Maria receives a Partially Accepted email

  Scenario: FOB-PIP-ADMIN-09 Admin rejects all Changes — playbook unchanged
    Given Mike is reviewing PIP-42
    When he sets admin_decision for both Changes to "REJECT"
    And he clicks [Finalize Decision]
    Then confirmation modal shows "Rejecting all 2 changes. No changes will be applied. This action cannot be undone."
    When Mike confirms
    Then PIP-42 status becomes "Rejected"
    And playbook id=1 is NOT modified
    And playbook id=1 version stays "1.0"
    And Maria receives a Rejected email

  Scenario: FOB-PIP-ADMIN-10 Finalize Decision disabled until all admin_decisions are set
    Given Mike is reviewing PIP-42 with 2 Changes
    And admin_decision for Change #1 is "ACCEPT"
    And admin_decision for Change #2 is "— (unset)"
    Then the [Finalize Decision] button is disabled
    When Mike sets Change #2 to "REJECT"
    Then the [Finalize Decision] button becomes enabled

  # ============================================================================
  # APPLY CHANGES — DATA INTEGRITY
  # ============================================================================

  Scenario: FOB-PIP-ADMIN-11 ADD Activity Change creates new Activity at correct position
    Given PIP with 1 ADD Change: Activity "Accessibility Audit" after Activity id=22
    And playbook Activities order in workflow 11 is: [22: Component Testing, 23: Write Documentation]
    When Admin accepts the ADD Change and finalises
    Then new Activity "Accessibility Audit" is created in workflow 11
    And order is: [22: Component Testing, NEW: Accessibility Audit, 23: Write Documentation]

  Scenario: FOB-PIP-ADMIN-12 ADD Activity Change with Append creates Activity at end
    Given PIP with 1 ADD Change: Activity "Post-launch Review" with position "Append at end of workflow 11"
    And workflow 11 Activities order is: [22, 23]
    When Admin accepts the ADD Change and finalises
    Then "Post-launch Review" is appended at order position 3 in workflow 11

  Scenario: FOB-PIP-ADMIN-13 ALTER Activity Change updates guidance content
    Given PIP with 1 ALTER Change: Activity Component Testing (id=22), new content "Add axe-core..."
    When Admin accepts the ALTER Change and finalises
    Then Activity id=22 guidance is replaced with "Add axe-core..."
    And Activity id=22 last_modified is updated

  Scenario: FOB-PIP-ADMIN-14 DROP Activity Change removes Activity and reassigns orphan order
    Given PIP with 1 DROP Change: Activity Write Documentation (id=23)
    And workflow 11 Activities order is: [22: Component Testing (order=1), 23: Write Documentation (order=2)]
    When Admin accepts the DROP Change and finalises
    Then Activity id=23 is deleted
    And workflow 11 Activities order is: [22: Component Testing (order=1)]

  Scenario: FOB-PIP-ADMIN-15 Version bump is exactly one minor increment regardless of Change count
    Given playbook id=1 is at version "1.0"
    And PIP has 3 accepted Changes
    When Admin finalises the PIP with all 3 Changes accepted
    Then playbook id=1 version is "2.0" (one major increment since all changes applied to v1.x → v2.0)
    And version history shows exactly one new entry "v2.0" with description aggregating all 3 changes
    And the v2.0 history entry links back to PIP-42

  # ============================================================================
  # PERMISSION CHECKS
  # ============================================================================

  Scenario: FOB-PIP-ADMIN-16 Regular user cannot access PIP Admin page
    Given user "maria" does not have Administrator role
    When Maria tries to access "/admin/methodology/pip/42/change/"
    Then she receives HTTP 403 or is redirected to Django Admin login

  # MVP simplified: owner finalizes PIPs via FOB UI is the first post-MVP item.
  # For MVP, owner submits the PIP and staff Administrator finalizes via Django Admin.
  @mvp_gap
  Scenario: FOB-PIP-OWNER-01 Playbook owner finalizes PIP on own Released playbook in FOB
    # MVP gap: owner finalize UI in FOB not yet built. Finalize goes through Django Admin (Administrator).
    Given Maria owns Released playbook "UX Research Methodology"
    And PIP-50 targets that playbook with status "Reviewed"
    And Galdr has completed recommendations on all Changes
    When Maria opens FOB-PIP-DETAIL-1 for PIP-50
    Then she sees [Finalize decision] or equivalent owner accept controls
    When she accepts Change #1 and rejects Change #2 and confirms finalize
    Then PIP-50 moves to Accepted or Accepted (partial)
    And the playbook version bumps per versioning rules

  # MVP simplified: public viewers can see the playbook but cannot finalize its PIPs.
  Scenario: FOB-PIP-OWNER-02 Public viewer cannot finalize someone else's PIP
    Given Mike owns a Public playbook "React Frontend Development"
    And Maria is authenticated in FOB but is not the owner
    And PIP-99 on that playbook has status "Reviewed"
    When Maria opens the PIP detail page for PIP-99
    Then she can read the PIP details (title, Changes, Galdr recommendations)
    And she does not see [Finalize decision] or [Accept] / [Reject] controls
    And a POST to finalize PIP-99 returns HTTP 403

  Scenario: FOB-PIP-ADMIN-17 Admin cannot modify an already-decided PIP
    Given PIP-35 has status "Accepted" (already finalised)
    When Mike opens PIP-35 in Django Admin
    Then all admin_decision fields are read-only
    And the [Finalize Decision] button is not shown
    And a banner shows "This PIP has already been decided and cannot be modified."

  Scenario: FOB-PIP-ADMIN-18 Finalize accepted LINK skill_activity updates Activity.skills
    Given PIP-60 has status "Reviewed" with LINK skill_activity Change #1 (Galdr ACCEPT)
    When Mike accepts Change #1 and finalizes PIP-60
    Then the target Activity's skills M2M includes the linked Skill
    And playbook version bumps one major line

  Scenario: FOB-PIP-ADMIN-19 Finalize accepted LINK activity_workflow creates membership
    Given PIP-61 has status "Reviewed" with LINK activity_workflow Change #1 (Galdr ACCEPT)
    When Mike accepts Change #1 and finalizes PIP-61
    Then ActivityWorkflowMembership exists for the activity and secondary workflow
