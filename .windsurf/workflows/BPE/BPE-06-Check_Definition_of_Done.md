# Activity: Check Definition of Done

**Activity ID**: 14
**Order**: 6
**Phase**: Validation
**Dependencies**: Predecessor: Activity 13 (Implement Journey Certification Tests)

## Description

Check Definition of Done

## Guidance

## Purpose
Validate that feature/story implementation complies with all project rules and standards by examining current state and outputs.

## Core Development Rules Checklist

### Test-First Development
- [ ] Every function/method has corresponding test(s)
- [ ] Feature files in `docs/features/` exist and comply with scenarios
- [ ] Tests use pytest framework
- [ ] Mocking is minimal

### Continuous Testing
- [ ] All tests are runnable via `pytest tests/`
- [ ] Tests are pytest compatible with proper fixtures
- [ ] `tests.log` file exists and contains test output

### Concise Methods
- [ ] Top-level (public) methods are 20-30 lines maximum
- [ ] Supporting logic is in well-named private methods
- [ ] Helper methods have single, focused responsibilities
- [ ] Method names are descriptive and clear

## Code Quality Rules Checklist

### Import Management
- [ ] All imports are at module level
- [ ] No imports inside functions/methods
- [ ] Dependencies are properly declared

### Informative Logging
- [ ] Logging statements exist in methods and properties
- [ ] Log levels are appropriate (DEBUG, INFO, WARNING, ERROR)
- [ ] Error conditions have logging statements

## Testing and Quality Assurance Checklist

### Integration Test Standards
- [ ] Integration tests in `tests/integration/` exist
- [ ] Integration tests avoid mocking
- [ ] Real dependencies are used in integration scenarios

### Commit Conventions
- [ ] Recent commit messages follow Angular conventional format
- [ ] Commits are atomic and focused
- [ ] Breaking changes are documented in commit messages

## UI and Frontend Rules Checklist

### Django Views + HTMX
- [ ] No DRF views exist for new web UI features
- [ ] Django views return HTML templates
- [ ] HTMX attributes used for dynamic interactions
- [ ] Services layer is shared between MCP and Web UI

### Semantic Naming
- [ ] All interactive elements have `data-testid` attributes
- [ ] Naming follows kebab-case convention
- [ ] Form inputs have proper name and id attributes

## Documentation Checklist

### Scenario Writing
- [ ] BDD scenarios exist for features
- [ ] Feature files are well-structured
- [ ] Scenarios cover edge cases and error conditions
- [ ] Review GUI - do scenarios match behavior, fields, URLs, design rules? Report inconsistencies to user

### TODO Management
- [ ] TODO comments exist for incomplete implementations
- [ ] TODO items have clear descriptions
- [ ] TODOs in dependencies can be ignored

### Document Updates
- [ ] Review code: new packages, patterns, approaches worth documenting?
- [ ] Review conversation: need to update feature files/corrections?
- [ ] Review modus operandi against workflows and rules - can we improve?

## Final Validation Checklist

### Overall Quality Check
- [ ] Feature meets acceptance criteria
- [ ] Code is production-ready
- [ ] Documentation exists and is accurate

### Integration Validation
- [ ] Feature integrates with existing system
- [ ] No breaking changes introduced
- [ ] Dependencies properly declared in requirements.txt

### Deployment Readiness
- [ ] Database migrations exist if needed
- [ ] Environment variables are documented
- [ ] Configuration changes are documented

### Cleanup
- [ ] Remove temporary files like debug_*.py
- [ ] Scan file structure for stray misplaced files
- [ ] Remove *.log files from repository

## Actions
All checkboxes must be completed before considering the story "Done". Any deviations must be presented to user. If user says "collect for cleanup but defer" - create a Backlog item in GitHub as Issue with "deferred" tag. Otherwise resolve deviations as directed by user, commit following Angular convention, and send Pull Request.

## Success Criteria
- All checklist items verified
- No deviations or all approved by user
- Code production-ready
- Ready for PR

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
