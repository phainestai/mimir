# FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 – DELETE Operation Implementation Plan (Issue #31)

## 0. Scope & References

- **Feature code**: FOB-PLAYBOOKS-DELETE_PLAYBOOK-1
- **Issue**: #31 – DELETE operation (Confirmation modal with cascade)
- **Entity**: Playbook (top-level methodology container in FOB)
- **Behavior**: Delete playbook with confirmation modal, full impact warning, and cascading removal of related entities.

**Primary specification sources:**
- `docs/architecture/SAO.md` – Web UI architecture, URL conventions, HTMX patterns, testing strategy.
- `docs/features/user_journey.md` – Act 2 PLAYBOOKS (DELETE flow description, FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 modal).
- `docs/features/act-2-playbooks/playbooks-delete.feature` – 20 detailed PB-DELETE scenarios.
- `docs/plans/PLAYBOOKS_CRUDV_IMPLEMENTATION_PLAN.md` – existing CRUDV plan; DELETE phase (PHASE 5) is described but not yet implemented.

**Existing implementation to reuse/extend:**
- Models: `methodology/models/playbook.py`, `playbook_version.py`, `workflow.py`, and related entities (activities, artifacts, roles, howtos, etc.) – already created for CRUDV.
- Views: `methodology/playbook_views.py` (list, create wizard, detail, stub edit, legacy add).
- URLs: `methodology/playbook_urls.py` – list, create, create/step2, create/step3, add, detail, edit; **no delete endpoint yet**.
- Templates: playbook list/detail/create wizard already implemented per CRUDV; no dedicated delete modal template yet.
- Tests: `tests/integration/test_playbook_create.py` fully covers PB-CREATE-01..21; delete tests not yet present (no `test_playbook_delete.py`).

Goal of this plan: implement **playbook delete operation with confirmation modal and cascade** to satisfy all scenarios PB-DELETE-01..20.

---

## 1. Requirements Summary from Feature File

From `docs/features/act-2-playbooks/playbooks-delete.feature` and user_journey:

1. **Entry points**
   - From **Playbooks list** (FOB-PLAYBOOKS-LIST+FIND-1): [Delete] in row Actions menu opens confirmation modal.
   - From **Playbook detail view** (FOB-PLAYBOOKS-VIEW_PLAYBOOK-1): [Delete] button opens the same modal.

2. **Confirmation modal (FOB-PLAYBOOKS-DELETE_PLAYBOOK-1)**
   - Title: "Delete Playbook?" (PB-DELETE-01..04)
   - Shows key playbook info (name, version, workflows count, activities count, last modified, etc.).
   - Shows impact statement and counts of dependent entities:
     - Workflows, Activities, Artifacts, Roles, Howtos (PB-DELETE-03, PB-DELETE-10).
   - Strong warning: "This action cannot be undone" + explanation about permanent deletion (PB-DELETE-04).
   - Buttons: [Cancel], [Delete Playbook] (danger style), accessible via keyboard.

3. **Cascade semantics**
   - When deletion is confirmed:
     - The Playbook is permanently removed.
     - All related Workflows, Phases (if any), Activities, Artifacts, Roles, Howtos, Version history are deleted (PB-DELETE-05, PB-DELETE-10, PB-DELETE-16, PB-DELETE-18).
     - Playbook disappears from all views: list, search, recent, dashboard widgets, MCP available playbooks (PB-DELETE-16).

4. **Constraints & special cases**
   - **Downloaded playbooks**: cannot be deleted (PB-DELETE-09):
     - [Delete] not visible / disabled.
     - Tooltip: "Only owned playbooks can be deleted".
   - **Family/shared playbooks**: show extra warnings about family members losing access (PB-DELETE-12).
   - **Active vs Disabled**: Active playbook deletion shows extra warning recommending disabling first, but still allows delete (PB-DELETE-13).
   - **Bulk delete**: explicitly not supported (PB-DELETE-14).
   - **Accessibility**: full keyboard navigation within modal; Enter only deletes when focused on [Delete Playbook] (PB-DELETE-11, PB-DELETE-15).

