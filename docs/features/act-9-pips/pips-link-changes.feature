Feature: FOB-PIP-LINK-1 Propose relationship changes via LINK / UNLINK PIP changes
  As a methodology author
  I want to propose Skill→Activity, Rule→Activity, Agent→Activity, and Activity→Workflow links
  So that relationship changes on Released playbooks are reviewable like ADD / ALTER / DROP

  Status: ✅ Implemented (feature/pip-link-changes)
  Related: act-9-pips/pips-create.feature, act-9-pips/pips-admin-review.feature

  Background:
    Given Maria is authenticated in FOB
    And playbook "React Frontend Dev" is Released at version 1.0
    And the playbook contains Activity "Create Components", Skill "React Component Guide", and Workflow "Testing"

  @FOB-PIP-LINK-01
  Scenario: Add a LINK change — Skill → Activity
    When Maria adds a PIP change type LINK relationship skill_activity
    And source is Skill "React Component Guide"
    And target is Activity "Create Components"
    Then the change appears in the PIP draft with relationship_type skill_activity

  @FOB-PIP-LINK-02
  Scenario: Add a LINK change — Activity cross-listed in additional Workflow
    When Maria adds a PIP change type LINK relationship activity_workflow
    And source is Activity "Create Components"
    And target is Workflow "Testing"
    Then the change is stored for secondary workflow membership

  @FOB-PIP-LINK-03
  Scenario: Add an UNLINK change — remove Skill from Activity
    Given Skill "React Component Guide" is linked to Activity "Create Components"
    When Maria adds a PIP change type UNLINK relationship skill_activity for that pair
    Then the UNLINK change is accepted into the draft

  @FOB-PIP-LINK-04
  Scenario: LINK referencing not-yet-existing entity via internal_ref
    When Maria adds ADD Skill "CDK Deployment" with internal_ref "#cdk-skill"
    And Maria adds LINK skill_activity source "#cdk-skill" target Activity "Create Components"
    Then both changes are ordered in the same PIP draft

  @FOB-PIP-LINK-05
  Scenario: LINK validation — source and target must be in same playbook
    When Maria attempts LINK skill_activity with entities from different playbooks
    Then FOB rejects the change with a playbook mismatch error

  @FOB-PIP-LINK-06
  Scenario: LINK validation — duplicate relationship rejected
    Given Skill is already linked to Activity
    When Maria attempts another LINK for the same pair
    Then FOB rejects with "Relationship already exists"

  @FOB-PIP-LINK-07
  Scenario: UNLINK validation — relationship must exist
    Given Skill is not linked to Activity
    When Maria attempts UNLINK skill_activity for that pair
    Then FOB rejects with "Relationship does not exist"

  @FOB-PIP-LINK-08
  Scenario: Preview diff shows Links Added / Links Removed
    Given the PIP contains LINK and UNLINK changes
    When Maria opens Preview diff
    Then sections "Links Added" and "Links Removed" are visible

  @FOB-PIP-LINK-09
  Scenario: Galdr evaluates LINK changes per-change
    Given a submitted PIP with a LINK change
    When Galdr completes review
    Then the LINK change has recommendation ACCEPT, REJECT, or NEEDS_CLARIFICATION with reasoning

  @FOB-PIP-LINK-10
  Scenario: Admin finalizes accepted LINK skill_activity
    Given Admin accepted LINK skill_activity
    When Admin finalizes the PIP
    Then Activity.skills M2M includes the Skill

  @FOB-PIP-LINK-11
  Scenario: Admin finalizes accepted LINK activity_workflow
    Given Admin accepted LINK activity_workflow
    When Admin finalizes the PIP
    Then an ActivityWorkflowMembership row exists for the secondary workflow

  @FOB-PIP-LINK-12
  Scenario: Admin finalizes accepted UNLINK skill_activity
    Given Admin accepted UNLINK skill_activity
    When Admin finalizes the PIP
    Then the Skill is removed from Activity.skills

  @FOB-PIP-LINK-13
  Scenario: Finalize resolves internal_ref — ADD Skill then LINK it
    Given PIP order is ADD Skill "#cdk-skill" then LINK to Activity
    When Admin accepts both and finalizes
    Then the new Skill exists and is linked to the Activity

  @FOB-PIP-LINK-14
  Scenario: Rejected LINK with accepted ADD does not create orphan link
    Given ADD Skill and LINK changes in one PIP
    When Admin accepts ADD but rejects LINK
    Then the Skill exists but is not linked to the Activity

  @FOB-PIP-LINK-15
  Scenario: Mixed ADD + LINK produces exactly one major version bump
    Given Admin accepts ADD and LINK changes together
    When Admin finalizes the PIP
    Then playbook version increments one major line only (e.g. 1.0 → 2.0)
