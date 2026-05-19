# Activity: Implement Backend

**Activity ID**: 97
**Order**: 2
**Phase**: Construction
**Dependencies**: None

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

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Feature Files** (Document, Required) — produced by Write Feature Files (#39).
- **System Architecture Overview Template** (Template, Required) — produced by Write SAO.md (#59).
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

**Title**: Django Backend Implementation Patterns
**Capability Domain**: BACKEND_FRAMEWORK
**Technology Stack**: Django+Python+pytest

## Rules

- **Check Previous Commits** (`do-check-previous-commits`)
- **Docstring Format** (`do-docstring-format`)
- **Fix Tests** (`do-fix-tests`)
- **Import On Module Level** (`do-import-on-module-level`)
- **Informative Logging** (`do-informative-logging`)
- **Not Go Into Debugging Loops** (`do-not-go-into-debugging-loops`)
- **Skeletons First** (`do-skeletons-first`)
- **Test First** (`do-test-first`)
- **Validate Api Contracts** (`do-validate-api-contracts`)
- **Keep Docstrings Consistent** (`keep-docstrings-consistent`)

## Artifacts Produced

None

## Artifacts Consumed

- **Feature Files** (Document) - Required
- **System Architecture Overview Template** (Template) - Required
- **Implementation Plan Template** (Template) - Required
- **Definition of Done Checklist Template** (Template) - Required

## Notes

No additional notes.
