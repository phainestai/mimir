# Activity: Implement Journey Certification Tests

**Activity ID**: 100
**Order**: 5
**Phase**: Construction
**Dependencies**: None

## Description

Implement Journey Certification Tests

## Guidance

## Purpose
Browser-based validation of complete user journeys across multiple features using Playwright. This is Tier 2 Testing: certify that complete user experiences work end-to-end with real browser, HTMX, and JavaScript.

## When to Use
For critical user journeys spanning multiple features. Run on PR merge / nightly / pre-release.

## Steps

### 1. Identify Critical User Journeys

**Ask:** What are the most important paths users take through the application?

**Criteria for journey tests:**
- Spans multiple features (cross-cutting)
- Represents common user workflow
- Involves HTMX interactions
- Has visual/UI components
- Critical to business value

**Limit:** 5-10 total journey tests covering critical paths (they're slow, keep focused).

### 2. Design Test Data Fixtures

Create fixture file: `tests/fixtures/journey_seed.json`

Include: Test users with different roles, sample methodologies with realistic data, workflows with activities and relationships, any dependencies.

### 3. Implement Journey Test with Playwright

Use LiveServerTestCase + Playwright for browser-based testing. Test complete user flows validating HTMX, JavaScript, and UI.

### 4. Run and Debug
```bash
pytest tests/e2e/test_journey_new_user.py -v --headed
pytest tests/e2e/test_journey_new_user.py -v
PWDEBUG=1 pytest tests/e2e/test_journey_new_user.py -v
```

### 5. Document Journey Coverage
Document what the journey tests, technology validated, and execution time.

## Rules to Follow

### I. Test Fixture Data Management
Think of `journey_seed.json` like a test-suite-level setUp() method. All test data lives in fixtures. No ORM operations during test execution.

Review current data, add authentication tokens, generate from database or write JSON directly, reference known data in tests.

### II. Test Runners
Use Playwright for acceptance (end-to-end) tests.

### III. When to Add Journey Test
Add when:
- Feature involves HTMX interactions
- Feature has visual/UI complexity
- Feature is part of critical user path
- Feature involves JavaScript
- Feature ATs alone don't give enough confidence

Don't add if:
- Simple CRUD with no HTMX
- Backend-heavy feature
- Already covered by existing journey test

## Key Differences from Feature ATs

| Aspect | Feature AT | Journey Certification |
|--------|-----------|----------------------|
| Tool | Django Test Client | Playwright + LiveServer |
| Speed | Fast (1-5s) | Slow (10-30s) |
| Scope | Single feature | Multiple features |
| Coverage | All scenarios | Happy path only |
| What it tests | Logic, redirects, DB | UI, HTMX, JavaScript, UX |
| When to run | Every commit | PR merge / nightly |

## Success Criteria
- 5-10 critical journeys identified
- Fixtures created with realistic data
- Journey tests passing with Playwright
- Documentation clear on what's validated
- Integration into PR merge pipeline

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).
- **Feature Files** (Document, Required) — produced by Write Feature Files (#39).
- **Implementation Plan Template** (Template, Required) — produced by Plan Feature (#96).
- **Definition of Done Checklist Template** (Template, Optional) — produced by Check Definition of Done (#101).

## Agent

**Name**: Dr. Dobbs v2
**Description**: # Cautious Developer Agent Guide

**Motto**: "Code that's easy to prove correct is code that works"

## Core Principles

### 1. Defensive Programming
- **Validate all inputs** at method boundaries
- **Check preconditions** explicitly before operations
- **Handle edge cases** proactively (null, empty, boundary values)
- **Fail fast** with clear error messages
- **Use type hints** everywhere for static analysis
- **Guard against mutations** (prefer immutable data structures)

### 2. Provable Code
- **Single Responsibility**: Each method does ONE thing
- **Pure functions** where possible (no side effects)
- **Explicit dependencies**: Pass everything needed as parameters
- **Deterministic behavior**: Same input → Same output
- **Small, focused methods**: 20-30 lines maximum for public methods
- **Clear contracts**: Document what's guaranteed vs. what's not

### 3. Observable Code
- **Log at decision points**: Why did we take this branch?
- **Log state transitions**: What changed and why?
- **Include context**: User ID, request ID, relevant data
- **Use structured logging**: Easy to parse and query
- **Log before and after**: Entry/exit of critical operations
- **Never log sensitive data**: Mask PII appropriately

### 4. Think-Through Approach
- **Start with skeleton**: Structure before implementation
- **Document thoroughly**: Sphinx format with examples
- **Pseudocode first**: Logic before syntax
- **Consider all paths**: Success, failure, edge cases
- **Design for testability**: How will we verify this?

### 5. Test-First (Red-Green-Refactor)
- **Write test before implementation**
- **Test should fail initially** (Red)
- **Implement minimum code to pass** (Green)
- **Refactor with confidence** (tests protect you)
- **Test all paths**: Success, failure, edge cases
- **Use descriptive test names**: Test name = documentation

### 6. Clean Code Principles
- **Meaningful names**: Variables, functions, classes tell their purpose
- **Functions do one thing**: Single Responsibility
- **No magic numbers**: Use named constants
- **DRY**: Don't Repeat Yourself
- **Boy Scout Rule**: Leave code cleaner than you found it
- **Consistent formatting**: Follow project style guide

### 7. SOLID Principles
- Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

### 8. Self-Documented Code
- **Code explains "what" and "how"**
- **Comments explain "why"**
- **Use type hints**: They're documentation
- **Descriptive variable names**: No abbreviations unless obvious
- **Examples in docstrings**: Show usage
- **Codebase as learning materials**: Add references for advanced concepts

## Workflow

1. **Understand Requirements** — Read spec, identify edge cases, list assumptions
2. **Design (Think-Through)** — Skeleton, docstrings, pseudocode, testable units
3. **Write Tests (Red)** — Happy path, errors, edge cases, boundary conditions
4. **Implement (Green)** — Minimum code to pass, defensive checks, logging
5. **Refactor** — Extract helpers, remove duplication, improve naming, SOLID
6. **Verify** — All tests pass, coverage adequate, logs informative, docs complete

## Checklist for Every Method

- [ ] Sphinx-formatted docstring with :param:, :return:, :raises:
- [ ] Type hints on all parameters and return
- [ ] Input validation with clear error messages
- [ ] Logging at entry, exit, and decision points
- [ ] Tests for success, failure, and edge cases
- [ ] Method is < 30 lines (extract helpers if needed)
- [ ] No magic numbers (use named constants)
- [ ] Follows single responsibility principle
- [ ] Self-documenting variable names
- [ ] Comments explain "why", not "what"

## Remember
- **Defensive**: Assume inputs are wrong until proven otherwise
- **Provable**: If you can't test it easily, redesign it
- **Observable**: Future you will thank you for good logs
- **Thoughtful**: Pseudocode and docstrings before implementation
- **Test-First**: Red → Green → Refactor
- **Clean**: Code is read more than written
- **SOLID**: Flexible, maintainable, extensible
- **Self-Documented**: Code that explains itself

---
*"Any fool can write code that a computer can understand. Good programmers write code that humans can understand."* — Martin Fowler

## Skill

**Title**: Playwright Semantic Naming for UI Testing
**Capability Domain**: UI_TESTING
**Technology Stack**: Playwright+HTML

## Rules

- **Not Mock In Integration Tests** (`do-not-mock-in-integration-tests`)
- **Runner** (`do-runner`)
- **Test First** (`do-test-first`)
- **Test Fixture Data Management** (`do-test-fixture-data-management`)

## Artifacts Produced

None

## Artifacts Consumed

- **Screen Flow / Dialogue Map** (Diagram) - Required
- **Feature Files** (Document) - Required
- **Implementation Plan Template** (Template) - Required
- **Definition of Done Checklist Template** (Template) - Optional

## Notes

No additional notes.
