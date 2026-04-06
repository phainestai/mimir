# Activity: Define Config & Secrets

**Activity ID**: TBD
**Order**: 13
**Phase**: Operations
**Dependencies**: Predecessor: DTA-09 (Define Infrastructure)

## Description

Define Config & Secrets

## Guidance

# Define Config & Secrets

## Objective

Define environment configuration strategy, secrets management, feature flag approach, and per-environment overrides.

---

## Decisions to Make

### 1. Environment Configuration

- **Config source**: Environment variables, config files (.env, YAML, TOML), Django settings
- **Per-environment overrides**: How do dev/staging/prod configs differ?
- **Config validation**: Are required configs validated at startup?
- **Config documentation**: Where are all config options documented?

Example patterns:
```
# .env file (local)
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
SECRET_KEY=dev-only-key

# Production (env vars from secrets manager)
DEBUG=False
DATABASE_URL=postgresql://...
SECRET_KEY=<from-vault>
```

### 2. Secrets Management

Choose approach:
- **Environment variables** — Simple, works everywhere. Risk: leakage in logs/errors.
- **Secrets manager** — AWS Secrets Manager, HashiCorp Vault, Azure Key Vault. Best for: production.
- **Sealed secrets** — Encrypted in Git, decrypted in cluster. Best for: GitOps.
- **.env files** — Local only, gitignored. Best for: development.
- **Django's SECRET_KEY rotation** — How often? How to rotate without downtime?

### 3. Feature Flags

- **Approach**: Config-based, database-based, external service (LaunchDarkly, Unleash)
- **Flag types**: Boolean (on/off), percentage rollout, user segment
- **Management**: Who can toggle flags? Via UI, CLI, API?
- **Cleanup**: How are stale flags removed?

### 4. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `CONFIG_ENV`
- `CONFIG_SECRETS`
- `CONFIG_FLAGS`

Report coverage and gaps.

---

## Deliverables

- ✅ **Environment configuration** strategy defined
- ✅ **Secrets management** approach chosen
- ✅ **Feature flag** approach defined (if applicable)
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Config & secrets decision → contributes to `artifacts/sao_document_template.md` § "12. Config & Secrets"

## Artifacts Consumed

- Infrastructure decision from DTA-09

## Notes

No additional notes.
