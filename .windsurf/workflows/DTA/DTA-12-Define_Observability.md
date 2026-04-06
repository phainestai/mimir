# Activity: Define Observability

**Activity ID**: TBD
**Order**: 12
**Phase**: Operations
**Dependencies**: Predecessor: DTA-09 (Define Infrastructure)

## Description

Define Observability

## Guidance

# Define Observability

## Objective

Define logging, metrics, distributed tracing, dashboards, alerting, and incident response approach.

---

## Decisions to Make

### 1. Logging

- **Format**: Structured logging (JSON) vs. plain text
- **Library**: Python logging, structlog, loguru
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL — when to use each
- **Aggregation**: CloudWatch, ELK stack, Loki, local file rotation
- **Retention**: How long are logs kept? Per environment?
- **Sensitive data**: What must NOT be logged? (passwords, tokens, PII)

### 2. Metrics

- **Application metrics**: Request count, response time, error rate, queue depth
- **Infrastructure metrics**: CPU, memory, disk, network
- **Business metrics**: Features used, user actions, conversion rates
- **Tools**: Prometheus, CloudWatch Metrics, Datadog, StatsD
- **Naming convention**: `app.request.duration`, `app.db.query.count`

### 3. Distributed Tracing

- **Correlation IDs**: How are requests traced across services/processes?
- **Span collection**: OpenTelemetry, Jaeger, Zipkin, X-Ray
- **Trace sampling**: Sample all requests or a percentage?
- **Trace context propagation**: How are trace IDs passed between services?

### 4. Dashboards & Alerting

- **Dashboard tool**: Grafana, CloudWatch Dashboards, Datadog
- **SLIs/SLOs**: Service Level Indicators and Objectives
  - e.g., "99.9% of requests complete in < 500ms"
  - e.g., "Error rate < 0.1%"
- **Alert channels**: Email, Slack, PagerDuty, OpsGenie
- **Alert severity levels**: P1 (page immediately) through P4 (review next day)

### 5. Incident Response

- **Runbooks**: Standard operating procedures for common incidents
- **Postmortems**: Blameless postmortem template and cadence
- **On-call rotation**: Who is on call? How are they reached?
- **Escalation path**: P1 → on-call → team lead → management

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `OBS_LOGGING`
- `OBS_METRICS`
- `OBS_TRACING`

Report coverage and gaps.

---

## Deliverables

- ✅ **Logging** strategy defined (format, aggregation, retention)
- ✅ **Metrics** approach chosen (tools, naming, key metrics)
- ✅ **Distributed tracing** configured (if applicable)
- ✅ **Dashboards & alerting** defined (SLIs/SLOs, alert channels)
- ✅ **Incident response** procedures established
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Observability decision (section for SAO.md)

## Artifacts Consumed

- Infrastructure decision from DTA-09
- Application blocks decision from DTA-02

## Notes

No additional notes.
