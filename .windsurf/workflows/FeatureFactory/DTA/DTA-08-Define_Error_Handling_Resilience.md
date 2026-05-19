# Activity: Define Error Handling & Resilience

**Activity ID**: 49
**Order**: 8
**Phase**: Inception
**Dependencies**: None

## Description

Define Error Handling & Resilience

## Guidance

# Define Error Handling & Resilience

## Objective

Define error taxonomy, error response format, retry policies, circuit breaker patterns, graceful degradation strategy, and idempotency requirements.

---

## Decisions to Make

### 1. Error Taxonomy

Classify errors into categories:
- **Domain errors** — Business rule violations (e.g., "Cannot delete released playbook")
- **Validation errors** — Input validation failures (e.g., "Name is required")
- **Infrastructure errors** — DB connection lost, disk full, OOM
- **External service errors** — 3rd party API timeout, rate limit exceeded
- **Authentication/Authorization errors** — Invalid session, insufficient permissions

For each category: how is it logged, how is it presented to the user, what's the HTTP status code?

### 2. Error Response Format

Define a standard error envelope:
```json
{
  "error": {
    "code": "PLAYBOOK_NOT_FOUND",
    "message": "Playbook with ID abc-123 does not exist",
    "details": {},
    "request_id": "req-xyz-789"
  }
}
```

Decide:
- Standard error codes (enum or free-text?)
- User-facing messages (localization needed?)
- Technical details (shown in dev, hidden in prod?)
- Correlation/request IDs for tracing

### 3. Retry Policies

For each type of retriable operation:
- Which operations are retriable? (network calls, DB transactions, queue publish)
- Backoff strategy: linear, exponential, jitter
- Max attempts before giving up
- Dead letter queue for permanently failed operations

### 4. Circuit Breakers

For external service dependencies:
- Failure threshold before circuit opens (e.g., 5 failures in 30 seconds)
- Fallback behavior when circuit is open
- Half-open recovery: how and when to retry
- Monitoring: how to alert on open circuits

### 5. Graceful Degradation

- Which features can operate in degraded mode?
- How are users notified of degraded functionality?
- Fallback data sources (cached data, default values)
- Feature flags for emergency feature disabling

### 6. Idempotency

- Which write operations must be idempotent? (payment processing, data import)
- How is idempotency ensured? (idempotency keys, upsert patterns, deduplication)
- Timeout handling: what happens if a request times out but the operation completed?

### 7. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `ERR_HANDLING`
- `ERR_RESILIENCE`
- `ERR_RETRY`

Report coverage and gaps.

---

## Deliverables

- ✅ **Error taxonomy** defined with handling rules per category
- ✅ **Error response format** standardized
- ✅ **Retry policies** defined for retriable operations
- ✅ **Circuit breaker** patterns defined (if applicable)
- ✅ **Graceful degradation** strategy documented
- ✅ **Idempotency** requirements identified
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

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

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
