# Activity: Define Security

**Activity ID**: 55
**Order**: 14
**Phase**: Inception
**Dependencies**: None

## Description

Define Security

## Guidance

# Define Security

## Objective

Define authentication model, authorization approach, API security measures, dependency scanning, and OWASP compliance targets.

---

## Decisions to Make

### 1. Authentication Model

Choose one:
- **Session-based** — Server-side sessions, cookie-based. Best for: traditional web apps.
- **JWT** — Stateless tokens. Best for: SPAs, mobile apps, microservices.
- **OAuth2/OIDC** — Delegated auth via provider. Best for: SSO, social login.
- **API keys** — Simple key-based auth. Best for: machine-to-machine.
- **mTLS** — Mutual TLS. Best for: service-to-service in zero-trust.

Decide:
- Password hashing algorithm (bcrypt, Argon2, PBKDF2)
- Session/token lifetime and refresh strategy
- MFA requirements (if any)
- Password complexity rules

### 2. Authorization Model

Choose one:
- **RBAC** — Role-Based Access Control. Roles → Permissions. Best for: most web apps.
- **ABAC** — Attribute-Based Access Control. Policy rules on attributes. Best for: complex permission logic.
- **Object-level** — Per-object ownership checks. Best for: multi-tenant apps.
- **Hybrid** — RBAC for coarse-grained + object-level for fine-grained.

Define permission model:
- What roles exist?
- What can each role do?
- How are permissions checked in code? (decorators, middleware, service layer)

### 3. API Security

- **Rate limiting**: Per-user, per-endpoint, per-IP
- **CORS**: Allowed origins, methods, headers
- **Input validation**: Where validated? (serializer, model, view)
- **CSRF protection**: Tokens, SameSite cookies
- **Content Security Policy**: CSP headers configuration

### 4. Dependency Scanning

- **Tool**: Dependabot, Snyk, pip-audit, npm audit, Trivy
- **Cadence**: On every PR? Nightly? Weekly?
- **Policy**: Block merge on critical CVEs? Warning only?
- **License compliance**: Check for incompatible licenses?

### 5. OWASP Compliance

Target OWASP Top 10 coverage:
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A05: Security Misconfiguration
- A07: Identification and Authentication Failures

For each: current mitigation strategy.

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `SEC_AUTH`
- `SEC_AUTHZ`
- `SEC_API`
- `SEC_SCAN`

Report coverage and gaps.

---

## Deliverables

- ✅ **Authentication model** chosen with configuration details
- ✅ **Authorization model** defined with role/permission structure
- ✅ **API security** measures configured
- ✅ **Dependency scanning** tool and policy established
- ✅ **OWASP compliance** targets set
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
