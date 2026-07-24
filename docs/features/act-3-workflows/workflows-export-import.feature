Feature: FOB-WORKFLOWS-EXPORT_IMPORT-1 MCP Workflow Synchronization
  As a methodology author (Maria)
  I want to export workflows to my AI workspace and import edited versions back via MCP
  So that I can collaborate with my AI assistant to improve workflow activities

  Background:
    Given Maria is authenticated in FOB
    And she owns playbook "React Frontend Development v0.5" in Draft status
    And the playbook has workflow "Frontend Development" with 15 activities

  # EXPORT SCENARIOS

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-01 Export via MCP tool
    Given Maria's AI assistant has access to Mimir MCP server
    When AI calls mcp.export_workflow_to_local(workflow_id=42, target_directory=".windsurf/workflows", folder_name="FFE")
    Then the MCP facade receives file contents from the server
    And the facade writes files to the AI workspace at ".windsurf/workflows/FFE/"
    And returns success response with export path and file list
    And 16 files are created in ".windsurf/workflows/FFE/"
    And folder contains "_workflow.md" with workflow metadata
    And folder contains 15 activity files: FFE-01-*.md through FFE-15-*.md

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-01c Hosted server returns file contents, not a path
    Given Maria's AI assistant uses the HTTP MCP facade against a hosted FOB server
    When AI calls mcp.export_workflow_to_local(workflow_id=42, target_directory=".windsurf/workflows", folder_name="FFE")
    Then the server response contains a "workflow_files" array with "filename" and "content" pairs
    And the server response does not contain an "export_path" key
    And the facade computes the local export path under ".windsurf/workflows/FFE/"
    And the tool return value includes that local "export_path" and "files_created" list

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-01d Docker facade rejects export without bind mount
    Given the HTTP MCP facade runs inside a Docker container
    And MIMIR_DEV_ROOT is not configured or not bind-mounted
    When AI calls mcp.export_workflow_to_local(workflow_id=42, target_directory=".windsurf/workflows", folder_name="FFE")
    Then the tool returns an error explaining how to add "-e" MIMIR_DEV_ROOT and "-v" to MCP config
    And no success status is returned

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-01b Export writes rules to sibling rules folder
    Given activities in the workflow link playbook rules "pytest" and "ruff"
    When AI exports the workflow to ".windsurf/workflows/FFE/"
    Then distinct rule files appear under ".windsurf/rules/" as "*.mdc"
    And each file contains YAML front matter with alwaysApply

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-02 Activity file contains complete metadata
    Given workflow "Frontend Development" has been exported via MCP
    When Maria opens "FFE-01-Setup_Project.md"
    Then file contains activity metadata: ID, Order, Phase, Dependencies
    And file contains Description section
    And file contains Guidance section with numbered steps
    And file contains Artifacts Produced section
    And file contains Artifacts Consumed section
    And file contains Notes section

  # LOCAL EDITING SCENARIOS

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-03 AI assistant edits activity files
    Given workflow files are exported to ".windsurf/workflows/FFE/"
    When Maria asks AI: "Reorder activities 2 and 3, and add a new activity for API testing"
    Then AI renames "FFE-02-Configure_Build.md" to "FFE-03-Configure_Build.md"
    And AI renames "FFE-03-Install_Dependencies.md" to "FFE-02-Install_Dependencies.md"
    And AI creates "FFE-16-API_Integration_Testing.md"
    And AI updates "_workflow.md" to show 16 activities

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-04 User reviews changes in IDE
    Given AI has edited workflow files
    When Maria opens her IDE's source control view
    Then she sees diff for renamed files
    And she sees new file "FFE-16-API_Integration_Testing.md"
    And she sees updated "_workflow.md"
    And she can review all changes before importing

  # IMPORT SCENARIOS

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-05 Generate upload protocol via MCP
    Given Maria's AI assistant has edited workflow files
    When AI calls mcp.import_workflow_from_local(workflow_id=42, source_directory=".windsurf/workflows/FFE", auto_apply=False)
    Then the MCP server compares local files with FOB workflow
    And detects 4 changes: 1 new, 2 modified, 2 reordered
    And generates "_Upload_Protocol.md" in ".windsurf/workflows/FFE/"
    And returns change summary to AI

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-06 AI prepares upload protocol with rationales
    Given Maria's AI assistant has detected 4 changes
    When AI generates "_Upload_Protocol.md"
    Then AI includes change summary with counts
    And AI includes detailed change list with:
      | change_type | activity_name           | details                  |
      | NEW         | API Integration Testing | Order 16, Phase: Testing |
      | MODIFIED    | Setup Project           | Description updated      |
      | REORDERED   | Configure Build         | Order 3 (was 2)          |
      | REORDERED   | Install Dependencies    | Order 2 (was 3)          |
    And AI fills in rationale for each change explaining the improvement
    And AI includes approval options: Apply Immediately, Submit as PIP, Cancel

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-07 User reviews and approves protocol
    Given AI has prepared upload protocol with rationales
    When Maria opens "_Upload_Protocol.md"
    Then she reviews AI's rationales for each change
    And she can edit rationales if needed
    And she can accept or reject individual changes
    And she approves the protocol for import

  # APPLY CHANGES - DRAFT PLAYBOOK SCENARIOS

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-08 Apply changes to draft playbook via MCP
    Given playbook is in Draft status (v0.5)
    And upload protocol exists with rationales
    When AI calls mcp.apply_upload_protocol(protocol_file=".windsurf/workflows/FFE/_Upload_Protocol.md")
    Then MCP server applies changes to workflow
    And 1 new activity is created
    And 2 activities are modified
    And 2 activities are reordered
    And playbook version auto-increments to v0.6
    And returns success response with change counts

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-09 Verify changes applied
    Given changes have been applied via MCP
    When Maria views the workflow in FOB
    Then workflow has 16 activities (was 15)
    And activities are in new order
    And playbook version is v0.6
    And local files in ".windsurf/workflows/FFE/" remain for future edits

  # SUBMIT PIP - RELEASED PLAYBOOK SCENARIOS

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-10 Create PIP via MCP for released playbook
    Given playbook is in Released status (v1.0)
    And upload protocol exists with rationales
    When AI calls mcp.create_pip_from_protocol(protocol_file=".windsurf/workflows/FFE/_Upload_Protocol.md", pip_title="Improve workflow")
    Then MCP server creates PIP with protocol changes
    And PIP contains all changes with rationales
    And returns PIP ID and status
    And changes will be applied upon PIP approval

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-11 Verify PIP created
    Given PIP has been created from protocol
    When Maria views the PIP in FOB
    Then PIP status is "Pending Review"
    And PIP contains change protocol with 4 changes
    And local files in ".windsurf/workflows/FFE/" are preserved as PIP documentation
    And upon approval, playbook minor version increments by 1 (e.g., v1.0 → v1.1)
    And major version is unchanged (only the "Release" action bumps major)

  # ERROR AND EDGE CASE SCENARIOS

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-12 Detect conflicting changes
    Given workflow was modified in FOB after export
    When AI attempts to import local changes via MCP
    Then MCP server detects conflict
    And returns warning: "Workflow was modified in FOB since export"
    And includes conflict details in response

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-13 Validate activity dependencies
    Given local files have circular dependency (Activity A depends on B, B depends on A)
    When AI attempts to apply changes via MCP
    Then MCP server validation fails
    And returns error: "Circular dependency detected: Activity A ↔ Activity B"
    And changes are not applied

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-14 Missing artifact references
    Given local file references artifact_id that doesn't exist
    When AI imports workflow via MCP
    Then MCP server returns warning: "Activity references unknown artifact (ID: 999)"
    And provides options: Create artifact, Remove reference, or Cancel

  # INTEGRATION SCENARIOS

  ✅ Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-15 Export-edit-import full cycle for draft
    Given Maria has draft playbook "React Frontend Development v0.5"
    # Export
    When AI exports workflow "Frontend Development" to ".windsurf/workflows/FFE/"
    # Edit with AI
    And AI adds 1 new activity and reorders 2 activities
    # Import
    And AI imports changes back via MCP
    And Maria fills in rationales in protocol
    And AI applies protocol via MCP
    # Verify
    Then workflow has 16 activities (was 15)
    And activities are in new order
    And playbook version is v0.6
    And Maria can continue editing or export again

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-16 Export-edit-PIP full cycle for released
    Given Maria has released playbook "React Frontend Development v1.0"
    # Export
    When AI exports workflow "Frontend Development" via MCP
    # Edit with AI
    And AI improves 3 activity descriptions
    # Import as PIP
    And AI imports changes via MCP
    And Maria fills in detailed rationales
    And AI creates PIP from protocol via MCP
    # Verify
    Then PIP is created with status "Pending Review"
    And upon approval, playbook minor version increments by 1 (e.g., v1.0 → v1.1)
    And major version is unchanged (only the "Release" action bumps major)
    And workflow changes will be applied as a single aggregated minor bump

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-17 Multiple export-import iterations
    Given Maria has exported workflow once
    And applied changes (v0.5 → v0.6)
    When AI exports the same workflow again via MCP
    Then new export reflects v0.6 state with 16 activities
    And Maria can make additional edits
    And import again (v0.6 → v0.7)
    And this cycle can repeat indefinitely for draft playbooks

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-18 AI assistant suggests workflow improvements
    Given workflow is exported to AI workspace
    When Maria asks AI: "Review this workflow and suggest improvements"
    Then AI reads all activity files
    And AI analyzes: order, dependencies, descriptions, guidance
    And AI suggests: "Activity 5 should have dependency on Activity 3"
    And AI suggests: "Add error handling guidance to Activity 8"
    And AI suggests: "Split Activity 12 into two smaller activities"
    And Maria can accept suggestions and import changes via MCP

  # ============================================================================
  # MCP FULL PLAYBOOK EXPORT / IMPORT
  # Covers portability between Mimir instances — complements UI-level act-10.
  # JSON schema is defined in act-10-import-export/import-export.feature.
  # ============================================================================

  # PRIMARY USE CASE for MCP playbook export/import:
  # Two separate Mimir instances, no shared DB, no shared filesystem.
  # Cascade exports on Instance A → Maria copies the file → Cascade imports on Instance B.
  # The JSON file is the only transfer mechanism.

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-19 Cross-instance migration via MCP
    # Golden path: export on one instance, import on another.
    Given Cascade is connected to Mimir MCP on Instance A
    And playbook (id=4) "GDD Playbook" exists on Instance A
    When Cascade calls "export_playbook" with playbook_id=4 and output_path="./exports/gdd-playbook.json"
    And Maria copies "gdd-playbook.json" to Instance B
    And Cascade calls "import_playbook" with input_path="./exports/gdd-playbook.json" on Instance B
    Then the playbook exists on Instance B with all workflows, activities, and entity links intact
    And all entity IDs on Instance B differ from those on Instance A
    And the playbook has no dependency on Instance A's database state
    And the playbook status and version on Instance B match those from the exported JSON
    And the playbook source is "imported" on Instance B
    And the playbook is owned by the current MCP user on Instance B

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-20 Export full playbook to JSON file via MCP
    Given playbook (id=4) has 5 workflows, 23 activities, 2 agents, 3 skills, 4 rules, 3 phases, 4 artifacts
    When Cascade calls MCP tool "export_playbook" with:
      | playbook_id | 4                             |
      | output_path | ./exports/gdd-playbook.json   |
    Then MCP writes a valid JSON file to "./exports/gdd-playbook.json"
    And MCP returns success with:
      | field      | value                        |
      | path       | ./exports/gdd-playbook.json  |
      | workflows  | 5                            |
      | activities | 23                           |
      | agents     | 2                            |
      | skills     | 3                            |
      | rules      | 4                            |
      | phases     | 3                            |
      | artifacts  | 4                            |
    And the JSON conforms to the schema defined in act-10

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-21 Import full playbook from JSON file via MCP
    Given a valid "gdd-playbook.json" exists at "./exports/gdd-playbook.json"
    And no playbook with the name from that file exists on this instance
    When Cascade calls MCP tool "import_playbook" with:
      | input_path | ./exports/gdd-playbook.json |
    Then MCP creates a new playbook from the JSON
    And MCP returns success with:
      | field       | value                   |
      | playbook_id | (new integer ID)        |
      | name        | (name from JSON)        |
      | status      | (preserved from JSON)   |
      | version     | (preserved from JSON)   |
      | source      | imported                |
    And the new playbook contains all entities from the source file
    And the playbook author is the current MCP user

  # ============================================================================
  # NAME COLLISION STRATEGIES
  # import_playbook accepts an optional conflict_strategy parameter.
  # Matching is always by name: workflow by name, activity by (workflow_name, activity_name),
  # agent/skill/phase/rule/artifact each by their own name or slug.
  # Default (no parameter): raise an error if a playbook with the same name exists.
  # conflict_strategy=replace: delete existing playbook and all its content, import fresh.
  # conflict_strategy=add_missing: add absent entities to the existing playbook, skip existing.
  #   If no playbook with that name exists, add_missing behaves identically to the default
  #   happy path — the playbook is created fresh with no conflict to resolve.
  # Note: add_missing is available in both MCP (conflict_strategy parameter) and UI
  #   ([Add Missing] button in the conflict dialog) — behaviour is identical.
  # ============================================================================

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-22 Import name collision with no strategy raises error
    Given Instance B already has a playbook named "GDD Playbook"
    When Cascade calls "import_playbook" with:
      | input_path | ./exports/gdd-playbook.json |
    Then MCP returns error:
      "ConflictError: Playbook 'GDD Playbook' already exists.
       Use conflict_strategy='replace' to overwrite or 'add_missing' to add only new entities."
    And the existing playbook is unchanged
    And no new playbook is created

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-23 conflict_strategy=replace drops existing and imports fresh
    Given Instance B already has playbook "GDD Playbook" with 10 activities
    When Cascade calls "import_playbook" with:
      | input_path        | ./exports/gdd-playbook.json |
      | conflict_strategy | replace                     |
    Then the existing "GDD Playbook" and all its content are permanently deleted
    And a new playbook "GDD Playbook" is created from the JSON
    And the new playbook has status and version preserved from the JSON, and source "imported"
    And the new playbook contains exactly the entities from the JSON file
    And the deletion and creation are a single atomic operation: if the import fails, the original playbook is preserved

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-24 conflict_strategy=add_missing adds only absent entities
    Given Instance B already has playbook "GDD Playbook" containing:
      | entity type | name               | present |
      | workflow    | VIS — Vision       | yes     |
      | workflow    | DYN — Dynamics     | no      |
      | activity    | Define aesthetic   | yes     |
      | activity    | Write elevator pitch | no    |
    When Cascade calls "import_playbook" with:
      | input_path        | ./exports/gdd-playbook.json |
      | conflict_strategy | add_missing                 |
    Then workflow "VIS — Vision" is not modified (already present by name)
    And activity "Define aesthetic" is not modified (already present by name)
    And workflow "DYN — Dynamics" is created (was absent)
    And activity "Write elevator pitch" is created (was absent)
    And no existing entity is deleted or overwritten
    And if the operation fails, no new entities are added and the existing playbook is unchanged

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-25 MCP round-trip preserves full structure
    Given Cascade exports playbook (id=4) to "./exports/export-v1.json"
    When Cascade imports "./exports/export-v1.json" with conflict_strategy="replace"
    And Cascade exports the newly imported playbook to "./exports/export-v2.json"
    Then "export-v1.json" and "export-v2.json" are structurally identical
    Except for the "exported_at" timestamp

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-26 Export non-existent playbook raises error
    When Cascade calls "export_playbook" with:
      | playbook_id | 999                      |
      | output_path | ./exports/missing.json   |
    Then MCP returns error "ValueError: Playbook 999 not found"
    And no file is written

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-27 Import from non-existent file raises error
    When Cascade calls "import_playbook" with:
      | input_path | ./exports/nonexistent.json |
    Then MCP returns error "ValueError: File not found: ./exports/nonexistent.json"

  Scenario: FOB-WORKFLOWS-EXPORT_IMPORT-28 Import JSON with broken predecessor reference raises error
    Given a JSON file where activity "Create Mockup" has predecessor_ref "activity-99"
    But no activity with ref "activity-99" exists in the file
    When Cascade calls "import_playbook" with that file
    Then MCP returns error "ValueError: Activity 'Create Mockup' references unknown predecessor 'activity-99'"
    And no playbook is created
    And no partial entities remain in the database