5. **Error handling & UX**
   - On success: success notification and redirect back to list, with removed playbook no longer visible (PB-DELETE-05, PB-DELETE-16).
   - On DB error: show clear error message in modal, do not delete, and allow Retry/Cancel (PB-DELETE-19).
   - Suggest export backup for important playbooks (PB-DELETE-20) with [Export JSON First] link that triggers export but keeps modal open.

---

## 2. Current State of Codebase (Delete-related)

1. **Models**
   - `Playbook`, `Workflow`, `PlaybookVersion`, and related entities already exist per CRUDV plan.
   - Relationships likely use `on_delete=CASCADE`; plan must **verify this** when implementing cascade behavior, and adjust if needed.

2. **URLs** – `methodology/playbook_urls.py`
   - Currently:
     - `''` → `playbook_list`
     - `create/`, `create/step2/`, `create/step3/` → create wizard
     - `add/` → legacy add (redirects to wizard)
     - `<int:pk>/` → `playbook_detail`
     - `<int:pk>/edit/` → `playbook_edit` (stub)
   - **No `delete/` URL yet**.

3. **Views** – `methodology/playbook_views.py`
   - Implemented: list, create wizard steps 1–3, detail, legacy add, stub edit.
   - **No delete view** yet – PHASE 5 of CRUDV plan is unimplemented.

4. **Templates**
   - Playbook list/detail/create templates exist.
   - No dedicated `playbooks/delete_modal.html` or similar; delete button/actions likely not wired.

5. **Tests**
   - CRUDV plan defines `tests/integration/test_playbook_delete.py` as future location for PB-DELETE-01..20.
   - Currently **no** `test_playbook_delete.py`; delete behavior is not covered by tests.

---

## 3. Open Questions for Clarification

These questions do not block the plan but affect implementation details:

1. **Cascade scope**: Should all related entities be physically deleted, or should some be archived?
   - According to the feature file, physical deletion is acceptable, but we should confirm there's no hidden requirement for an audit log beyond standard DB history.
2. **Export JSON integration**: Is the `playbook_export` view already implemented, which should be linked from [Export JSON First]? (see CRUDV PLAN PHASE 3.6)
3. **Family/Homebase integration**: Some warnings (PB-DELETE-12) assume Homebase synchronization. For the MVP Delete, should we implement only the local aspect and mark Homebase scenarios as "partial"?

In the absence of additional information, this plan assumes that:
- **Local deletion** (SQLite) will be fully implemented.
- Homebase-related messages can be shown as static text without actual sync calls.

---

## 4. Detailed TODO Plan (Atomic Steps)

### 4.1. Preparation & Rules

1. **Re-read core rules before implementation**
   - [ ] `docs/architecture/SAO.md` – patterns for URLs, HTMX, testing.
   - [ ] `.windsurf/rules/do-plan-before-doing.md` (already considered during planning).
   - [ ] `.windsurf/rules/do-test-first.md` – tests first, then implementation.
   - [ ] `.windsurf/rules/do-informative-logging.md` – INFO-level logging in views.
   - [ ] `.windsurf/rules/tooltips.md` – tooltips on buttons.
   - [ ] `.windsurf/rules/do-semantic-versioning-on-ui-elements.md` – `data-testid` for modals, buttons, etc.

2. **Branch & commits**
   - [ ] Create a branch for Issue #31, e.g., `feature/playbooks-delete`.
   - [ ] Follow Angular commit convention (`feat(playbooks): ...`, `test(playbooks): ...`).

---

### 4.2. Backend Design – Delete Endpoint & Cascade

Goal: Implement the server-side delete operation, reusing the existing Playbook model layer.

1. **URL pattern for delete**
   - [ ] In `methodology/playbook_urls.py` add:
     - `path('<int:pk>/delete/', playbook_views.playbook_delete, name='playbook_delete')`.
   - [ ] Ensure the URL follows SAO convention (`/playbooks/playbook/delete/{id}` at the project URLs routing level).

