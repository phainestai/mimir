# Activity: Implement Journey Certification Tests

**Activity ID**: 13
**Order**: 5
**Phase**: Testing
**Dependencies**: Predecessor: Activity 12 (Implement Feature Acceptance Tests)

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

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
