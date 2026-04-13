# The Composite: Human-AI OODA for RIPL PM

> *Saved from conversation — April 13, 2026*

---

## Seed: On Command and Composite Cognition

> *"Nothing kills respect faster than pity."*
> — Ninefox Gambit, Yoon Ha Lee

**Command as equation-solving:** Identify the variables, solve the system, implement — ruthlessly or sneakily, whatever the topology of the problem demands. Boyd's OODA, Clausewitz's Schwerpunkt, implicit guidance and control — all variations of the same idea.

**The Composite framing** (Cheris/Jedao as archetype):
- Shared problem representation
- Asymmetric capabilities mapped to subproblems
- A trust/authority protocol that evolves as the mission unfolds
- Neither component can solve the problem alone — the composite is load-bearing

---

## Composite Cognition — Applied Science Foundation

**Distributed cognition** (Hutchins, *Cognition in the Wild*, 1995): cognition is distributed across people, artifacts, and representations. A navigation team isn't six people thinking — it's one cognitive system with six nodes.

**Extended mind theory** (Clark & Chalmers, 1998): cognitive processes can extend into tools. The boundary of "mind" is functional, not anatomical.

**Transactive memory systems** (Kozlowski et al.): high-performing teams don't share all knowledge — they share *knowledge about knowledge*, and route problems accordingly. Maps directly to human+AI composites.

**Empirical signal** (Noy & Zhang, MIT/QJE, 2023): AI assistance didn't just speed up writing — it changed cognitive strategy. Workers offloaded different parts of the problem than expected. That's cognitive restructuring, not tool use.

### Known failure modes
- **Automation bias** — humans over-trust AI under cognitive load; composite becomes less capable than either alone (Parasuraman & Manzey)
- **Skill atrophy** — AI consistently handling a subproblem causes human capability loss; composite degrades in ways neither component would alone
- **Representation mismatch** — human and AI solving slightly different problems because internal representations diverged; invisible until catastrophic

### What a well-functioning composite requires
- Shared problem representation — both nodes working on the same formulation
- Explicit uncertainty signaling — AI communicates confidence, not just answers
- Dynamic authority allocation — who leads on which subproblem shifts as the problem evolves
- Productive friction — a composite that never disagrees has silenced one node

---

## OODA Decomposition for RIPL PM

### The decomposition

| Phase | Owner | Rationale |
|-------|-------|-----------|
| **O1 — Observe** | AI primary | Sensor fusion, pattern detection, recall without fatigue. Human doing first-O alone is slower and noisier. |
| **O2 — Orient** | Composite | Destruction and reconstruction of mental models. AI brings pattern libraries and consistency; human brings contextual judgment, stakes awareness, skin-in-the-game heuristics. |
| **D — Decide** | Human | Requires someone who bears the consequences. Fog is thickest here. Human judgment least replaceable. |
| **A-prep** | AI | Planning, dependency mapping, scenario modeling. |
| **A-exec** | Human | Execution is yours. But AI observes in real time, feeds directly into next O1. |

### The seam to watch — Act

Boyd's Act isn't sequential — it's a commitment that immediately generates new Observe inputs. If AI is on the next Observe cycle but wasn't in the execution, there's a **representation gap** — the AI didn't experience the friction of what actually happened, only the reported outcome.

**Fix:** AI as live observer during execution, flagging divergence from the plan model. Closes the representation gap without giving AI authority it shouldn't have.

### Loop tempo

The side cycling faster wins. The composite either multiplies your tempo or becomes a bottleneck.

---

## Data Foundation — What We Have

| Source | Signal type | Resolution |
|--------|------------|------------|
| GitLab (no squash commits) | Work in progress, commit frequency, PR cycle time | Hours |
| Jira (issue-to-branch traceability) | Ticket state, flow efficiency, estimation drift | Daily |
| SQLite app | PR cycle time, computed metrics | Daily |
| FastMCP wrapper | AI-queryable interface to SQLite | Real-time |

**Derived signals the AI can compute from this stack:**
- Flow efficiency — time tickets spend active vs. waiting
- WIP pressure — open branches per developer, trending
- Commit-to-PR lag — work done but not surfaced for review
- Review responsiveness — how long PRs sit before first comment
- Estimation drift — story points vs. actual cycle time, per ticket type
- Critical path exposure — which open tickets block the most downstream work

---

## Intel Network — Full Stack

### Slack
**What to extract:**
- Blocker mentions — "blocked", "waiting on", "can't proceed", "dependency" — especially those that never surface as Jira updates
- Scope signals — "actually", "wait", "changed", "new requirement", "stakeholder said"
- Decision artifacts — things decided in Slack, never written elsewhere
- Sentiment delta — repeated friction around same component = leading indicator
- Cross-channel ticket ID mentions — conversations relevant to ticket state

**API:** `channels:history` + `search:read` scopes. Private channels require explicit access grants.

### Zoom Transcripts
**API:** `GET /users/{userId}/recordings` — returns VTT transcript files.

**What to extract:**
- Action items — verbal commitments that never become tickets
- Decision records — higher fidelity than Slack; captures reasoning, not just decision
- Blocker discussions raised in standup but not ticketed
- Estimate challenges, scope debates, risk discussions

**Honest constraint:** NLP extraction of action items from transcripts has ~60-70% recall. Augments Orient, doesn't replace human recall.

### Signal linkage principle
Raw Slack and Zoom data is noise. Value multiplies when linked back to Jira tickets and Git branches.

