# Playbook access control (FOB — target model)

This document is the source of truth for playbook permissions in Mimir FOB.
Feature files under `act-2-playbooks/` and `act-9-pips/` align with this model.

> **MVP note:** The simplified implementation for MVP supports two visibility values:
> **Private** and **Public**. Family, Local, and Homebase sync are deferred.
> Owner PIP finalisation runs through Django Admin for MVP; the in-FOB owner
> finalize UI is the first post-MVP piece.

---

## Visibility

| Value | Who can view | Who can edit (draft) | Who can finalize PIP (released) |
|-------|-------------|----------------------|---------------------------------|
| **Private** | Owner only | Owner only | Owner or Staff admin |
| **Public** | Any authenticated user | Owner only | Owner or Staff admin |

- Default on creation: **Private**.
- Changing from Public → Private immediately hides the playbook from non-owners.
- Changing from Private → Public immediately makes it readable to all logged-in users.

---

## Access by surface

| Surface | Private playbook | Public playbook |
|---------|-----------------|-----------------|
| **FOB GUI list** | Owner only | Appears in "Public Playbooks" tab / search for all users |
| **FOB GUI detail** | Owner only | Any authenticated user (read-only for non-owners) |
| **MCP tools** | Owner only (`author=user`) | Owner only (MCP scoped to author; public read is GUI-only) |
| **REST API** | Owner or `shared_with_groups` member | Owner or `shared_with_groups` member |

---

## Lifecycle (status)

- **draft** — editable by owner; version 0.x; auto-increments on save.
- **released** — read-only direct edits; version 1.0+; changes via PIP.
- **active** / **disabled** — legacy statuses retained in model.

---

## PIP acceptance (released playbooks)

| Actor | Can submit PIP | Can finalize (accept/reject changes) |
|-------|---------------|--------------------------------------|
| **Playbook owner** | Yes | Yes |
| **Staff admin** (`is_staff`) | No | Yes (Django Admin; in-FOB UI post-MVP) |
| **Public viewer** (not owner) | No | No |
| **Anonymous / non-owner** | No | No |

> **MVP note:** In-FOB owner finalize UI is not yet built. For MVP, owners
> submit PIPs and staff finalize via Django Admin. The `@mvp_gap` tag marks
> scenarios that describe the owner-finalize FOB UI.

---

## Deferred (not in MVP)

- **Family** visibility (Homebase family sharing)
- **Local only** visibility (exclude from Homebase sync)
- MCP public read access (MCP remains author-scoped)
- REST API group sharing UI in FOB browser

---

## Related specs

- `playbooks-create.feature` — wizard visibility Private / Public, Step 3 draft/released
- `playbooks-edit.feature` — visibility toggle, owner-only write
- `playbooks-list-find.feature` — "My Playbooks" + "Public Playbooks" browse
- `playbooks-view.feature` — public read by any authenticated user
- `playbooks-delete.feature` — public visibility deletion impact
- `pips-admin-review.feature` — owner and admin finalize, public viewer cannot
- `pips-view.feature` — PIP detail visibility for public viewers
- `docs/features/user_journey.md` — Act 2 narrative
