# Activity: Implement Backend

**Activity ID**: 10
**Order**: 2
**Phase**: Implementation
**Dependencies**: Predecessor: Activity 9 (Plan Feature)

## Description

Implement Backend

## Guidance

## Purpose
Implement backend services, models, and views following test-first development and small increments approach.

## Steps

### 1. Create Skeletons
Create all class and method skeletons with full docstrings following your language's documentation conventions.

The core principle: the developer who has no knowledge of the system can implement methods/properties etc. following only documentation in the skeleton.

- Create class and method/function stubs and document them
- Include full docstrings, return types, and sample return values
- Use appropriate placeholder (e.g., `NotImplementedError`, `TODO`, `panic!`, etc.)
- Do not skip type hints or documentation
- Add comments inside the methods pointing attention to the logic flow, exception handling, logging etc.

### 2. Write Tests Before Logic
Write unit tests before writing method logic using your test framework. Use real dependencies in integration scenarios - no mocking.

### 3. Implement Incrementally
Work method-by-method. Each method/property should be: implemented → tested → committed separately.

### 4. Add Comprehensive Logging
Add comprehensive logging to the application with appropriate log rotation. Add extensive logging at INFO level so you can troubleshoot who was doing what with which data when errors occur.

Every service call or controller action must log at INFO level.

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

### 6. Backend Architecture
- **Services Layer**: Business logic shared between different interfaces (API, Web UI, CLI, etc.)
- **Repository Pattern**: Data access abstraction (can be swapped)
- **Views/Controllers**: Return appropriate responses for your framework
- **API Endpoints**: Follow RESTful or your framework's conventions
- **Context/State**: Always validate and document

### 7. Route Registration
Register new routes/endpoints with descriptive names. Follow your framework's conventions for URL/route structure.

### 8. Testing Views/Controllers
Use your framework's test client. Test responses, validate context/state, check templates/views used, test dynamic endpoints.

### 9. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `BACKEND_FRAMEWORK` — Backend implementation patterns for your tech stack
- `TEST_FRAMEWORK` — Testing patterns and best practices
- `LOGGING_PATTERN` — Logging implementation for your language
- `DOCSTRING_FORMAT` — Documentation format for your language

Apply reference implementations and patterns from matched Skills.

## Rules to Follow

### I. Skeleton-First Development
Create class and method stubs with full documentation before implementation. Follow your language's documentation conventions.

### II. Test-First Development
Write tests before implementing logic. Use appropriate test framework for unit and integration tests.

### III. No Mocking in Integration Tests
Do not use mocks in integration tests - they're supposed to use real objects, real connections, real or real-like data from fixtures. Think of them as acceptance tests without UI.

### IV. Informative Logging
Every service call or controller action must log at INFO level. Include method entry with context, data structure logging, conditional logic documentation, data validation and transformation results, error context with full parameter context.

**Log Level Guidelines:**
- DEBUG: Detailed flow control, type checking, internal state
- INFO: Method entry/exit, configuration, major processing steps, results
- WARNING: Concerning but recoverable conditions, substitutions, fallback usage, data quality issues
- ERROR: Failures requiring attention, unrecoverable conditions

### V. Dependency Management
All imports/dependencies must be at module level. No imports inside functions/methods. Dependencies must be properly declared in your dependency management file.

## Success Criteria
- All skeletons created with full documentation
- Tests written before implementation
- All tests passing (100% pass rate)
- Comprehensive logging added
- Code committed with proper messages
- Routes/endpoints properly registered
- Services layer properly structured

## Artifacts Produced

None

## Artifacts Consumed

- Skills from capability domains: `BACKEND_FRAMEWORK`, `TEST_FRAMEWORK`, `LOGGING_PATTERN`, `DOCSTRING_FORMAT`

## Notes

No additional notes.
