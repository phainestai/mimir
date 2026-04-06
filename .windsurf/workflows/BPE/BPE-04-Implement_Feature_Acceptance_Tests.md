# Activity: Implement Feature Acceptance Tests

**Activity ID**: 12
**Order**: 4
**Phase**: Testing
**Dependencies**: Predecessor: Activity 11 (Implement Frontend)

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

## Artifacts Produced

None

## Artifacts Consumed

- Skills from capability domains: `TEST_FRAMEWORK`, `TEST_DATA`

## Notes

No additional notes.
