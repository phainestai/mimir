# Activity: Define Test Strategy

**Activity ID**: TBD
**Order**: 6
**Phase**: Design
**Dependencies**: Predecessor: DTA-04 (Define Code Organization)

## Description

Define Test Strategy

## Guidance

# Define Test Strategy

## Objective

Define the test pyramid, choose frameworks per layer, establish coverage targets, plan test data management, and configure CI integration for tests.

---

## Decisions to Make

### 1. Test Pyramid & Coverage Targets

Define ratio and targets per level:
- **Unit tests** — Isolated logic, services, utilities. Target: X% coverage.
- **Integration tests** — Views, DB queries, service interactions. Target: all CRUD paths.
- **E2E tests** — Full user journeys via browser/API. Target: critical paths only.
- **Contract tests** — API contract validation (if applicable).

Define what "100% pass rate" means (all tests must pass before declaring feature complete).

### 2. Frameworks per Layer

Choose frameworks for each test level:
- **Unit**: pytest, unittest, Jest, Vitest
- **Integration**: pytest + Django test client, supertest
- **E2E**: Playwright, Cypress, Selenium
- **Contract**: Pact, Schemathesis
- **Performance**: Locust, k6, Artillery

### 3. Test Data Management

- **Fixtures**: Static JSON/YAML fixtures loaded before tests
- **Factories**: Dynamic data generation (factory_boy, Faker)
- **DB seeding**: Management commands for consistent test state
- **Isolation**: How are tests isolated? Transaction rollback? Fresh DB?
- **Makefile targets**: `make test`, `make test-unit`, `make test-e2e`

### 4. CI Integration

- When do tests run? On every push? On PR? Nightly?
- Failure gates: Which test failures block merge/deploy?
- Test reporting: Where are results published?
- Flaky test policy: How are flaky tests handled?

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `TEST_UNIT`
- `TEST_INTEGRATION`
- `TEST_E2E`

Report coverage and gaps.

---

## Deliverables

- ✅ **Test pyramid** defined with coverage targets
- ✅ **Frameworks** chosen per test level
- ✅ **Test data management** approach defined
- ✅ **CI integration** rules established
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Test strategy decision (section for SAO.md)

## Artifacts Consumed

- Code organization decision from DTA-04
- Structured requirements list from DTA-01

## Notes

No additional notes.