2. **View: `playbook_delete`**
   - [ ] In `methodology/playbook_views.py` implement a new view `playbook_delete(request, pk)`:
     - Decorators: `@login_required`, `@require_http_methods(["POST"])` for the delete operation.
     - Behavior:
       - Get Playbook by `pk` or return 404.
       - Verify the user is the owner (`source='owned'`) and has delete permissions.
         - Otherwise, return a redirect with an error message (or 403) and **do not delete**.
       - In a transaction:
         - Delete the Playbook (`playbook.delete()`), relying on `on_delete=CASCADE` for Workflows/Activities and other related entities.
         - Handle potential DB errors (see PB-DELETE-19).
       - After successful deletion:
         - Set a success message: `messages.success(request, "Playbook 'X' deleted successfully")`.
         - Redirect to `playbook_list`.
       - On `Exception`:
         - Log the error (logger.error with `exc_info=True`).
         - Return a JSON/HTML response that the frontend modal can display as an error without closing.
   - [ ] Add INFO-level logs:
     - Deletion attempt: who, which playbook ID/name.
     - Successful deletion.
   - [ ] Add ERROR logs for exceptions with `exc_info=True`.

3. **Data model / cascade verification**
   - [ ] Verify models:
     - `Workflow.playbook = ForeignKey(Playbook, on_delete=CASCADE, ...)`.
     - Relationships between Activities/Artifacts/Roles/Howtos and Playbook/Workflow.
   - [ ] If cascade deletion is missing but required for PB-DELETE-10/16, update `on_delete` or implement explicit cascade deletion in the service layer.
   - [ ] Add (if needed) a `delete_playbook_with_cascade(playbook: Playbook)` method/service in a separate layer (service/repository) if the logic becomes too complex for the view (follow the short methods rule).

---

### 4.3. Frontend – Delete Modal & Integration Points

1. **Delete modal template**
   - [ ] Create a template, e.g., `templates/playbooks/delete_modal.html`:
     - Use Bootstrap modal markup.
     - Include:
       - Title: "Delete Playbook?".
       - Block with playbook details (name, version, status, last_modified, counts).
       - Impact statement listing entities: Workflows, Activities, Artifacts, Roles, Howtos.
       - Main warning text ("This action cannot be undone", PB-DELETE-04).
       - Suggestion for export (PB-DELETE-20) with [Export JSON First] link.
     - Buttons:
       - [Cancel] (secondary).
       - [Delete Playbook] (danger, red).
     - `data-testid`:
       - `data-testid="playbook-delete-modal"` for the root container.
       - `data-testid="playbook-delete-confirm-button"` and `...-cancel-button` for buttons.
       - Additional test IDs for impact counts if needed.

2. **Wiring from list and detail views**
   - [ ] In the playbooks list template, add a `Delete` action to the Actions menu:
     - Button/link that opens the modal (via data-attributes or HTMX request for the `delete_modal.html` fragment).
   - [ ] In the detail view template, add a `Delete` button in the top actions section:
     - Similarly, opens the same modal.
   - [ ] Use HTMX to load the modal content (as per SAO: standard Django views returning HTML fragments).
     - Add an HTMX endpoint, e.g., `playbook_delete_confirm(request, pk)` with populated data.

3. **Keyboard accessibility & behavior**
   - [ ] Ensure the modal supports Tabbing between Cancel/Delete (PB-DELETE-11, PB-DELETE-15).
   - [ ] Confirm that Enter does not trigger deletion unless focus is on Delete (handled by default form+button behavior or minimal JS/attributes).

4. **Export JSON integration**
   - [ ] If `playbook_export` is implemented, use its `href`/HTMX call from [Export JSON First].
   - [ ] After export, keep the modal open (PB-DELETE-20).

---

### 4.4. Tests – Integration (NO mocking)

Create a new test file **for DELETE**:

1. **Test file skeleton**
   - [ ] Create `tests/integration/test_playbook_delete.py`.
   - [ ] Use pytest + `django_db` marker.
   - [ ] Add fixtures/helpers to create a playbook with dependencies (workflows, activities, etc.).

2. **Map scenarios PB-DELETE-01..20 → tests**

Example tests:

