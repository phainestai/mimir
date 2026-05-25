Feature: FOB-MCP-SKILLS-1 AI Assistant Interacts with Skills via MCP
  As an AI assistant (Cascade)
  I want to create, read, update, delete, link and unlink skills via MCP tools
  So that I can help users define reusable technical guidance within playbooks

  Status: ✅ DONE - CRUD + link/unlink operations implemented
  Branch: feature/skill-capability-metadata
  Related: act-8-skills

  Background:
    Given MCP server is running with command "python manage.py mcp_server --user=maria"
    And user context is set for "maria"
    And Cascade is connected via stdio protocol

  # ============================================================================
  # CREATE SKILL
  # ============================================================================

  Scenario: MCP-SK-01 Create skill in draft playbook
    Given draft playbook "React Frontend v1.2" exists for user "maria"
    When Cascade calls MCP tool "create_skill" with:
      | playbook_id       | 1                  |
      | title             | Build Login Form   |
      | content           | ## Steps\n1. ...  |
      | capability_domain | GUI_FORM           |
      | technology_stack  | React+Redux        |
    Then MCP returns success response with:
      | id                | 1                |
      | title             | Build Login Form |
      | capability_domain | GUI_FORM         |
      | technology_stack  | React+Redux      |
    And parent playbook version is incremented

  Scenario: MCP-SK-02 Create skill with empty title raises error
    Given draft playbook "React Frontend v1.2" exists for user "maria"
    When Cascade calls MCP tool "create_skill" with:
      | playbook_id | 1 |
      | title       |   |
    Then MCP returns error "ValueError: Skill title cannot be empty"

  Scenario: MCP-SK-03 Create skill in released playbook raises error
    Given released playbook "Production Guide" exists for user "maria"
    When Cascade calls MCP tool "create_skill" with:
      | playbook_id | 2                |
      | title       | Build Login Form |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # LIST SKILLS
  # ============================================================================

  Scenario: MCP-SK-04 List skills for playbook
    Given draft playbook with 3 skills exists for user "maria"
    When Cascade calls MCP tool "list_skills" with:
      | playbook_id | 1 |
    Then MCP returns list of 3 skills with title, capability_domain, technology_stack, activity_count

  Scenario: MCP-SK-05 List skills filtered by capability domain
    Given draft playbook with skills in domains "GUI_FORM" and "API_CRUD"
    When Cascade calls MCP tool "list_skills" with:
      | playbook_id | 1        |
      | domain      | GUI_FORM |
    Then MCP returns only skills with capability_domain "GUI_FORM"

  Scenario: MCP-SK-06 List skills filtered by technology stack
    Given draft playbook with skills using stacks "React+Redux" and "Django+HTMX"
    When Cascade calls MCP tool "list_skills" with:
      | playbook_id | 1           |
      | stack       | React+Redux |
    Then MCP returns only skills with technology_stack "React+Redux"

  Scenario: MCP-SK-07 List skills with search query
    Given draft playbook with skills "Build Login Form" and "API Authentication"
    When Cascade calls MCP tool "list_skills" with:
      | playbook_id | 1     |
      | search      | Login |
    Then MCP returns only skills matching "Login" in title or content

  # ============================================================================
  # GET SKILL
  # ============================================================================

  Scenario: MCP-SK-08 Get skill details with activity count
    Given draft playbook with skill "Build Login Form" linked to 2 activities
    When Cascade calls MCP tool "get_skill" with:
      | skill_id | 1 |
    Then MCP returns skill details including:
      | title             | Build Login Form |
      | capability_domain | GUI_FORM         |
      | technology_stack  | React+Redux      |
      | activity_count    | 2                |

  # ============================================================================
  # UPDATE SKILL
  # ============================================================================

  Scenario: MCP-SK-09 Update skill title and metadata
    Given draft playbook with skill "Build Login Form" for user "maria"
    When Cascade calls MCP tool "update_skill" with:
      | skill_id          | 1                    |
      | title             | Build Auth Form      |
      | capability_domain | GUI_AUTH             |
      | technology_stack  | React+Redux+Formik   |
    Then MCP returns updated skill with new values
    And parent playbook version is incremented

  Scenario: MCP-SK-10 Update skill in released playbook raises error
    Given released playbook with skill "Build Login Form" for user "maria"
    When Cascade calls MCP tool "update_skill" with:
      | skill_id | 1               |
      | title    | Build Auth Form |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # DELETE SKILL
  # ============================================================================

  Scenario: MCP-SK-11 Delete skill clears activity FKs
    Given draft playbook with skill "Build Login Form" linked to 2 activities
    When Cascade calls MCP tool "delete_skill" with:
      | skill_id | 1 |
    Then MCP returns success with deleted=True
    And parent playbook version is incremented
    And the 2 activities have no skills linked

  Scenario: MCP-SK-12 Delete skill in released playbook raises error
    Given released playbook with skill "Build Login Form" for user "maria"
    When Cascade calls MCP tool "delete_skill" with:
      | skill_id | 1 |
    Then MCP returns error "PermissionError: Cannot modify released playbook"

  # ============================================================================
  # LINK / UNLINK
  # ============================================================================

  Scenario: MCP-SK-13 Link skill to activity in same playbook
    Given draft playbook with skill "Build Login Form" and activity "Implement Login"
    When Cascade calls MCP tool "link_skill_to_activity" with:
      | activity_id | 1 |
      | skill_id    | 1 |
    Then MCP returns success with activity_id and skill_id in skill_ids

  Scenario: MCP-SK-14 Link skill to activity in different playbook raises error
    Given draft playbook A with skill "Build Login Form"
    And draft playbook B with activity "Implement Login"
    When Cascade calls MCP tool "link_skill_to_activity" with:
      | activity_id | 2 |
      | skill_id    | 1 |
    Then MCP returns error "ValueError: must be in the same playbook"

  Scenario: MCP-SK-15 Unlink specific skill from activity
    Given draft playbook with activity linked to skills "Build Login Form" and "Deploy to AWS"
    When Cascade calls MCP tool "unlink_skill_from_activity" with:
      | activity_id | 1 |
      | skill_id    | 1 |
    Then MCP returns success and skill_id 1 is removed from skill_ids
    And activity still has skill "Deploy to AWS" in skill_ids

  Scenario: MCP-SK-16 set_activity_skills replaces full skill set
    Given draft playbook with activity linked to skill "Build Login Form"
    And playbook has skill "Deploy to AWS"
    When Cascade calls MCP tool "set_activity_skills" with:
      | activity_id | 1 |
      | skill_ids   | [2] |
    Then MCP returns skill_ids [2]
    When Cascade calls MCP tool "set_activity_skills" with:
      | activity_id | 1 |
      | skill_ids   | [] |
    Then MCP returns skill_ids []
