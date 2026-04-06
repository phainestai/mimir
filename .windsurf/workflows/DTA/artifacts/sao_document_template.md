# {Project Name}: System Architecture Overview

## Executive Summary
- System purpose (1-2 sentences)
- Key architectural decisions (bullet list of the most impactful choices)

## 1. Application Blocks
<!-- Decision from DTA-02 -->
### Bounded Contexts / Domain Packages
- List domain packages with responsibilities

### Module Dependency Rules
- Dependency direction diagram or rules

### Foundational Architectural Pattern
- **Chosen**: {pattern}
- **Rationale**: Why this pattern over alternatives

### UI Architecture Patterns (if applicable)
- **Rendering model**: {server-rendered | SPA | hybrid} — rationale
- **Layout pattern**: {single-panel | multi-panel | wizard} — rationale
- **Component interaction model**: {full reload | partial updates | client-side state} — rationale
- **Visualization approach**: {server-generated | client-rendered | hybrid} — rationale

## 2. Integration & API Design
<!-- Decision from DTA-03 -->
### API Style
- **Chosen**: {style}
- **Rationale**: Why this style

### Versioning Strategy
- **Chosen**: {strategy}

### Contract Approach
- **Chosen**: {approach}

### External Integrations
- List 3rd party APIs, webhook patterns, retry policies

### Inter-Service Communication
- **Chosen**: {model}
- **Rationale**: Why this model

### Implementation Patterns
<!-- Populated during/after implementation -->
- Service-to-transport mapping:
- Sync/async boundary:
- Protocol-specific constraints:
- Shared service layer:
- Error propagation:

## 3. Code Organization
<!-- Decision from DTA-04 -->

## 4. Data Architecture
<!-- Decision from DTA-05 -->

## 5. Test Strategy
<!-- Decision from DTA-06 -->

## 6. Performance & Scalability
<!-- Decision from DTA-07 -->

## 7. Error Handling & Resilience
<!-- Decision from DTA-08 -->

## 8. Infrastructure
<!-- Decision from DTA-09 -->

## 9. CI/CD Pipeline
<!-- Decision from DTA-10 -->

## 10. Release & Rollback
<!-- Decision from DTA-11 -->

## 11. Observability
<!-- Decision from DTA-12 -->

## 12. Config & Secrets
<!-- Decision from DTA-13 -->

## 13. Security
<!-- Decision from DTA-14 -->

## 14. Backup & Recovery
<!-- Decision from DTA-15 -->

## 15. Developer Experience
<!-- Decision from DTA-16 -->

## 16. Documentation Strategy
<!-- Decision from DTA-17 -->

## Technology Stack Table

Machine-readable table consumed by Bootstrap Project (BSP) for automated provisioning.

| Layer | Tool | Version | Install Command (macOS) | Install Command (Linux) | Verify Command |
|-------|------|---------|-------------------------|-------------------------|----------------|
| ...   | ...  | ...     | ...                     | ...                     | ...            |

> **Note**: Each row must have install + verify commands so BSP can automate provisioning.

## Skill Coverage Report

| Domain | Covered Skills | Gaps |
|--------|---------------|------|
| Application Blocks | | |
| Integration & API | | |
| Code Organization | | |
| Data Architecture | | |
| Test Strategy | | |
| Performance & Scalability | | |
| Error Handling & Resilience | | |
| Infrastructure | | |
| CI/CD Pipeline | | |
| Release & Rollback | | |
| Observability | | |
| Config & Secrets | | |
| Security | | |
| Backup & Recovery | | |
| Developer Experience | | |
| Documentation Strategy | | |

## Key Decisions with Rationale

| # | Domain | Decision | Rationale |
|---|--------|----------|-----------|
| 1 | | | |

## Discovered Patterns & Lessons Learned
<!-- Reserved section — populated during and after implementation -->

### Critical Discoveries

<!-- For each significant discovery during implementation: -->
<!--
#### Discovery: {title}
- **Context**: What was being built/integrated
- **Problem**: What didn't work as expected
- **Solution**: The pattern/workaround adopted
- **Key Lessons**:
  1. ...
-->

### Retrospective Updates

<!-- Track SAO sections updated post-implementation: -->
<!--
| Section | Original Decision | What Changed | Updated Decision |
|---------|-------------------|--------------|------------------|
| | | | |
-->
