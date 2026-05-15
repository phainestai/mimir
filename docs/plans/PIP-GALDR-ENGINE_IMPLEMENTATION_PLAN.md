# PIP Sub-Story 4: Galdr AI Engine

**Feature file**: cross-cutting — triggered by CREATE-18/DETAIL-16; output consumed by DETAIL-04/05; feeds ADMIN-05/06  
**Scenarios driven**: FOB-PIP-CREATE-18, FOB-PIP-DETAIL-04/05, MCP-PIP-26  
**Complexity**: hard — LLM integration, async triggering, lifecycle state machine  
**Branch**: `feature/act-9-pips/galdr-engine`  
**Depends on**: PIP-LIST (model), PIP-CREATE (`submit_pip` service method)  
**Blocks**: PIP-ADMIN-REVIEW (Admin reviews Galdr output), PIP-MCP (submit_pip MCP scenario MCP-PIP-26)

---

## Overview

Galdr is a background AI worker triggered when a PIP is submitted. It reads the target playbook in full, assesses each Change against the playbook's workflow structure and entity relationships, and writes a per-Change recommendation (ACCEPT / REJECT / NEEDS_CLARIFICATION + reasoning). On completion the PIP transitions `processing_galdr → reviewed`. On failure, it reverts to `submitted` (retryable).

**No Celery needed for MVP.** Galdr runs in a daemon thread spawned by `pip_submit` and `pip_cancel` views, and is also callable via a management command for ops/retry.

---

## BPE-02: Backend Implementation

### Step 1 — LLM Client

**LLM target: Anthropic — default model `claude-sonnet-4-5`.**  
Configuration via `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...          # required
GALDR_MODEL=claude-sonnet-4-5         # default; override to any Anthropic model
```

**File**: `methodology/services/galdr_client.py`

```python
class GaldrClient:
    """
    Thin wrapper around the Anthropic Claude API for Galdr assessments.

    Example:
        client = GaldrClient()
        response = client.call_llm("Assess this change: ...")
        # response: '{"recommendation": "ACCEPT", "reasoning": "..."}'
    """

    def call_llm(self, prompt: str) -> str:
        """
        Send prompt to Anthropic Claude, return raw JSON string response.

        Uses model from settings.GALDR_MODEL (default: claude-sonnet-4-5).
        Reads ANTHROPIC_API_KEY from environment.

        :param prompt: str — full prompt including context + change details
        :returns: str — JSON with keys 'recommendation' and 'reasoning'
        :raises GaldrLLMError: on API failure or malformed response
        :example: '{"recommendation": "ACCEPT", "reasoning": "Consistent with Testing phase."}'
        """
        # import anthropic
        # model = settings.GALDR_MODEL  (default: "claude-sonnet-4-5")
        # client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        # response = client.messages.create(
        #     model=model, max_tokens=1024,
        #     system=SYSTEM_PROMPT,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # Log: prompt length, model, call start/end
        # Return response.content[0].text

    def _parse_response(self, raw: str) -> tuple[str, str]:
        """
        Parse JSON response → (recommendation, reasoning).

        :raises GaldrLLMError: if JSON invalid or keys missing
        """


class GaldrLLMError(Exception):
    """Raised on LLM API errors or unparseable responses."""


class StubGaldrClient(GaldrClient):
    """
    Test double — returns canned ACCEPT response. Used in integration tests.
    Never use in production.

    Example:
        StubGaldrClient().call_llm("any") → '{"recommendation": "ACCEPT", "reasoning": "Stub."}'
    """
    def call_llm(self, prompt: str) -> str:
        return '{"recommendation": "ACCEPT", "reasoning": "Test stub — always accept."}'
```

**Unit tests** (`tests/unit/test_galdr_client.py`):
- [ ] `test_stub_client_returns_accept`
- [ ] `test_parse_response_valid_json`
- [ ] `test_parse_response_invalid_json_raises`
- [ ] `test_parse_response_missing_keys_raises`

Commit: `feat(galdr): add GaldrClient, StubGaldrClient, and GaldrLLMError`

---

### Step 2 — Prompt Templates

**File**: `methodology/services/galdr_prompts.py`

```python
SYSTEM_PROMPT = """\
You are Galdr, an AI reviewer for playbook improvement proposals.
Assess whether each proposed change is consistent with the playbook's goals,
free of conflicts with existing entities, and structurally sound.

Respond ONLY with a JSON object — no prose, no markdown:
{"recommendation": "ACCEPT"|"REJECT"|"NEEDS_CLARIFICATION", "reasoning": "<one paragraph>"}
"""

def build_playbook_context_summary(playbook) -> str:
    """
    Build a compact text summary of the playbook for LLM context.

    :param playbook: Playbook instance with workflows + activities prefetched
    :returns: str summary. Example:
        'Playbook: React Frontend Dev v1.0
         Workflow 10: Component Development
           Activity 20: Setup Project
           Activity 21: Create Components
         Workflow 11: Testing & Documentation
           Activity 22: Component Testing'
    """

def build_change_prompt(change, context_summary: str) -> str:
    """
    Build the full LLM prompt for a single PIPChange assessment.

    :returns: str prompt including system context + playbook summary + change details
    """
```

