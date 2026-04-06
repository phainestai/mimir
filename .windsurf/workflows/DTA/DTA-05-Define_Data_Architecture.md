# Activity: Define Data Architecture

**Activity ID**: TBD
**Order**: 5
**Phase**: Design
**Dependencies**: Predecessor: DTA-02 (Define Application Blocks)

## Description

Define Data Architecture

## Guidance

# Define Data Architecture

## Objective

Choose database engine, define schema strategy, select data access patterns, and plan migration and caching approaches.

---

## Decisions to Make

### 1. Database Engine

Choose one (or combination):
- **SQLite** — File-based, zero config. Best for: desktop apps, prototypes, single-user.
- **PostgreSQL** — Full-featured relational. Best for: production web apps, complex queries.
- **MySQL/MariaDB** — Relational, widely supported. Best for: standard web apps.
- **Neo4j** — Graph database. Best for: relationship-heavy data, graph traversals.
- **MongoDB** — Document store. Best for: flexible schemas, rapid prototyping.
- **Combination** — e.g., SQLite for FOB + Neo4j for HOMEBASE.

Document rationale: performance needs, data model fit, team expertise, licensing.

### 2. Schema Strategy

- **Migration tool**: Django migrations, Alembic, Flyway, manual SQL
- **Versioning**: How are schema changes tracked? Numbered migrations? Timestamps?
- **Seed data**: How is initial/test data loaded? Fixtures, factories, management commands?
- **Schema evolution**: How are breaking changes handled? Expand-contract pattern?

### 3. Data Access Patterns

Choose one:
- **ORM** — Object-Relational Mapping (Django ORM, SQLAlchemy). Best for: standard CRUD.
- **Repository Pattern** — Abstract interface over storage. Best for: storage-agnostic design, testability.
- **Raw Queries** — Direct SQL/Cypher. Best for: complex queries, performance-critical paths.
- **Hybrid** — ORM for simple CRUD + raw queries for complex operations.

### 4. Read/Write Separation & Caching

- Is read/write separation needed? (CQRS pattern)
- Cache strategy: application-level cache, query cache, HTTP cache
- Cache invalidation approach
- Connection pooling configuration

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `DB_RELATIONAL`
- `DB_GRAPH`
- `DATA_ACCESS`

Report coverage and gaps.

---

## Deliverables

- ✅ **Database engine** chosen with rationale
- ✅ **Schema strategy** defined (migrations, versioning, seed data)
- ✅ **Data access pattern** selected
- ✅ **Caching strategy** defined (if applicable)
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Data architecture decision → contributes to `artifacts/sao_document_template.md` § "4. Data Architecture"

## Artifacts Consumed

- Structured requirements list from DTA-01
- Application blocks decision from DTA-02

## Notes

No additional notes.
