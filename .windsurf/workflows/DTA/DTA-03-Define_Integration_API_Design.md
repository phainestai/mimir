# Activity: Define Integration & API Design

**Activity ID**: TBD
**Order**: 3
**Phase**: Design
**Dependencies**: Predecessor: DTA-02 (Define Application Blocks)

## Description

Define Integration & API Design

## Guidance

# Define Integration & API Design

## Objective

Choose API style, versioning strategy, contract approach, external integration patterns, and inter-service communication model.

---

## Decisions to Make

### 1. API Style

Choose one or hybrid:
- **REST** — Resource-oriented, HTTP verbs, JSON. Best for: standard CRUD web apps.
- **GraphQL** — Query language, single endpoint. Best for: complex data fetching, mobile clients.
- **gRPC** — Binary protocol, protobuf. Best for: internal service-to-service, high throughput.
- **MCP (Model Context Protocol)** — stdio-based, tool-oriented. Best for: AI agent integration.
- **Hybrid** — e.g., REST for web UI + MCP for AI agents.

### 2. API Versioning Strategy

Choose one:
- **URL path** — `/api/v1/playbooks/` → simple, visible, easy to route
- **Header** — `Accept: application/vnd.mimir.v1+json` → clean URLs
- **Query param** — `/api/playbooks/?version=1` → easy to test
- **No versioning** — acceptable for internal-only APIs in early stages

### 3. Contract Approach

Choose one:
- **Contract-first** — Write OpenAPI/AsyncAPI spec first, generate code from it
- **Code-first** — Write code first, generate spec from annotations/decorators
- **No formal contract** — acceptable for internal APIs with single consumer

### 4. External Integrations

- Identify 3rd party APIs the system consumes (if any)
- Define webhook patterns (inbound/outbound)
- Define event bus usage (if applicable)
- Define retry and error handling for external calls

### 5. Inter-Service Communication

If multiple services/processes exist:
- **Sync (HTTP/gRPC)** — Request-response. Simple but creates coupling.
- **Async (Message Queue)** — Fire-and-forget. Decoupled but complex.
- **Shared Database** — Both processes read/write same DB. Simple but limits scaling.
- **File-based** — Export/import via files. Simple for batch scenarios.

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `API_REST`
- `API_GRAPHQL`
- `API_GRPC`
- `API_CONTRACT`

Report coverage and gaps.

---

## Deliverables

- ✅ **API style** chosen with rationale
- ✅ **Versioning strategy** defined
- ✅ **Contract approach** selected
- ✅ **External integrations** identified and patterns defined
- ✅ **Inter-service communication** model chosen (if applicable)
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Integration & API design decision (section for SAO.md)

## Artifacts Consumed

- Structured requirements list from DTA-01
- Application blocks decision from DTA-02

## Notes

No additional notes.
