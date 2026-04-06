# Activity: Define Error Handling & Resilience

**Activity ID**: TBD
**Order**: 8
**Phase**: Design
**Dependencies**: Predecessor: DTA-03 (Define Integration & API Design)

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

## Artifacts Produced

- Error handling & resilience decision → contributes to `artifacts/sao_document_template.md` § "7. Error Handling & Resilience"

## Artifacts Consumed

- Integration & API design decision from DTA-03
- Structured requirements list from DTA-01

## Notes

No additional notes.
