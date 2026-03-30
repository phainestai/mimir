# Activity: Implement Backend

**Activity ID**: 10
**Order**: 2
**Phase**: Implementation
**Dependencies**: Predecessor: Activity 9 (Plan Feature)

## Description

Implement Backend

## Guidance

## Purpose
Implement backend services, models, and Django views following test-first development and small increments approach.

## Steps

### 1. Create Skeletons
Create all class and method skeletons with `NotImplementedError` and full docstrings. Include proper ReST/Sphinx docstrings for all methods.

The core principle: the developer who has no knowledge of the system can implement methods/properties etc. following only documentation in the skeleton.

- Create class and method/function stubs and document them
- Include full docstrings, return types (eg "-> list[str]"), and sample return values
- Use `raise NotImplementedError()` in each method
- Do not skip type hints or documentation
- Add comments inside the methods pointing attention to the logic flow, exception handling, logging etc.

### 2. Write Tests Before Logic
Write unit tests before writing method logic using pytest. Use real dependencies in integration scenarios - no mocking.

### 3. Implement Incrementally
Work method-by-method. Each method/property should be: implemented → tested → committed separately.

### 4. Add Comprehensive Logging
Always add app.log into the application with a logger and file handler which rotates the log on every app relaunch. Add extensive logging on the INFO level so we can troubleshoot who was doing what with which data when error occurred. Use logs/app.log to check for errors when app is not running as expected.

Every service call or controller action must log to `app.log` at INFO level. Log wiped on every restart for clean diagnosis.

**On the INFO level, always include:**
- Who triggered the action (user or agent)
- What the action did (inputs, affected models)
- Why the action occurred (based on intent, rule, or logic)
- The exact location (class, method/function, line if possible)
- Key input parameters or identifiers relevant to the operation
- The specific operation or action being attempted
- The error or unexpected condition encountered
- Relevant context or state (e.g., user ID, transaction ID, environment)

Design each log message so that if something fails, you can find the source and root cause without guessing or needing to reproduce the problem.

### 5. Commit After Each Step
Write → run → test → evaluate → fix. Commit using Angular-style commit messages.

### 6. Django Views Architecture
- **Services Layer**: Business logic shared between MCP and Web UI
- **Repository Pattern**: Data access abstraction (currently Django ORM, can be swapped)
- **Django Views**: Return rendered HTML templates (NOT JSON/DRF)
- **HTMX Endpoints**: Return HTML fragments for dynamic updates
- **Template Context**: Always validate and document context

### 7. URL Pattern Registration
Register new views in app urls.py with descriptive names. Follow RESTful conventions for URL structure.

### 8. Testing Django Views
Use Django TestCase (NOT DRF test clients). Test with Django test client, validate template context, check template used, test HTMX endpoints with HTTP_HX_REQUEST header.

## Rules to Follow

### I. Skeleton-First Development
Read short-concise-methods rule and keep-docstrings-consistent rule. Create class and method stubs with full documentation before implementation.

### II. Test Runners
Use pytest for unit and integration tests, Django test client for API view tests, Playwright for acceptance (end-to-end) tests.

### III. No Mocking in Integration Tests
Do not use mocks in integration tests - they're supposed to use real objects, real connections, real or real-like data from fixtures. Think of them as acceptance tests without UI.

### IV. Informative Logging
Every service call or controller action must log to `app.log` at INFO level. Include method entry with context, data structure logging with buffers, conditional logic documentation, data validation and transformation results, error context with full parameter context.

**Log Level Guidelines:**
- DEBUG: Detailed flow control, type checking, internal state
- INFO: Method entry/exit, configuration, major processing steps, results
- WARNING: Concerning but recoverable conditions, substitutions, fallback usage, data quality issues
- ERROR: Failures requiring attention, unrecoverable conditions

### V. Import Management
All imports must be at module level. No imports inside functions/methods. Dependencies must be properly declared.

## Success Criteria
- All skeletons created with full docstrings
- Tests written before implementation
- All tests passing
- Comprehensive logging added
- Code committed with proper messages
- Django views properly registered
- Services layer properly structured

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