Commit: `feat(galdr): add prompt templates and context builder`

---

### Step 3 — `GaldrService`

**File**: `methodology/services/galdr_service.py`

```python
class GaldrService:
    """
    Orchestrates AI assessment of a submitted PIP.

    Usage:
        GaldrService().assess_pip(pip_id=42)
        # Transitions: submitted → processing_galdr → reviewed
        # Each Change gets galdr_recommendation + galdr_reasoning
    """

    def __init__(self, client: GaldrClient = None):
        """
        :param client: GaldrClient instance. Defaults to real GaldrClient.
                       Pass StubGaldrClient in tests.
        """
        self.client = client or GaldrClient()

    def assess_pip(self, pip_id: int) -> None:
        """
        Full assessment lifecycle for a single PIP.

        :param pip_id: int — PIP to assess
        :raises ValidationError: if PIP not in 'submitted' status
        """
        pip = self._get_pip_for_processing(pip_id)
        self._mark_processing(pip)
        try:
            context = self._build_playbook_context(pip.playbook)
            for change in pip.changes.all().order_by("order"):
                recommendation, reasoning = self._assess_change(change, context)
                self._write_recommendation(change, recommendation, reasoning)
            self._mark_reviewed(pip)
        except Exception as exc:
            self._mark_failed(pip, exc)
            raise

    def _get_pip_for_processing(self, pip_id: int):
        """
        Fetch PIP and verify it is in 'submitted' status.

        :raises ValidationError: if status != 'submitted'
        """

    def _mark_processing(self, pip) -> None:
        """Set status='processing_galdr', status_changed_at=now()."""

    def _build_playbook_context(self, playbook) -> str:
        """Return compact text summary of playbook for LLM context."""

    def _assess_change(self, change, context: str) -> tuple[str, str]:
        """
        Call LLM for a single Change. Returns (recommendation, reasoning).

        :returns: tuple[str, str]. Example: ("ACCEPT", "No conflicts detected.")
        """

    def _write_recommendation(self, change, recommendation: str, reasoning: str) -> None:
        """Persist galdr_recommendation and galdr_reasoning on the Change."""

    def _mark_reviewed(self, pip) -> None:
        """Set status='reviewed', reviewed_at=now(), status_changed_at=now()."""

    def _mark_failed(self, pip, exc: Exception) -> None:
        """
        Revert to 'submitted' on any error — keeps PIP retryable.
        Logs full exception with pip_id.
        Does NOT set status='rejected'.
        """
```

**Unit tests** with `StubGaldrClient` (`tests/unit/test_galdr_service.py`):
- [ ] `test_assess_pip_transitions_to_reviewed`
- [ ] `test_assess_pip_writes_accept_recommendation_per_change`
- [ ] `test_assess_pip_multiple_changes_all_assessed`
- [ ] `test_assess_pip_invalid_status_raises`
- [ ] `test_assess_pip_llm_failure_reverts_to_submitted`
- [ ] `test_mark_processing_sets_status`
- [ ] `test_mark_reviewed_sets_status_and_reviewed_at`

Commit: `feat(galdr): add GaldrService.assess_pip with full lifecycle`

---

### Step 4 — Integration Test (no LLM mock)

**File**: `tests/integration/test_galdr_service.py`

