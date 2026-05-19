# Activity: Implement Feature Acceptance Tests

**Activity ID**: 99
**Order**: 4
**Phase**: Construction
**Dependencies**: None

## Description

Implement Feature Acceptance Tests

## Guidance

## Purpose
Test all scenarios from a `.feature` file using your framework's test client to ensure feature works correctly at the logic level. This is Tier 1 Testing: Fast, comprehensive feature validation.

## When to Use
For every feature implementation. Run on every commit.

## Steps

### 1. Identify Feature Scenarios
Review the feature file, list all scenarios. Goal: Create one test method per scenario (or logical group).

### 2. Create Test File
File naming convention: `tests/integration/test_<feature>_<aspect>.<ext>`

Examples:
- tests/integration/test_auth_login
- tests/integration/test_workflow_create
- tests/integration/test_activity_crud

### 3. Implement Tests with Framework Test Client

**Test All Paths:**
- Happy path (valid input → success)
- Validation errors (invalid input → error messages)
- Edge cases (boundary conditions)
- Authentication/authorization checks
- State changes (database, cache, etc.)
- Redirects and messages

### 4. Run Tests
Use your test framework's commands to run tests:
- Run all integration tests for a feature
- Run with coverage reporting
- Run specific test class or method

### 5. Document Coverage
Add documentation to test class documenting which scenarios are covered, test strategy, and how to run.

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `TEST_FRAMEWORK` — Testing patterns and best practices for your stack
- `TEST_DATA` — Test data and fixture management patterns

Apply reference implementations and patterns from matched Skills.

## Rules to Follow

### I. No Mocking in Integration Tests
Do not use mocks - integration tests supposed to use real objects, real connections, real or real-like data from fixtures. Think of them as acceptance tests - just without UI.

### II. Test-First Development
Every function/method must begin with a test. Tests prove that your implementation works as intended.

### III. Test Framework
Use your test framework for unit and integration tests.

### IV. Fix Tests Immediately
Failing tests are major problem - we don't start new development until we fix them. If it's a test problem - fix it. If it's implementation details vs test diff - either fix the test, or ask user what takes precedence.

### V. Update Tests After Bugfixing
When a bug was discovered and fixed, ask yourself: "why did our current tests not find it?" If there is no test for that functionality - time to create it. If there are tests - extend them to prove the bug doesn't exist anymore.

## Key Principles
1. **Fast** - Should run in 1-5 seconds
2. **Comprehensive** - Cover ALL scenarios from .feature file
3. **No Mocking** - Use real database
4. **Clear** - One test per scenario, clear docstrings
5. **Reliable** - No flaky tests, deterministic results

## Success Criteria
- All scenarios from feature file covered
- Tests run in <5 seconds
- 100% pass rate
- Clear docstrings documenting coverage
- No mocking used in integration tests

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).
- **Feature Files** (Document, Required) — produced by Write Feature Files (#39).
- **HTML Mockups** (Code, Optional) — produced by Create Mockups (#40).
- **Implementation Plan Template** (Template, Required) — produced by Plan Feature (#96).
- **Definition of Done Checklist Template** (Template, Required) — produced by Check Definition of Done (#101).

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

**Title**: pytest Continuous Testing
**Capability Domain**: TEST_FRAMEWORK
**Technology Stack**: pytest+Python

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
- **HTML Mockups** (Code) - Optional
- **Implementation Plan Template** (Template) - Required
- **Definition of Done Checklist Template** (Template) - Required

## Notes

No additional notes.
