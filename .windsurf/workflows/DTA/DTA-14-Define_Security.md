# Activity: Define Security

**Activity ID**: TBD
**Order**: 14
**Phase**: Operations
**Dependencies**: Predecessor: DTA-03 (Define Integration & API Design)

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

## Artifacts Produced

- Security decision → contributes to `artifacts/sao_document_template.md` § "13. Security"

## Artifacts Consumed

- Integration & API design decision from DTA-03
- Structured requirements list from DTA-01

## Notes

No additional notes.