Use `StubGaldrClient` (not a mock — it's a real test double with deterministic behavior):

```python
class TestGaldrServiceIntegration(TestCase):
    def setUp(self):
        self.galdr = GaldrService(client=StubGaldrClient())

    def test_full_assessment_flow_submitted_to_reviewed(self):
        """Submit PIP → run Galdr → PIP is Reviewed with recommendations on all Changes."""

    def test_partial_reject_stub(self):
        """Configure stub to return REJECT → Change has galdr_recommendation=REJECT."""

    def test_galdr_does_not_process_draft_pip(self):
        """PIP in Draft status → ValidationError raised, status unchanged."""
```

Commit: `test(galdr): integration tests for full assessment flow`

---

### Step 5 — Trigger from `pip_submit` view

**File**: `methodology/pip_views.py`

After `PIPService.submit_pip(pip, user)` succeeds, spawn Galdr in a daemon thread:

```python
import threading
from methodology.services.galdr_service import GaldrService

def _trigger_galdr_async(pip_id: int) -> None:
    """Spawn Galdr assessment in background daemon thread (MVP, no Celery)."""
    thread = threading.Thread(
        target=GaldrService().assess_pip,
        args=(pip_id,),
        daemon=True,
        name=f"galdr-pip-{pip_id}",
    )
    thread.start()
    logger.info("Galdr thread started for PIP %s", pip_id)
```

Update `pip_submit` and the submit path in `pip_create` to call `_trigger_galdr_async(pip.pk)` after status transition.

Commit: `feat(views): trigger Galdr async on pip submit`

---

### Step 6 — Management Command (ops/retry)

**File**: `methodology/management/commands/run_galdr.py`

```
python manage.py run_galdr --pip=42        # re-assess specific PIP
python manage.py run_galdr --all-pending   # assess all in submitted/processing state
```

```python
class Command(BaseCommand):
    help = "Run Galdr AI assessment for one or all pending PIPs"

    def add_arguments(self, parser):
        parser.add_argument("--pip", type=int)
        parser.add_argument("--all-pending", action="store_true")

    def handle(self, *args, **options):
        # Log: command invoked, options
        ...
```

Commit: `feat(management): run_galdr command for ops retry`

---

## BPE-03: Frontend Implementation

Galdr has no dedicated UI page. Its output surfaces in:
- `templates/methodology/pips/detail.html` — Galdr verdict badges (implemented in PIP-VIEW)
- `templates/methodology/pips/admin_review.html` — read-only Galdr reasoning (implemented in PIP-ADMIN)

The only frontend item here is the **status banner** while processing:

In `pip_detail` view, map `processing_galdr` → banner text `"Galdr is reviewing your changes — check back shortly."` — already wired in PIP-VIEW.

Optionally: add polling via HTMX for auto-refresh while status is `processing_galdr`:
```html
{% if pip.status == 'processing_galdr' %}
<div hx-get="{% url 'pip_detail' pk=pip.pk %}"
     hx-trigger="every 5s"
     hx-target="body"
     hx-swap="outerHTML">
</div>
{% endif %}
```

Commit: `feat(templates): HTMX auto-refresh on pip detail while Galdr is processing`

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_galdr_engine.py`

- [ ] `test_galdr_triggered_on_submit_pip_view` — POST to `/pips/<id>/submit/` → Galdr thread starts (check PIP transitions to `processing_galdr` or `reviewed` depending on sync/async)
- [ ] `test_galdr_writes_recommendation_to_all_changes`
- [ ] `test_galdr_pip_reviewed_after_assessment`
- [ ] `test_galdr_failed_pip_reverts_to_submitted`
- [ ] `test_detail_05_processing_banner_shown_before_review` — PIP in `processing_galdr` → banner text correct

Run: `pytest tests/integration/test_galdr_engine.py -v`

Commit: `test(galdr): acceptance tests for Galdr engine lifecycle`

---

## BPE-05: Journey Certification Test

Add a step to the existing `test_pip_journey_view.py` (from PIP-VIEW):

```
After submitting PIP:
  6. Wait up to 3s for Galdr to process (StubGaldrClient in test env)
  7. Refresh /pips/<id>/ — verify status is "Reviewed"
  8. Verify Change #1 shows green ACCEPT badge
```

Use `settings.GALDR_CLIENT_CLASS = 'methodology.services.galdr_client.StubGaldrClient'` for test environment.

Commit: `test(e2e): extend view journey to cover Galdr processing step`

---

## BPE-06: Definition of Done

- [ ] `GaldrService.assess_pip` transitions PIP: `submitted → processing_galdr → reviewed`
- [ ] All Changes receive `galdr_recommendation` and `galdr_reasoning`
- [ ] LLM failures revert PIP to `submitted` (retryable), not `rejected`
- [ ] Galdr triggered asynchronously on submit (daemon thread)
- [ ] `run_galdr --pip=X` management command works
- [ ] `StubGaldrClient` used in all integration/E2E tests (no real LLM calls)
- [ ] Unit tests pass with stub
- [ ] Integration tests pass
- [ ] `GALDR_CLIENT_CLASS` setting allows swapping client in test env
- [ ] INFO logging: PIP id, user trigger, change count, LLM call timing, errors
- [ ] All methods ≤ 30 lines

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Submit a PIP in browser, verify processing → reviewed transition
- [ ] Run `python manage.py run_galdr --all-pending` with a submitted PIP in DB
- [ ] Add `anthropic` to `requirements.txt` (`pip install anthropic && pip freeze | grep anthropic >> requirements.txt`)
- [ ] Ensure `ANTHROPIC_API_KEY` and `GALDR_MODEL` are documented in `.env.example`
- [ ] Final commit: `feat(pips): Galdr AI engine — assess, write recommendations, trigger on submit`
- [ ] Close GitHub issue, `status-done`
- [ ] PR → `main`

---

## Files Created / Modified

**New (7):**
1. `methodology/services/galdr_client.py`
2. `methodology/services/galdr_prompts.py`
3. `methodology/services/galdr_service.py`
4. `methodology/management/commands/run_galdr.py`
5. `tests/unit/test_galdr_client.py`
6. `tests/unit/test_galdr_service.py`
7. `tests/integration/test_galdr_engine.py`

**Modified (2):**
1. `methodology/pip_views.py` — trigger Galdr on submit
2. `mimir/settings.py` — `GALDR_CLIENT_CLASS` setting
