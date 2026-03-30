# Activity: Finalize Feature

**Activity ID**: 15
**Order**: 7
**Phase**: Finalization
**Dependencies**: Predecessor: Activity 14 (Check Definition of Done)

## Description

Finalize Feature

## Guidance

## Purpose
Finalize feature with testing, validation, and deployment preparation.

## Steps

### 0. Run All Tests
Run all tests and ensure none are broken. If there are discrepancies between test expectations and implementation - ask user to clarify what takes precedence. Mark scenarios with "done" emoji and add "completed" tag.

### 1. Identify E2E Test
Identify Playwright E2E test for this feature/scenario. If there is none - ask user if they want to create one.

### 2. Run Development Server and Validate
**Auto-run:** Start the server: `python manage.py runserver`
Execute Playwright tests to ensure they pass.
Fix any issues found during testing.

### 3. Run Full Test Suite
**Auto-run:** Execute all unit tests, integration tests, and E2E tests.
Ensure no regressions were introduced.
Fix any failing tests.

### 4. Update Project Dependencies
Add any new packages to requirements.txt that were added during feature development.
Use `pip install <package>` to add new dependencies.
Ensure version constraints are appropriate.
Test that `pip install -r requirements.txt` works in a fresh venv.

### 5. Present Completed Work
Summarize implemented features and changes.
Show test results and coverage.
Demonstrate functionality if possible.

### 6. Final Commit
Check if there is a corresponding issue. Update the status with the latest changes and associate commit.
Commit all remaining changes using Angular-style commit messages.
Ensure commit message clearly describes the completed feature.

### 7. Handle Feature Branch
If on feature branch - ask user if they want to send a PR or merge into main.

### 8. Update Screen Flow Diagram
Update `docs/ux/2_dialogue-maps/screen-flow.drawio` to mark completed screens with green borders:
- Change `strokeColor=#1565c0` to `strokeColor=#22c55e` (green)
- Add `strokeWidth=3` if not present
- Add ✅ emoji prefix to screen labels
- This indicates feature completion per the diagram legend

### 9. Close and Mark Complete
Close issue if exists, review and mark all todos as "done" in the implementation plan, and update scenario and/or feature with "done" emoji.

## Rules to Follow

### I. 100% Test Pass Rate Required
Only 100% test pass rate can be reported as "success" or "complete". 92%, 95%, 99% are NOT success. Any failing tests must be fixed before declaring feature complete. Cannot mark features as "done" or "production-ready" with failing tests. Test failures must be resolved, not deferred or ignored.

Exception: Only if user explicitly approves deferring specific test scenarios can they be excluded from the count.

### II. Fix Tests Immediately
Failing tests are major problem - we don't start new development until we fix them.

### III. Commit Convention
Follow Angular convention with proper type, scope, subject, body, and footer.

## Success Criteria
- All tests passing (100% pass rate)
- Dependencies updated in requirements.txt
- Final commit made with clear message
- Issue updated and closed
- Implementation plan marked complete
- Feature file updated with completion markers

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
