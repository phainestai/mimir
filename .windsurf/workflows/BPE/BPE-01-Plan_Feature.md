# Activity: Plan Feature

**Activity ID**: 9
**Order**: 1
**Phase**: Planning
**Dependencies**: None

## Description

Plan Feature

## Guidance

## Purpose
Plan a new feature implementation by analyzing requirements, assessing codebase state, creating detailed implementation plan, and preparing for execution.

## Prerequisites
- Feature specification or idea for what needs to be built
- Access to codebase and documentation

## Steps

### Step 0: Reset and Prepare
Reset your task plan. If there was work in progress on another task, create a TODO.md file documenting what was being worked on, what was completed, what remains to be done, and any blockers or notes.

### Step 1: Understand Architecture
Read `docs/architecture/SAO.md` (if exists) to identify architectural patterns and principles relevant to this implementation. Use it to guide design decisions.

### Step 2: Understand User Journey
Check `docs/features/user_journey.md` (if exists) to understand what you're building and how it integrates with other parts of the system.

### Step 3: Analyze Feature Specification
Read the feature specification thoroughly. If none exists, propose creating one first.

**Follow BDD/Gherkin format:**
- One scenario = one user goal achievable in single session
- Each scenario should be 5-10 steps maximum
- Use concrete examples, not abstract descriptions
- Follow GIVEN-WHEN-THEN structure
- Scenarios must be independently executable
- If specification has >2 scenarios, work scenario-by-scenario
- If scenarios are >10 lines, suggest breaking them down

### Step 4: Assess Codebase State
Systematically review existing codebase:

a) **Identify reusable components:**
   - List components/views/services/models that can be reused/extended/integrated
   - Verify implementations actually exist (not just stubs with `NotImplementedError`)
   - Ask user: integrate with existing or replace?

b) **Check test coverage:**
   - For any reusable components without tests, add test creation to the plan
   - Maintain test coverage as you extend functionality

### Step 5: Clarification Questions
Ask clarification questions scenario-by-scenario: UI/UX details, data validation rules, error handling expectations, integration points, performance requirements.

If >5 questions total, create `FEAT_X.Y.Z_Clarifications.md` with all questions for user to answer in batch.

Update feature file and plan based on answers.

### Step 6: Create Implementation Plan

Write a step-by-step, todo-style, highly atomic implementation plan:

**Initial Setup:**
- Create and checkout new branch: `feature/feature-name`
- Enable "Plan mode" for planning phase

**For Each Scenario (in order):**

1. **Backend Implementation:**
   - Design models and data structures
   - Register new models with `/admin` module  
   - Create utility/helper functions
   - Implement services (business logic shared by MCP and Web UI)
   - Add repository methods for data access
   - Create Django Views (returning HTML templates)
   - Design URL patterns
   - Write tests: unit, integration (NO MOCKING!), view tests
   
2. **Frontend Implementation:**
   - Design Django templates with semantic HTML
   - Implement HTMX interactions for dynamic behavior
   - Create template partials for reusable components
   - Add graph visualizations with Graphviz (if needed)
   - Implement form handling and validation
   - Add semantic `data-testid` attributes for all interactive elements
   
3. **Testing:**
   Explicitly list all tests to be created:
   - Unit tests: Test individual functions/methods in isolation
   - Integration tests: Test complete workflows WITHOUT mocking
   - View tests: Test Django views return correct templates/status codes
   - Specify what each test validates

4. **Commit Strategy:**
   After every principal step commit with Angular convention message format.

### Step 7: Add Rule References
For each major step in the plan, add explicit reminders to review relevant rules.

### Step 8: No Time Estimates
Do NOT add hours/days to the plan - it's for AI to execute.

### Step 9: Submit for Approval
Present the complete plan to user for review and approval. Create `FEATURECODE_IMPLEMENTATION_PLAN.md` in `docs/plans/` directory.

Do not proceed to implementation without explicit approval.

### Step 10: GitHub Issue Management
If project has GitHub integration, search for existing issue or create new one with clear title, full scenario description, acceptance criteria, and link to implementation plan.

## Rules to Follow

### I. Test-First Development
Every function/method must begin with a test. Tests prove that your implementation works as intended. As long as tests are not passing, you cannot claim that the scenario/class/method is implemented.

- Review current implementation you are about to start testing to learn methods, properties, fields etc. you can use
- If actual implementation contradicts docstring - ask user what takes precedence
- Review design documentation for guidance on how things shall be implemented
- Write unit tests before implementing logic (do not write tests for NotImplementedError)
- Look into feature files to identify relevant scenarios
- Tests must test main success, border conditions, expected errors, handling of unexpected errors
- Start with method-level tests, then go to API, then to integration
- For integration: use real objects, connections, and data - no mocking
- Make the test fail, then implement logic to pass it
- Use pytest for running tests
- All tests must be placed in the `tests/` directory structure: unit tests in tests/unit/, integration tests in tests/integration/, API tests in tests/api/, E2E tests in tests/e2e/, service tests in tests/services/
- Never place test files in the root directory of the repository

### II. Small Increments
Work in method-by-method steps. Implement small vertical slices. After every change: write → run → test → evaluate → fix. No large PRs or 1000-line commits.

### III. Write Concise Methods
When designing new methods, ensure the top-level (public) method is concise—ideally 20–30 lines maximum. Move all supporting logic and details into well-named private (or inner/helper) methods. The top-level method should clearly express the main workflow, delegating specifics to lower-level helpers.

Each helper/private method should do one thing and have a clear, descriptive name. Avoid cramming complex logic into the top-level method; instead, encapsulate details in private helpers.

### IV. GitHub Issue Management
When creating an Issue, create a task for the person with very little knowledge of the domain. Create a very detailed to-do, giving the person very little space to misinterpret what needs to be done.

Add labels: Feature/Scenario/Enhancement/Bug/Refactoring/Infra and easy/medium/hard.
Start name with the Scenario prefix when available.
Transfer scenario content to description.
If there is plan in docs/plans - add plan contents to the description.
Before creating issue - check if issue with this prefix already exists.

### V. Commit Convention
Follow Angular convention:
```
<type>(<scope>): <subject>
<BLANK LINE>
<body - what changed>
<BLANK LINE>
<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

## Success Criteria
- Feature specification exists and is clear
- All clarification questions answered
- Codebase assessment complete
- Implementation plan is atomic and detailed
- All tests are explicitly listed with what they test
- Plan reviewed and approved by user
- GitHub issue created/updated
- Plan document saved to `docs/plans/`

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