- [ ] `test_open_delete_confirmation_from_list` → PB-DELETE-01.
- [ ] `test_open_delete_confirmation_from_detail` → PB-DELETE-02.
- [ ] `test_modal_shows_playbook_details_and_impact_counts` → PB-DELETE-03,10.
- [ ] `test_modal_shows_warning_and_buttons` → PB-DELETE-04.
- [ ] `test_confirm_deletion_deletes_playbook_and_redirects_to_list` → PB-DELETE-05.
- [ ] `test_cancel_deletion_from_modal_and_x_and_backdrop` → PB-DELETE-06,07,08.
- [ ] `test_cannot_delete_downloaded_playbook` → PB-DELETE-09.
- [ ] `test_delete_requires_explicit_action_no_auto_submit` → PB-DELETE-11.
- [ ] `test_delete_family_playbook_shows_family_warning_text` → PB-DELETE-12.
- [ ] `test_delete_active_playbook_shows_active_warning_but_allows_delete` → PB-DELETE-13.
- [ ] `test_bulk_delete_not_supported` → PB-DELETE-14 (verify absence of bulk-actions in list template).
- [ ] `test_keyboard_navigation_in_delete_modal` → PB-DELETE-15.
- [ ] `test_deletion_removes_from_all_views` → PB-DELETE-16.
- [ ] `test_deletion_cannot_be_undone_no_undo_link` → PB-DELETE-17.
- [ ] `test_delete_local_only_no_homebase_sync` → PB-DELETE-18 (can be limited to checking absence of sync call or UI text if sync is not implemented).
- [ ] `test_delete_database_error_shows_error_notification_and_keeps_modal` → PB-DELETE-19.
- [ ] `test_delete_modal_shows_export_json_first_link` → PB-DELETE-20.

3. **Test-first workflow**
   - [ ] Start with basic scenarios (01–06) and write failing tests.
   - [ ] Implement backend+frontend to satisfy the first scenarios.
   - [ ] Gradually add complex scenarios (warnings, counts, error handling, export, accessibility).
   - [ ] Always run:
     - `pytest tests/integration/test_playbook_delete.py -vv`.
     - Periodically – `pytest tests/` for regression.

---

### 4.5. Logging, Errors, and Cascades

1. **Logging**
   - [ ] Add INFO logs in `playbook_delete`:
     - Deletion attempt (user, playbook id/name, source, visibility, status).
     - Successful deletion.
   - [ ] Add ERROR logs for exceptions with `exc_info=True`.

2. **Error handling**
   - [ ] Wrap delete in `transaction.atomic`.
   - [ ] On error:
     - Do not delete the Playbook.
     - Return a clear error message for display in the modal.

3. **Cascade correctness**
   - [ ] After deletion in tests, verify:
     - Playbook is absent.
     - Related Workflows/Activities/... are absent from the DB.

---

### 4.6. Documentation & Issue Management

1. **Update docs**
   - [ ] If needed, clarify the DELETE description in `playbooks-delete.feature` (if implementation requires it).
   - [ ] Update `docs/plans/PLAYBOOKS_CRUDV_IMPLEMENTATION_PLAN.md`, marking PHASE 5: DELETE as complete.

2. **GitHub Issue #31**
   - [ ] Following `.windsurf/rules/do-github-issues.md`, update the Issue:
     - Briefly describe the approach (modal + cascade + tests).
     - Include PR links and a list of covered PB-DELETE scenarios.

3. **Definition of Done**
   - [ ] Re-read `.windsurf/workflows/dev-5-check-dod.md`.
   - [ ] Verify that:
     - All PB-DELETE scenarios have tests.
     - All tests pass.
     - Logs are informative.
     - UI follows data-testid and tooltips rules.

---


## 5. Summary

This plan covers the implementation of Issue #31 (DELETE operation with confirmation modal and cascade) for **FOB-PLAYBOOKS-DELETE_PLAYBOOK-1**:

- Add **backend**: playbook_delete view + URL + cascade deletion.
- Add **frontend**: delete modal template + integration from list and detail views + accessible UX.
- Implement **full set of integration tests** for PB-DELETE-01..20.
- Update documentation and Issue #31 upon completion.

**Current status (increment 1):**

- Core **backend delete** implemented: `playbook_delete` view + URL, which deletes only owned-playbooks of the author and redirects to `playbook_list`.
- Added simple **POST-based Delete** controls (without modal):
  - On the detail page (`playbooks/detail.html`) for `can_edit`;
  - On the list page (`playbooks/list.html`) for `playbook.source == 'owned' and playbook.author == request.user`.
