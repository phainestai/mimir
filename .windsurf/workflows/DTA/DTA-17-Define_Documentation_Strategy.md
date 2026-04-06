# Activity: Define Documentation Strategy

**Activity ID**: TBD
**Order**: 17
**Phase**: Support
**Dependencies**: Predecessor: DTA-04 (Define Code Organization)

## Description

Define Documentation Strategy

## Guidance

# Define Documentation Strategy

## Objective

Define Architecture Decision Record (ADR) process, API documentation approach, living documentation standards, runbook format, and knowledge base structure.

---

## Decisions to Make

### 1. Architecture Decision Records (ADRs)

- **Template**: Standard ADR format (Title, Status, Context, Decision, Consequences)
- **Storage location**: `docs/architecture/decisions/` or `docs/adr/`
- **Numbering**: Sequential (ADR-001, ADR-002, ...)
- **Review process**: PR-based? Team discussion? Informal?
- **When to write**: Any significant architecture or technology choice

### 2. API Documentation

- **Approach**: OpenAPI/Swagger spec generation
- **Generation**: Contract-first (write spec, generate code) or code-first (generate spec from code)
- **Publishing**: Auto-published on build? Swagger UI endpoint?
- **MCP tool documentation**: How are MCP tools documented?
- **Versioning**: Spec versioned with API version

### 3. Living Documentation

- **Code comments policy**: When to comment (non-obvious logic), when NOT to comment (obvious code)
- **Docstring standards**: Sphinx format with `:param:`, `:return:`, `:raises:` and examples
- **Type hints**: Required on all public methods and functions
- **README hierarchy**: Root README → app-level READMEs → module docs

### 4. Runbook Standards

- **Format**: Markdown with structured sections (Trigger, Impact, Steps, Verification)
- **Storage**: `docs/runbooks/` or alongside infrastructure code
- **Update cadence**: After every incident that reveals a gap
- **Review**: Quarterly runbook review for staleness

### 5. Knowledge Base

- **Wiki**: GitHub Wiki, Confluence, Notion, or docs/ in repo
- **Onboarding guides**: For new developers, new operators
- **FAQ**: Common questions and troubleshooting
- **Search**: How is documentation discoverable?

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `DOCS_ADR`
- `DOCS_API`
- `DOCS_RUNBOOK`

Report coverage and gaps.

---

## Deliverables

- ✅ **ADR process** established with template and storage location
- ✅ **API documentation** approach chosen
- ✅ **Living documentation** standards defined (comments, docstrings, type hints)
- ✅ **Runbook standards** set
- ✅ **Knowledge base** structure defined
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Documentation strategy decision (section for SAO.md)

## Artifacts Consumed

- Code organization decision from DTA-04

## Notes

No additional notes.
