Feature: MCP Rules — CRUDLF and activity linking
  As an AI assistant using Mimir MCP
  I want to manage playbook rules and attach them to activities
  So that workflows export produces .mdc files next to workflows/

  Background:
    Given MCP user owns a draft playbook

  Scenario: MCP-RULE-01 create_rule increments draft version
    When create_rule is called with title and optional slug
    Then a rule row exists for the playbook
    And playbook patch version increments like other playbook-scoped entities

  Scenario: MCP-RULE-02 list_rules filters
    When list_rules is called with search or unlinked_only
    Then matching rules are returned with activity_count

  Scenario: MCP-RULE-03 get_activity includes rules
    When get_activity is called for an activity with linked rules
    Then the payload contains a rules array with id title slug always_apply

  Scenario: MCP-RULE-04 set_activity_rules replaces M2M
    When set_activity_rules is called with rule id list
    Then only rules from the same playbook may be linked
    And released playbooks reject mutations