**`signal_events` table schema:**
```
source          (slack / zoom / jira / git)
ticket_id       (nullable — link where possible)
signal_type     (blocker / decision / scope_change / sentiment / commitment)
timestamp
raw_text
extracted_insight
confidence
```

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│              INTEL NETWORK                   │
│  GitLab ──┐                                  │
│  Jira ────┼──► SQLite DB ──► FastMCP         │
│  Slack ───┤                                  │
│  Zoom ────┘                                  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           ONTOLOGY LAYER                     │
│  Neo4j graph — entities + relationships      │
│  Intent → Epic → Story → Task → Branch       │
│  Signal → evidences → Risk                   │
│  Decision → affects → Scope                  │
│  Blocker → threatens → Commitment            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           OODA LOOP                          │
│                                              │
│  NIGHT/MORNING                               │
│  AI pulls signals, computes deltas,          │
│  flags anomalies, generates Orient brief     │
│                                              │
│  MORNING SYNC (20-30 min, composite)         │
│  AI presents state picture                   │
│  You inject: human context, offline          │
│  decisions, political overlay                │
│  Output: decision brief, 2-3 actions         │
│                                              │
│  EXECUTION (yours)                           │
│  AI observes, flags divergence               │
│                                              │
│  EOD                                         │
│  AI re-queries, closes loop,                 │
│  seeds next morning's O1                     │
└─────────────────────────────────────────────┘
```

---

## The Five Phases of Building the Composite

### 1. Doctrine
*What does good look like. What are we optimizing for. What are we willing to sacrifice.*

Questions to answer explicitly:
- Primary objective — velocity, predictability, quality, or weighted combination?
- What constitutes crisis vs. normal variance that self-corrects?
- When does AI escalate vs. absorb and monitor?
- Decision authority model — what can recommendations nudge, what requires explicit decision, what's off-limits?

**Composite element:** Doctrine is a negotiation. AI stress-tests implicit assumptions in stated goals, forces them explicit. Not you dictating to AI.

**Risk if skipped:** AI optimizes for the wrong thing with high efficiency. You consistently override recommendations. Loop degrades. Trust collapses.

---

### 2. Intel Network
*Not just data sources — a network with reliability, freshness, and gap awareness.*

- **Source reliability ratings** — Jira state: high. Slack sentiment: low. AI weights accordingly.
- **Freshness requirements** — commit frequency: hourly. Sprint velocity: daily. Team sentiment: weekly.
- **Gap map** — explicit acknowledgment of what the network can't see. Informal relationships, political context, decisions over lunch. AI must know its own blind spots.
- **Counterintelligence** — signals that can be gamed. If team knows commit frequency is tracked, they'll commit more. Doctrine addresses this.

**Composite element:** You maintain the gap map. AI maintains source reliability model, flags when sources degrade.

---

### 3. Ontology
*Shared conceptual model. Not just schema — defined relationships and inference rules.*

**Core entities:**
```
Intent → Epic → Story → Task → Branch → Commit → PR
Team Member → Capacity → Assignment
Risk → Impact → Mitigation
Decision → Context → Outcome
Signal → Source → Confidence → Ticket linkage
```

**Relationships (matter as much as entities):**
- Signal *evidences* Risk
- Decision *affects* Epic scope
- Blocker *threatens* Commitment
- Sentiment pattern *precedes* Velocity drop

**Substrate:** Neo4j. The inference required ("this blocker mentioned in Slack three days ago is now manifesting as a cycle time spike on this PR") requires graph traversal, not joins.

**Composite element:** You define what relationships mean in RIPL's context. AI proposes inference rules. You validate against experience.

---

### 4. Loop Design

| Cadence | Owner | Purpose |
|---------|-------|---------|
| **Intraday** (continuous) | AI | Git/Jira delta, anomaly detection. No human involvement — accumulates. |
| **Daily** (morning, 20-30 min) | Composite | AI presents state delta + anomalies + risk register. You inject human context. Output: decision brief, 2-3 prioritized actions. |
| **Weekly** (Friday, 45 min) | Composite | Doctrine review. Ontology refinement. Intel network health check. **This is where the system learns.** |
| **Ad hoc** (threshold-triggered) | AI flags → Human decides | Critical path threat, sentiment spike, velocity collapse. Push immediately. |

**Composite element:** You own the thresholds. What constitutes a threshold breach is a Doctrine question, not a data question.

---

### 5. Tooling
*Only specified after Doctrine, Intel Network, Ontology, and Loop Design are defined.*

| Component | Role |
|-----------|------|
| Neo4j | Ontology + relationship graph |
| SQLite | Time-series operational data |
| FastMCP | AI query interface to both |
| Slack extractor | Intel network node |
| Zoom extractor | Intel network node |
| Agent layer | Orient brief generation |
| Decision UI | Morning sync interface |

**Orient brief requirements:**
- Scannable in under 5 minutes
- Anomalies first → context second → recommendations third
- Confidence-rated — AI expresses uncertainty explicitly
- Auditable — every claim traces to a source signal

---

## The Meta-Point

This is **doctrine-driven intelligence architecture** applied to software delivery.

Most PM tooling skips to dashboards because doctrine work is hard and unglamorous. The composite framing is what makes it coherent:

- **You bring:** intent, context, stakes, human judgment under friction
- **AI brings:** consistency, memory, pattern detection across more variables than you can hold simultaneously

The composite only works if:
1. The AI's reasoning is transparent enough to interrogate
2. You have enough productive friction to catch drift
3. The doctrine is explicit enough that the AI knows what it's optimizing for

---

*Next step: Formalize Doctrine, then sketch the Ontology.*
