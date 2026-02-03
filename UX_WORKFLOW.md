# UX Workflow for Mimir

## Overview

This workflow defines the complete UX design-to-development process for Mimir, from initial user journey definition through feature implementation. It integrates with the existing `/dev-1-plan-feature` workflow and follows all project rules.

---

## Workflow Steps

### Step 1: Define User Journey

**Objective**: Establish the high-level user experience narrative with personas, user flows, and screen descriptions.

**Artifacts Created**:
- `docs/features/user_journey.md` - Complete user journey narrative

**Process (steps)**:

1. **Write User Journey Document**
   - Define personas (e.g., Mike Chen, Maria Rodriguez)
   - Map out Acts (Act 0: Authentication → Act 9: PIPs, etc.)
   - Describe user goals, motivations, and context for each Act
   - Identify key screens and user flows
   - Document system architecture notes (FOB vs HB, MCP integration)
   - Follow narrative structure: Context → Screen → Actions → Results
   
   **Template**:
   ```markdown
   ### Act X: [ENTITY] - Complete CRUDLF
   
   **Context**: [User situation and needs]
   
   **Pattern**: [Entity] follows the standard CRUDLF pattern with LIST+FIND as the entry point.
   
   #### Screen: FOB-[ENTITY]-LIST+FIND-1
   
   [User] clicks "[Entity]" in the main navigation. The [entity] list page appears:
   
   **Layout**:
   - **Header**: "[Entity]" with count badge (e.g., "[Entity] (3)")
   - **Top Actions**:
     - [Create New [Entity]] button (primary action, bold blue)
     - [Additional Action] button
   - **Search & Filter Section**:
     - Search box: "Find [entity]..." (searches [fields])
     - Filters: [Filter1], [Filter2], [Filter3]
     - [Clear Filters] button
   - **[Entity] Table** with columns:
     - [Column1] | [Column2] | [Column3] | Actions
     - Sort by any column
   - **Row Actions** (dropdown menu per [entity]):
     - [View] - Opens FOB-[ENTITY]-VIEW_[ENTITY]
     - [Edit] - Opens FOB-[ENTITY]-EDIT_[ENTITY]
     - [Delete] - Opens FOB-[ENTITY]-DELETE_[ENTITY] modal
     - [...More] - Additional actions
   - **Empty State** (if no [entity]):
     - Illustration: [Description]
     - "No [entity] yet"
     - "[Call to action message]"
     - [Action Buttons]
   - **Pagination**: Shows 20 per page with page controls
   
   **Example Data**:
   - "[Example 1]" | [Data] | [Data] | [Status]
   - "[Example 2]" | [Data] | [Data] | [Status]
   
   [User] sees [description of what user can do].
   ```
   
   **Good Example from Mimir** (`docs/features/user_journey.md:373-415`):
   ```markdown
   ### Act 2: PLAYBOOKS - Complete CRUDLF
   
   **Context**: After onboarding, Maria needs to manage playbooks - the top-level 
   container for methodologies. She can create her own, view downloaded ones, edit 
   them, and delete obsolete ones.
   
   **Pattern**: Playbook follows the standard CRUDLF pattern with LIST+FIND as the 
   entry point.
   
   #### Screen: FOB-PLAYBOOKS-LIST+FIND-1
   
   Maria clicks "Playbooks" in the main navigation. The playbooks list page appears 
   (this is the entry point for all playbook operations, marked with bold border in 
   flow diagrams):
   
   **Layout**:
   - **Header**: "Playbooks" with count badge (e.g., "Playbooks (3)")
   - **Top Actions**:
     - [Create New Playbook] button (primary action, bold blue)
     - [Import from JSON] button
     - [Sync with Homebase] button (if connected)
   - **Search & Filter Section**:
     - Search box: "Find playbooks..." (searches name, description, author)
     - Filters: Status (Active/Disabled), Source (Local/Downloaded/Owned), Category dropdown
     - [Clear Filters] button
   - **Playbooks Table** with columns:
     - Name | Description | Author | Version | Status | Last Modified | Actions
     - Sort by any column
   - **Row Actions** (dropdown menu per playbook):
     - [View] - Opens FOB-PLAYBOOKS-VIEW_PLAYBOOK
     - [Edit] - Opens FOB-PLAYBOOKS-EDIT_PLAYBOOK  
     - [Delete] - Opens FOB-PLAYBOOKS-DELETE_PLAYBOOK modal
     - [Export JSON] - (only for authored playbooks)
     - [...More] - Additional actions
   - **Empty State** (if no playbooks):
     - Illustration: Empty bookshelf
     - "No playbooks yet"
     - "Create your first playbook, download from Homebase, or import from JSON"
     - [Create Playbook] [Browse Families] [Import JSON] buttons
   - **Pagination**: Shows 20 per page with page controls
   
   **Example Data**:
   - "React Frontend Development" | Mike Chen | v1.2 | Active | Downloaded
   - "UX Research Methodology" | Maria Rodriguez | v2.1 | Active | Owned
   - "Design System Patterns" | Community | v1.0 | Disabled | Downloaded
   
   Maria sees her existing playbooks and can search/filter to find specific ones.
   ```

---

### Step 2: Define Information Architecture

**Objective**: Establish the design system foundation, layout patterns, and component standards.

**Artifacts Created**:
- `docs/ux/IA_guidelines.md` - Information architecture and design system

**Process (steps)**:

1. **Define Information Architecture**
   - Document design system foundation (Bootstrap 5.3+ base)
   - Define design tokens (colors, spacing, typography, shadows, borders)
   - Establish layout patterns (2-column, 3-column, grid, forms)
   - Define navigation structure (top navbar, breadcrumbs, tabs)
   - Document component patterns (cards, buttons, forms, modals)
   - Specify accessibility requirements
   - Define icon system (Font Awesome Pro)
   
   **Template**:
   ```markdown
   # [Project Name] Information Architecture Guidelines
   
   ## Design System Foundation
   
   ### 1. Design Tokens
   
   **Philosophy**: [Base framework choice and customization approach]
   
   #### Color Tokens
   ```css
   /* Primary palette */
   --[namespace]-primary: #[hex];
   --[namespace]-secondary: #[hex];
   
   /* Custom colors */
   --[namespace]-[color-name]: #[hex];
   ```
   
   #### Spacing Tokens
   ```css
   /* Base spacing scale */
   --[namespace]-spacer: [value];
   
   /* Custom spacing */
   --[namespace]-[element]-padding: [value];
   ```
   
   #### Typography Tokens
   ```css
   /* Font stacks */
   --[namespace]-font-sans-serif: [font stack];
   
   /* Font sizes */
   --[namespace]-[element]-font-size: [value];
   ```
   
   ### 2. Layout Patterns
   
   #### [Pattern Name] (e.g., Dashboard Grid)
   **Use Case**: [When to use this pattern]
   **Structure**: [HTML structure]
   **Responsive Behavior**: [How it adapts]
   
   ### 3. Navigation Design
   
   #### Top Navigation (Primary)
   **Structure**: [Navigation elements]
   **Active States**: [How to indicate current page]
   **Icons**: [Icon system and usage]
   
   ### 4. Component Patterns
   
   #### [Component Name]
   **Usage**: [When and how to use]
   **Variants**: [Different versions]
   **Accessibility**: [ARIA requirements]
   ```
   
   **Good Example from Mimir** (`docs/ux/IA_guidelines.md:1-180`):
   ```markdown
   # Mimir Information Architecture Guidelines
   
   ## Design System Foundation
   
   **Philosophy**: Leverage Bootstrap's conventions, utilities, and component patterns 
   as the first choice. Customize only when necessary for brand identity or specific 
   user experience requirements.
   
   ### 1. Design Tokens
   
   We extend Bootstrap's native CSS variables with Mimir-specific tokens. All tokens 
   follow Bootstrap's naming convention for consistency.
   
   #### Color Tokens
   
   **Base Bootstrap Colors** (use as-is):
   ```css
   /* Primary palette - Bootstrap defaults */
   --bs-primary: #0d6efd;
   --bs-secondary: #6c757d;
   --bs-success: #198754;
   ```
   
   **Mimir Custom Colors** (stat cards from dashboard):
   ```css
   /* Dashboard stat card colors */
   --mimir-purple: #5856d6;       /* Members online - purple card */
   --mimir-blue: #38a9f0;         /* Members online - blue card */
   --mimir-orange: #ffa726;       /* Members online - orange card */
   ```
   
   #### Spacing Tokens
   
   **Use Bootstrap's spacing scale** (0.25rem increments):
   ```css
   /* Bootstrap spacing multiplier: 1 = 0.25rem = 4px */
   --bs-spacer: 1rem; /* 16px base */
   
   /* Usage via utility classes */
   .m-3  /* margin: 1rem (16px) */
   .p-4  /* padding: 1.5rem (24px) */
   ```
   
   **Mimir Custom Spacing**:
   ```css
   /* Card spacing */
   --mimir-card-padding: 1.25rem;        /* 20px */
   --mimir-card-gap: 1.5rem;             /* 24px between cards */
   ```
   
   ### 2. Navigation Design
   
   #### Top Navigation (Primary)
   
   From dashboard screenshot:
   
   ```html
   <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
     <div class="container-fluid">
       <!-- Brand/Logo -->
       <a class="navbar-brand" href="/">Mimir</a>
       
       <!-- Main navigation links (left) -->
       <ul class="navbar-nav me-auto">
         <li class="nav-item">
           <a class="nav-link active" href="/dashboard">Dashboard</a>
         </li>
       </ul>
       
       <!-- Utility items (right) -->
       <ul class="navbar-nav ms-auto">
         <!-- Dark mode toggle -->
         <li class="nav-item">
           <button class="btn btn-link nav-link" id="darkModeToggle">
             <i class="fa-solid fa-moon"></i>
           </button>
         </li>
       </ul>
     </div>
   </nav>
   ```
   
   **Navigation States**:
   - **Active**: `.nav-link.active` (bold, primary color, lighter background)
     - Applied dynamically based on current `request.path`
     - Must include `aria-current="page"` attribute for accessibility
   ```

**How to Execute This Step**:

1. **Plan Before Executing** (plan-then-do):
   - Identify all affected documents, sections, and artifacts
   - Figure out what content you need and what's available to reference
   - Note what needs to be created from scratch
   - ALWAYS show the plan and ask for approval or refinements
   - Execute the plan, adjusting as necessary based on discoveries
   - After every major section, update the plan and explain next step

2. **Work Incrementally** (small-increments):
   - Work section-by-section (one Act at a time for user journey)
   - After every change: write → review → refine → evaluate
   - No massive documents created in one go
   - Build incrementally: personas → Act 0 → Act 1 → Act 2, etc.

**Deliverables**:
- ✅ Complete user journey with all Acts documented
- ✅ IA guidelines with design system specifications
- ✅ Navigation structure defined
- ✅ Layout patterns documented

---

### Step 3: Create Dialogue Maps (Screen Flows)

**Objective**: Visualize screen-to-screen flows and entity relationships.

**Artifacts Created**:
- `docs/ux/2_dialogue-maps/screen-flow.drawio` - Visual flow diagrams

**Process (steps)**:

1. **Create Domain Model Diagram**
   - Map core entities (Playbook, Workflow, Phase, Activity, Artifact, Role, Howto)
   - Show relationships between entities
   - Document cardinality and dependencies
   - Use color coding:
     - Blue (#4682B4): FOB screens
     - Green (#82b366): Homebase screens
     - Purple (#9370DB): MCP operations
     - Yellow (#fff2cc): PIP workflow
     - Pink (#f8cecc): Error states
   
   **Template**: Draw.io diagram with:
   - Entity boxes with names and colors
   - Relationship arrows with labels ("contains", "produces", "belongs to")
   - Cardinality notation (1:1, 1:N, N:M)
   - Legend explaining color coding
   
   **Good Example from Mimir** (`docs/ux/2_dialogue-maps/screen-flow.drawio` - Domain Model tab):
   - Shows 7 core entities: User, Family, Playbook, Workflow, Phase, Activity, Artifact, Role, Howto, Goal
   - Relationships clearly labeled: "User authors Playbook", "Playbook contains Workflow", "Activity produces Artifact"
   - Color-coded by concern: Blue (user/family), Green (playbook structure), Yellow (PIP system)
   - Clean layout with entities grouped logically

2. **Create MVP Flow Diagram**
   - Organize by Acts (horizontal swimlanes)
   - Show CRUDLF operations per entity:
     - **LIST+FIND** (bold border - entry point)
     - CREATE
     - VIEW
     - EDIT
     - DELETE
   - Use bold black arrows for main progression flow
   - Add screen IDs (e.g., `FOB-PLAYBOOKS-LIST+FIND-1`)
   - Show navigation paths between screens
   - Include modal/dialog states
   
   **Template**: Draw.io diagram with:
   - Horizontal swimlane per Act (ACT 0, ACT 2, ACT 3, etc.)
   - Screen boxes with IDs: `FOB-[ENTITY]-[OPERATION]-[VERSION]`
   - Bold border on LIST+FIND screens (entry points)
   - Arrows showing navigation flow
   - Color coding: Blue (FOB), Green (HB), Purple (MCP)
   
   **Good Example from Mimir** (`docs/ux/2_dialogue-maps/screen-flow.drawio` - MVP Flow tab):
   - ACT 2 swimlane shows complete Playbooks CRUDLF:
     - FOB-PLAYBOOKS-LIST+FIND-1 (bold border, entry point)
     - FOB-PLAYBOOKS-CREATE_PLAYBOOK-1
     - FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
     - FOB-PLAYBOOKS-EDIT_PLAYBOOK-1
     - FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 (modal)
   - Arrows show: LIST → CREATE → VIEW, LIST → VIEW → EDIT, LIST → DELETE
   - Clear visual hierarchy and flow

3. **Document Screen States**
   - Empty states
   - Loading states
   - Error states
   - Success confirmations
   - Validation feedback
   
   **Template**: Add state variations to flow diagram:
   - Dashed boxes for modal/dialog states
   - Pink boxes for error states
   - Annotations for loading/empty states
   
   **Good Example from Mimir**:
   - Empty state shown in LIST+FIND screens ("No playbooks yet" with illustration)
   - Delete confirmation modal (FOB-PLAYBOOKS-DELETE_PLAYBOOK-1) shown as dashed box
   - Error states documented in user journey (validation errors, connection failures)

**How to Execute This Step**:

1. **Plan Before Executing** (plan-then-do):
   - Identify all entities and relationships to diagram
   - Determine which Acts and screens need flow diagrams
   - Plan the layout and color coding scheme
   - Show the plan and get approval before creating diagrams

2. **Create Diagrams Element-by-Element**:
   - First, create an empty diagram file and save it
   - Then start adding edits one by one, saving after each edit
   - Build incrementally: entities → relationships → flows → states

3. **Visual Validation - Check with Human Eye**:
   Before finalizing, verify the diagram is visually clear:
   
   **Layout and Spacing**:
   - No overlapping components - all elements clearly separated
   - Not too crowded - adequate spacing between elements
   - Text doesn't cover arrows completely
   - Consistent spacing - uniform gaps between similar elements
   - Good alignment - elements align to grid or baseline
   
   **Flow and Navigation Clarity**:
   - Arrow direction is immediately obvious
   - Connection points are clear - arrows connect specific elements
   - Minimize crossing arrows that create confusion
   - Consistent arrow styles for similar connections
   - Maintain 40px minimum gaps between parallel arrow segments
   - Avoid more than 3 arrows meeting at any single point
   - Route error flows away from primary success paths
   - Ensure arrow labels don't overlap with other elements
   
   **Visual Hierarchy**:
   - Related elements visually grouped together
   - Similar elements have similar sizes
   - Sufficient color contrast between elements and backgrounds
   - Important elements are visually prominent
   
   **Legend and Documentation**:
   - Complete legend explaining all visual elements
   - Legend easily visible and doesn't interfere with content
   - All shapes, colors, and symbols are intuitive or explained
   - All text is large enough with sufficient contrast
   
   **Validation Tests**:
   - Zoom out test: understandable at 50% zoom
   - Fresh eyes test: can someone unfamiliar understand immediately?
   - Arrow clarity test: can you trace each flow path without confusion?
   - Primary user path is visually prominent and easy to follow

**Tools**:
- Draw.io for diagram creation

**Deliverables**:
- ✅ Domain model diagram
- ✅ Complete MVP flow with all Acts
- ✅ Screen state documentation
- ✅ Navigation flow clarity

---

### Step 4: Write Feature Files (BDD Scenarios)

**Objective**: Define testable acceptance criteria for each feature.

**Artifacts Created**:
- `docs/features/act-X-entity/*.feature` files

**Important**: Feature files are mapped to screens in the screen flow diagram (Step 2) via their screen IDs. Each feature file name corresponds to a screen box in the Draw.io diagram using the naming convention `FOB-[ENTITY]-[OPERATION]-[VERSION]` (e.g., `FOB-PLAYBOOKS-LIST+FIND-1`). This ensures traceability between visual flows and testable scenarios.

**Process**:

1. **Structure Feature Files by Entity**
   - Organize by Act and entity (e.g., `act-2-playbooks/`)
   - One file per CRUDLF operation:
     - `entity-list-find.feature`
     - `entity-create.feature`
     - `entity-view.feature`
     - `entity-edit.feature`
     - `entity-delete.feature`

2. **Write BDD Scenarios**
   - Follow Gherkin syntax (Given/When/Then)
   - Use specific scenario IDs (e.g., `PB-LIST-01`)
   - Define clear actors (Maria, Mike, etc.)
   - Specify exact UI elements and interactions
   - Include data tables for test data
   - Document expected outcomes
   - Add error/edge case scenarios
   
   **Template**:
   ```gherkin
   Feature: FOB-[ENTITY]-[OPERATION]-1 [Entity] [Operation Description]
     As a [user role] ([persona name])
     I want to [action]
     So that I can [benefit/goal]
   
     Background:
       Given [persona] is authenticated in FOB
       And [initial context/state]
   
     Scenario: [PREFIX]-[OPERATION]-01 [Main happy path scenario]
       Given [preconditions]
       And [test data setup with table if needed]:
         | column1 | column2 | column3 |
         | data1   | data2   | data3   |
       When [user action]
       Then [expected outcome]
       And [additional verification]
       And [UI state verification]
     
     Scenario: [PREFIX]-[OPERATION]-02 [Alternative path]
       Given [preconditions]
       When [different action]
       Then [different outcome]
     
     Scenario: [PREFIX]-[OPERATION]-03 [Error case]
       Given [preconditions]
       When [action that causes error]
       Then [error message displayed]
       And [system state unchanged]
     
     Scenario Outline: [PREFIX]-[OPERATION]-04 [Multiple variations]
       Given [preconditions]
       When [action with "<parameter>"]
       Then [outcome with "<result>"]
       
       Examples:
         | parameter | result |
         | value1    | result1 |
         | value2    | result2 |
   ```
   
   **Good Example from Mimir** (`docs/features/act-2-playbooks/playbooks-list-find.feature`):
   ```gherkin
   Feature: FOB-PLAYBOOKS-LIST+FIND-1 Playbooks List and Search
     As a methodology author (Maria)
     I want to view, search, and filter my playbooks
     So that I can quickly find and manage methodologies I need
   
     Background:
       Given Maria is authenticated in FOB
       And she is on the FOB Dashboard
   
     Scenario: PB-LIST-01 View playbooks list with existing playbooks
       Given Maria has 3 playbooks in her FOB:
         | name                        | author          | version | status   | source     |
         | React Frontend Development  | Mike Chen       | v1.2    | Active   | Downloaded |
         | UX Research Methodology     | Maria Rodriguez | v2.1    | Active   | Owned      |
         | Design System Patterns      | Community       | v1.0    | Disabled | Downloaded |
       When she clicks "Playbooks" in the main navigation
       Then she sees the playbooks list page
       And the header shows "Playbooks (3)"
       And she sees all 3 playbooks in the table
       And each playbook row shows: Name, Description, Author, Version, Status, Last Modified, Actions
   
     Scenario: PB-LIST-03 Search playbooks by name
       Given Maria is on the playbooks list page
       And she has playbooks including "React Frontend Development"
       When she enters "React" in the search box
       Then she sees only playbooks matching "React" in name, description, or author
       And "React Frontend Development" appears in the results
       And unmatched playbooks are hidden
   
     Scenario: PB-LIST-04 Search with no results
       Given Maria is on the playbooks list page
       When she enters "NonExistentPlaybook" in the search box
       Then she sees "No playbooks found matching 'NonExistentPlaybook'"
       And she sees a [Clear Search] button
       And the playbooks table is empty
   
     Scenario Outline: PB-LIST-06 Filter playbooks by source
       Given Maria is on the playbooks list page
       And she has playbooks from different sources
       When she selects "<source>" from the Source filter
       Then she sees only "<source>" playbooks
       And the filter badge shows "Source: <source>"
       
       Examples:
         | source     |
         | Local      |
         | Downloaded |
         | Owned      |
   ```

3. **Add Navbar Integration Scenarios**
   - Wire navbar links when feature block is complete
   - Document active state behavior
   - Specify icons and tooltips
   
   **Template**:
   ```gherkin
   # ============================================================
   # NAVBAR INTEGRATION - Wire when [Entity] block is complete
   # ============================================================
   
   Scenario: [PREFIX]-NAVBAR-01 [Entity] link appears in main navigation
     Given the [Entity] feature is fully implemented
     And [persona] is authenticated in FOB
     When [persona] views any page in FOB
     Then [persona] sees "[Entity]" link in the main navbar
     And the link has icon "[fa-icon-name]"
     And the link has tooltip "[Helpful description]"
   
   Scenario: [PREFIX]-NAVBAR-02 Navigate to [Entity] from any page
     Given [persona] is authenticated in FOB
     And [persona] is on any page in FOB
     When [persona] clicks "[Entity]" in the main navbar
     Then [persona] is redirected to FOB-[ENTITY]-LIST+FIND-1
     And the [Entity] nav link is highlighted as active
   ```
   
   **Good Example from Mimir** (`docs/features/act-2-playbooks/playbooks-list-find.feature:202-220`):
   ```gherkin
   # ============================================================
   # NAVBAR INTEGRATION - Wire when Playbooks block is complete
   # ============================================================
   
   Scenario: PB-NAVBAR-01 Playbooks link appears in main navigation
     Given the Playbooks feature is fully implemented
     And Maria is authenticated in FOB
     When she views any page in FOB
     Then she sees "Playbooks" link in the main navbar
     And the link has icon "fa-book-sparkles"
     And the link has tooltip "Browse and manage your engineering playbooks"
   
   Scenario: PB-NAVBAR-02 Navigate to Playbooks from any page
     Given Maria is authenticated in FOB
     And she is on any page in FOB
     When she clicks "Playbooks" in the main navbar
     Then she is redirected to FOB-PLAYBOOKS-LIST+FIND-1
     And the Playbooks nav link is highlighted as active
   ```

**How to Execute This Step**:

1. **Plan Before Executing** (plan-then-do):
   - Identify all CRUDLF operations needed for the entity
   - Determine which scenarios are critical vs. nice-to-have
   - Plan scenario IDs and prefixes
   - Show the plan and get approval before writing scenarios

2. **Work Incrementally** (small-increments):
   - Write one feature file at a time (list-find, then create, then view, etc.)
   - Within each file: Background → Happy path → Alternative paths → Error cases
   - After each scenario: review → refine → evaluate

3. **BDD Best Practices** (do-write-scenarios):
   
   **Always Start With Feature Specification**:
   - Define the user (role or persona)
   - State the goal (what user wants to achieve)
   - Describe the context (why it matters)
   - Pick an ID prefix (e.g., "Playbooks" → PB, "Workflows" → WF)
   
   **Be Specific - Who Does What, and Why**:
   - Identify the actor clearly (Maria, Mike, specific role)
   - Describe what they're trying to do in plain English, very specific
   - State why it matters for the workflow
   - Capture precise values - exact UI elements, data, expected results
   - Use scenario IDs like "PB-LIST-01"
   
   **Scenario Structure**:
   ```gherkin
   Scenario: <ID> <User goal>
     Given <initial system state or data>
     When <action is taken>
     Then <expected result or outcome>
   ```
   
   **Common Mistakes to Avoid**:
   - ❌ Vague actor roles ("user" instead of "Maria Rodriguez")
   - ❌ Missing context (why is the user doing this?)
   - ❌ Generic values ("some playbook" instead of "React Frontend Development")
   - ❌ Ambiguous outcomes ("should work" instead of exact behavior)
   
   **When in Doubt, Ask**:
   - Who is performing the action?
   - What are they trying to achieve?
   - Why is it important?
   - Which exact inputs are used?
   - What are the expected outputs, UI reactions, or system responses?

4. **UI Naming Conventions** (do-semantic-versioning-on-ui-elements):
   
   **Playwright Selector Hierarchy (use in scenarios)**:
   1. `data-testid` - Primary choice for all interactive elements
   2. `aria-label` / role - Secondary for semantic elements
   3. Text content - Only for static, stable content
   
   **Every Interactive Element Needs**:
   - `data-testid="[entity]-[action]-button"` format
   - `aria-label` describing the action
   - Bootstrap tooltip explaining what happens
   
   **Hierarchical Naming**:
   - Page level: `data-testid="[entity]-page"`
   - Components: `data-testid="[entity]-card"`, `data-testid="[entity]-list"`
   - Actions: `data-testid="create-[entity]-button"`, `data-testid="edit-[entity]-button"`
   - Forms: `data-testid="[entity]-name-input"`, `data-testid="[entity]-description-textarea"`
   - States: `data-testid="success-message"`, `data-testid="error-message"`

**Deliverables**:
- ✅ Complete feature files for all CRUDLF operations
- ✅ Navbar integration scenarios
- ✅ Error handling scenarios
- ✅ Edge case coverage

---

### Step 5: Create Mockups (Prototyped Screens)

**Objective**: Build functional prototypes with mocked data to validate UX before full implementation.

**Artifacts Created**:
- Django templates in `templates/entity/`
- Mock views in `entity/views.py`
- Mock data fixtures

**Important**: Embed the screen ID from Step 2 (screen flow diagram) as a comment at the top of each template and as a `data-screen-id` attribute on the main container. This enables quick discovery of screen implementations via grep (e.g., `grep -r "FOB-PLAYBOOKS-LIST+FIND-1" .`).

**Process**:

1. **Create Template Structure**
   - Extend `base.html` for consistent layout
   - Follow Bootstrap 5.3+ conventions
   - Implement responsive grid layouts
   - Add semantic HTML with ARIA attributes
   - Include `data-testid` attributes for testing
   - **Add screen ID comment and attribute for traceability**
   
   **Template**:
   ```django
   {# Screen ID: FOB-[ENTITY]-[OPERATION]-[VERSION] #}
   {# Maps to: docs/ux/2_dialogue-maps/screen-flow.drawio - [Act X] #}
   {# Feature: docs/features/act-X-entity/entity-operation.feature #}
   {% extends "base.html" %}
   
   {% block content %}
   <div class="container-fluid p-4" data-screen-id="FOB-[ENTITY]-[OPERATION]-[VERSION]">
     <!-- Breadcrumbs -->
     <nav aria-label="breadcrumb" class="mb-3">
       <ol class="breadcrumb">
         <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">Home</a></li>
         <li class="breadcrumb-item active" aria-current="page">[Entity]</li>
       </ol>
     </nav>
     
     <!-- Page Header -->
     <div class="d-flex justify-content-between align-items-center mb-4">
       <h1 class="h3 mb-0" data-testid="[entity]-page-title">[Entity] ({{ count }})</h1>
       <div>
         <button class="btn btn-primary" 
                 data-testid="create-[entity]-button"
                 data-bs-toggle="tooltip" 
                 title="Create new [entity]">
           <i class="fa-solid fa-plus me-2"></i>
           Create New [Entity]
         </button>
       </div>
     </div>
     
     <!-- Search & Filters -->
     <div class="card mb-3">
       <div class="card-body">
         <div class="row g-3">
           <div class="col-md-6">
             <input type="text" 
                    class="form-control" 
                    placeholder="Find [entity]..."
                    data-testid="[entity]-search-input">
           </div>
           <div class="col-md-3">
             <select class="form-select" data-testid="[entity]-filter-[field]">
               <option value="">All [Field]</option>
               <option value="option1">Option 1</option>
             </select>
           </div>
         </div>
       </div>
     </div>
     
     <!-- Main Content Table/Grid -->
     <div class="card">
       <div class="card-body">
         {% if items %}
           <table class="table table-hover" data-testid="[entity]-table">
             <thead>
               <tr>
                 <th>Column 1</th>
                 <th>Column 2</th>
                 <th>Actions</th>
               </tr>
             </thead>
             <tbody>
               {% for item in items %}
               <tr data-testid="[entity]-row" data-[entity]-id="{{ item.id }}">
                 <td>{{ item.field1 }}</td>
                 <td>{{ item.field2 }}</td>
                 <td>
                   <button class="btn btn-sm btn-outline-primary" 
                           data-testid="view-[entity]-button"
                           aria-label="View {{ item.name }}">
                     <i class="fa-solid fa-eye"></i>
                   </button>
                 </td>
               </tr>
               {% endfor %}
             </tbody>
           </table>
         {% else %}
           <!-- Empty State -->
           <div class="text-center py-5" data-testid="[entity]-empty-state">
             <i class="fa-solid fa-[icon] fa-4x text-muted mb-3"></i>
             <h4>No [entity] yet</h4>
             <p class="text-muted">[Call to action message]</p>
             <button class="btn btn-primary" data-testid="create-first-[entity]-button">
               <i class="fa-solid fa-plus me-2"></i>
               Create Your First [Entity]
             </button>
           </div>
         {% endif %}
       </div>
     </div>
   </div>
   {% endblock %}
   ```
   
   **Good Example from Mimir** (Playbooks list template pattern):
   - Extends `base.html` for consistent navbar/footer
   - Uses Bootstrap 5.3+ grid: `container-fluid`, `row`, `col-md-*`
   - Breadcrumbs with `aria-label="breadcrumb"`
   - Page header with count badge and primary action button
   - Search/filter card with responsive columns
   - Table with hover effect and `data-testid` attributes
   - Empty state with icon, message, and CTA button
   - All interactive elements have tooltips and ARIA labels
   - Consistent spacing using Bootstrap utilities (`mb-3`, `p-4`, etc.)

2. **Create Mock Views**
   ```django
   {% extends "base.html" %}
   
   {% block content %}
   <div class="container-fluid p-4">
     <!-- Breadcrumbs -->
     <nav aria-label="breadcrumb" class="mb-3">
       <ol class="breadcrumb">
         <li class="breadcrumb-item"><a href="{% url 'dashboard' %}">Home</a></li>
         <li class="breadcrumb-item active" aria-current="page">Playbooks</li>
       </ol>
     </nav>
     
     <!-- Page Header -->
     <div class="d-flex justify-content-between align-items-center mb-4">
       <h1 class="h3 mb-0">Playbooks ({{ playbooks|length }})</h1>
       <button class="btn btn-primary" data-testid="create-playbook-button">
         <i class="fa-solid fa-plus me-2"></i>
         Create New Playbook
       </button>
     </div>
     
     <!-- Playbooks Table -->
     <div class="card">
       <div class="card-body">
         <table class="table" data-testid="playbooks-table">
           <!-- Table content -->
         </table>
       </div>
     </div>
   </div>
   {% endblock %}
   ```

2. **Create Mock Views**
   - Return templates with hardcoded/fixture data
   - Implement basic navigation
   - Show all UI states (empty, loading, error, success)
   - Add placeholder interactions
   
   **Example View**:
   ```python
   def playbooks_list(request):
       """Mock view for playbooks list - returns template with fixture data."""
       mock_playbooks = [
           {
               'id': 1,
               'name': 'React Frontend Development',
               'author': 'Mike Chen',
               'version': 'v1.2',
               'status': 'Active',
           },
           # More mock data...
       ]
       return render(request, 'playbooks/list.html', {
           'playbooks': mock_playbooks
       })
   ```

3. **Follow IA Guidelines**
   - Use Bootstrap components and utilities
   - Apply design tokens consistently
   - Implement proper spacing (Bootstrap scale)
   - Add Font Awesome Pro icons
   - Include Bootstrap tooltips on all actions
   - Ensure responsive behavior
   - Follow accessibility guidelines

4. **Add UI Element Attributes**
   - `data-testid` for Playwright testing
   - `aria-label` for accessibility
   - `data-state` for component states
   - Semantic HTML roles
   
   **Example**:
   ```html
   <button 
     class="btn btn-primary"
     data-testid="save-playbook-button"
     data-state="ready"
     aria-label="Save playbook changes"
     data-bs-toggle="tooltip"
     title="Save changes to the playbook">
     <i class="fa-solid fa-save me-2"></i>
     Save
   </button>
   ```

**How to Execute This Step**:

1. **Plan Before Executing** (plan-then-do):
   - Identify all screens needed for the entity (LIST+FIND, CREATE, VIEW, EDIT, DELETE)
   - Determine which UI states to show (empty, loading, error, success)
   - Plan the template structure and mock data
   - Show the plan and get approval before creating templates

2. **Work Incrementally** (small-increments):
   - Create one template at a time (list, then create form, then detail view, etc.)
   - For each template: structure → mock data → styling → interactions
   - After each template: review → refine → evaluate

3. **Skeletons First** (do-skeletons-first):
   - Start with HTML structure and Bootstrap classes
   - Add `data-testid` attributes and ARIA labels
   - Add placeholder content and mock data
   - Then add Font Awesome icons
   - Finally add tooltips and interactions
   - Use `raise NotImplementedError()` in mock views for unfinished parts

4. **Design System Compliance** (IA_guidelines.md):
   - Use Bootstrap 5.3+ components and utilities exclusively
   - Apply design tokens consistently (spacing, colors, typography)
   - Follow responsive grid patterns (`container-fluid`, `row`, `col-md-*`)
   - Use Bootstrap card components for content containers
   - Apply proper spacing with utility classes (`mb-3`, `p-4`, `gap-3`)
   - Ensure all forms use Bootstrap form components

5. **UI Element Requirements**:
   
   **Every Interactive Element Must Have**:
   - `data-testid="[entity]-[action]-button"` for Playwright testing
   - `aria-label="[Clear description]"` for accessibility
   - Font Awesome Pro icon (semantically appropriate)
   - Bootstrap tooltip with `data-bs-toggle="tooltip"` and `title`
   
   **Tooltip Content Rules**:
   - **Active buttons**: Explain what will happen when clicked
     - Example: "Create a new playbook"
     - Example: "Delete this playbook permanently"
   - **Disabled buttons**: Explain why disabled and how to enable
     - Example: "Fill in required fields on the form (indicated in bold)"
     - Example: "Connect to Homebase in Settings to enable sync"
   
   **Icon Selection**:
   - If no icon specified in requirements, propose 3 options
   - Use Font Awesome Pro classes: `fa-solid`, `fa-regular`, `fa-light`
   - Icons must be semantically appropriate for the action
   
   **Example Button**:
   ```html
   <button class="btn btn-primary" 
           data-testid="create-playbook-button"
           aria-label="Create new playbook"
           data-bs-toggle="tooltip" 
           data-bs-placement="top"
           title="Create a new playbook from scratch">
     <i class="fa-solid fa-plus me-2"></i>
     Create New Playbook
   </button>
   ```

6. **Hierarchical Naming** (do-semantic-versioning-on-ui-elements):
   - Page containers: `data-testid="[entity]-page"`
   - Feature components: `data-testid="[entity]-list"`, `data-testid="[entity]-card"`
   - Action buttons: `data-testid="create-[entity]-button"`, `data-testid="edit-[entity]-button"`
   - Form inputs: `data-testid="[entity]-name-input"`, `data-testid="[entity]-description-textarea"`
   - Status elements: `data-testid="success-message"`, `data-testid="error-message"`
   - Table rows: `data-testid="[entity]-row"` with `data-[entity]-id="{{ item.id }}"`

7. **Component State Visibility**:
   - Add `data-state` attributes for testability:
     - `data-state="loading"` / `data-state="loaded"`
     - `data-state="submitting"` / `data-state="ready"`
     - `data-valid="true"` / `data-valid="false"`

**Deliverables**:
- ✅ Functional mockup templates for all screens
- ✅ Mock views returning templates
- ✅ All UI states represented
- ✅ Proper accessibility attributes
- ✅ Testable with `data-testid` attributes

---

### Step 6: Feed into Feature Implementation Workflow

**Objective**: Transition from UX design to full backend implementation.

**Process**:

1. **Invoke `/dev-1-plan-feature` Workflow**
   - Reference the feature file created in Step 3
   - Use mockups from Step 4 as UI reference
   - Follow the complete planning workflow
   
   **Workflow Steps** (from `/dev-1-plan-feature`):
   - Read `docs/architecture/SAO.md` for architecture guidance
   - Review `docs/features/user_journey.md` for context
   - Read feature specification (`.feature` files)
   - Assess current codebase state
   - Ask clarification questions
   - Create atomic implementation plan
   - Submit plan for approval
   - Create/update GitHub issue

2. **Implementation Plan Structure**
   - Start feature branch
   - Implement backend (per `dev-2-implement-backend.md`):
     - Models and data design
     - Register models with Django admin
     - Utility/helper functions
     - Services (business logic)
     - Repository methods
     - Django views (replace mock views)
     - URL patterns
     - Tests (unit, integration, view tests)
   - Implement frontend (per `dev-3-implement-frontend.md`):
     - Enhance Django templates (replace mocks)
     - Add HTMX interactions
     - Create template partials
     - Add Graphviz visualizations (if needed)
     - Implement form handling with validation
     - Ensure semantic `data-testid` attributes
   - Commit after each major step
   - Update GitHub issue with progress

3. **Replace Mocks with Real Implementation**
   - Convert mock views to real views with database queries
   - Replace fixture data with actual model queries
   - Implement form processing and validation
   - Add error handling
   - Maintain all UI attributes from mockups

4. **Testing Strategy**
   - Write tests BEFORE implementation
   - Create unit tests for models and services
   - Create integration tests (NO MOCKING)
   - Create view tests for Django views
   - Create E2E tests with Playwright (using `data-testid` selectors)
   - Ensure 100% test pass rate

**How to Execute This Step**:

1. **Plan Before Executing** (plan-then-do):
   - Identify all affected models, views, services, templates
   - Figure out methods, properties, enums needed and what's available
   - Note what needs to be created from scratch
   - Create atomic implementation plan covering all components
   - ALWAYS show the plan and ask for approval
   - After every major step: update plan, show status, explain next step

2. **Work Incrementally** (small-increments):
   - Implement method-by-method, not entire classes at once
   - Small vertical slices: model → service → view → template → test
   - After every change: write → run → test → evaluate → fix
   - No large PRs or 1000-line commits
   - Commit after each completed component

3. **Test-First Development** (do-test-first):
   
   **Core Principle**: Tests prove implementation works. Until tests pass, feature is not implemented.
   
   **Process**:
   - Review current implementation to learn available methods/properties
   - Review design documentation for implementation guidance
   - Look into feature files (`.feature`) to identify relevant scenarios
   - Write unit tests BEFORE implementing logic
   - Don't write tests for `raise NotImplementedError` - write actual checks
   - Tests must cover: main success, border conditions, expected errors, unexpected errors
   - Start with method-level tests, then API, then integration
   - Make test fail, then implement logic to pass it
   - Use pytest for running tests
   - Do not mock unless absolutely necessary
   
   **Test Organization**:
   - All tests in `tests/` directory structure:
     - Unit tests: `tests/unit/`
     - Integration tests: `tests/integration/`
     - API tests: `tests/api/`
     - End-to-end tests: `tests/e2e/`
     - Service tests: `tests/services/`
   - **Never place test files in repository root**

4. **Test Success Criteria**:
   - **Only 100% test pass rate = success**
   - 92%, 95%, 99% are NOT success
   - Any failing tests must be fixed before declaring feature complete
   - Cannot mark features as "done" or "production-ready" with failing tests
   - Test failures must be resolved, not deferred or ignored
   - Exception: Only if user explicitly approves deferring specific scenarios

5. **Continuous Testing**:
   - Run `pytest tests/` continuously during development
   - Monitor `tests.log` for errors
   - Fix errors automatically as detected
   - Use file watchers or interval-based execution
   - Parse test results in real-time

6. **GitHub Issue Management**:
   - **Before creating issues**: Always list existing issues first
   - Search for matching scenario prefixes (e.g., PB-LIST-01)
   - Check if scenarios already exist before creating new ones
   - Avoid duplicates - reference existing issues instead
   - Link commits to issues
   - Update issue status as work progresses

7. **Commit Conventions** (Angular style):
   ```
   <type>(<scope>): <subject>
   <BLANK LINE>
   <body - what changed>
   <BLANK LINE>
   <footer>
   ```
   
   Types: feat, fix, docs, style, refactor, test, chore
   Example: `feat(playbooks): add list and search functionality`

**Deliverables**:
- ✅ Complete implementation plan approved
- ✅ GitHub issue created/updated
- ✅ Feature branch created
- ✅ Backend fully implemented
- ✅ Frontend fully implemented
- ✅ All tests passing (100%)
- ✅ Feature merged to main

---

## Core Principles Applied Throughout

These principles apply to **every step** of the UX workflow:

### 1. Plan-Then-Do Pattern
- **Always** create a plan before executing
- Identify affected components and what's available vs. what needs creation
- Show plan to user and get approval/refinements
- Execute plan, adjusting based on discoveries
- After every major step: update plan, show status, explain next step

### 2. Small Increments
- Work in small, manageable pieces (section-by-section, file-by-file, method-by-method)
- Implement small vertical slices
- After every change: write → run → test → evaluate → fix
- No massive documents, large PRs, or 1000-line commits

### 3. Test-First Approach
- Write tests before implementation (for Steps 4-5)
- Tests prove implementation works
- Only 100% test pass rate = success
- All tests in `tests/` directory structure

### 4. Visual Validation
- Check diagrams with human eye (Step 2)
- Verify layout, spacing, flow clarity, visual hierarchy
- Run validation tests: zoom out, fresh eyes, arrow clarity

### 5. Specificity and Clarity
- Be specific in scenarios: exact actors, actions, data, outcomes
- Use precise naming: `data-testid`, `aria-label`, semantic IDs
- Document everything: tooltips, accessibility, state visibility

---

## Quality Gates

### Before Moving to Next Step

**Step 1 → Step 2**:
- [ ] User journey complete with all Acts
- [ ] IA guidelines documented
- [ ] Design system tokens defined
- [ ] Navigation structure clear

**Step 2 → Step 3**:
- [ ] Domain model diagram complete
- [ ] MVP flow diagram shows all screens
- [ ] Screen states documented
- [ ] Flow validated visually (human eye check)

**Step 3 → Step 4**:
- [ ] All CRUDLF feature files written
- [ ] Scenarios follow BDD best practices
- [ ] Navbar integration scenarios added
- [ ] Error/edge cases covered

**Step 4 → Step 5**:
- [ ] All mockup templates created
- [ ] Mock views functional
- [ ] All UI states represented
- [ ] Accessibility attributes present
- [ ] `data-testid` attributes added
- [ ] Design system compliance verified

**Step 5 Completion**:
- [ ] Implementation plan approved
- [ ] All backend code implemented
- [ ] All frontend code implemented
- [ ] 100% test pass rate achieved
- [ ] GitHub issue updated/closed
- [ ] Feature merged to main

---

## Example: Complete Workflow for Playbooks Feature

### Steps 1-2: User Journey & IA
- ✅ Documented Act 2: PLAYBOOKS in `user_journey.md`
- ✅ Defined CRUDLF pattern in IA guidelines
- ✅ Specified Bootstrap-based design system

### Step 3: Dialogue Maps
- ✅ Created domain model showing Playbook relationships
- ✅ Created MVP flow for Act 2 with all screens:
  - FOB-PLAYBOOKS-LIST+FIND-1 (entry point)
  - FOB-PLAYBOOKS-CREATE_PLAYBOOK-1
  - FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
  - FOB-PLAYBOOKS-EDIT_PLAYBOOK-1
  - FOB-PLAYBOOKS-DELETE_PLAYBOOK-1

### Step 4: Feature Files
- ✅ `act-2-playbooks/playbooks-list-find.feature`
- ✅ `act-2-playbooks/playbooks-create.feature`
- ✅ `act-2-playbooks/playbooks-view.feature`
- ✅ `act-2-playbooks/playbooks-edit.feature`
- ✅ `act-2-playbooks/playbooks-delete.feature`
- ✅ `act-2-playbooks/playbooks-versioning.feature`

### Step 5: Mockups
- ✅ `templates/playbooks/list.html` with mock data
- ✅ `templates/playbooks/create.html` with form
- ✅ `templates/playbooks/detail.html` with tabs
- ✅ Mock views in `playbooks/views.py`

### Step 6: Implementation
- ✅ Invoked `/dev-1-plan-feature` with playbooks feature
- ✅ Implemented Playbook model
- ✅ Created PlaybookService for business logic
- ✅ Replaced mock views with real views
- ✅ Added HTMX interactions
- ✅ Wrote comprehensive tests
- ✅ Achieved 100% test pass rate

---

## Tools & Artifacts Reference

### Documentation
- `docs/features/user_journey.md` - User journey narrative
- `docs/ux/IA_guidelines.md` - Information architecture
- `docs/ux/2_dialogue-maps/screen-flow.drawio` - Visual flows
- `docs/features/act-X-entity/*.feature` - BDD scenarios

### Templates
- `templates/base.html` - Base layout
- `templates/entity/*.html` - Entity-specific templates

### Rules
- `.windsurf/rules/` - Project-specific rules
- `.cursor/rules/` - Additional rules

### Workflows
- `.windsurf/workflows/dev-1-plan-feature.md` - Feature planning
- `.windsurf/workflows/dev-2-implement-backend.md` - Backend implementation
- `.windsurf/workflows/dev-3-implement-frontend.md` - Frontend implementation

---

## Success Criteria

### UX-Complete Checklist

A feature is considered **UX-complete** when:

1. ✅ User journey documented with clear narrative (Step 1)
2. ✅ IA guidelines updated with design patterns (Step 1)
3. ✅ Domain model diagram created and validated (Step 2)
4. ✅ MVP flow diagram shows all screens and states (Step 2)
5. ✅ Diagrams pass visual validation tests (Step 2)
6. ✅ All CRUDLF scenarios written in BDD format (Step 3)
7. ✅ Navbar integration scenarios added (Step 3)
8. ✅ Error and edge case scenarios covered (Step 3)
9. ✅ Mockup templates created following IA guidelines (Step 4)
10. ✅ All accessibility attributes present (Step 4)
11. ✅ All `data-testid` attributes added (Step 4)
12. ✅ Font Awesome icons and Bootstrap tooltips on all buttons (Step 4)
13. ✅ Mock views returning templates with fixture data (Step 4)
14. ✅ All UI states represented (empty, loading, error, success) (Step 4)
15. ✅ Design system compliance verified (Step 4)
16. ✅ Ready for `/dev-1-plan-feature` workflow (Step 5)

### Implementation-Complete Checklist

A feature is considered **implementation-complete** when:

1. ✅ Implementation plan created and approved (Step 5)
2. ✅ GitHub issue created/updated (Step 5)
3. ✅ Feature branch created (Step 5)
4. ✅ Tests written BEFORE implementation (Step 5)
5. ✅ Backend fully implemented (models, services, views) (Step 5)
6. ✅ Frontend fully implemented (templates, HTMX) (Step 5)
7. ✅ Mockups replaced with real implementation (Step 5)
8. ✅ Form validation and error handling added (Step 5)
9. ✅ **100% test pass rate achieved** (Step 5)
10. ✅ All UI attributes maintained from mockups (Step 5)
11. ✅ Commits follow Angular convention (Step 5)
12. ✅ GitHub issue updated with progress (Step 5)
13. ✅ Feature merged to main (Step 5)
14. ✅ Navbar link activated (if applicable) (Step 5)

---

## Important Notes

### What NOT to Do
- ❌ Do NOT create .MD files unless explicitly part of task definition, workflow, or rule
- ❌ Do NOT skip the planning step - always show plan and get approval
- ❌ Do NOT create massive documents or commits in one go
- ❌ Do NOT declare features complete with failing tests
- ❌ Do NOT mock in integration tests
- ❌ Do NOT skip accessibility attributes or tooltips
- ❌ Do NOT use vague naming or generic values in scenarios

### What TO Do
- ✅ Follow plan-then-do at every step
- ✅ Work incrementally - small vertical slices
- ✅ Write tests before implementation
- ✅ Maintain 100% test pass rate
- ✅ Use existing patterns and conventions
- ✅ Prioritize accessibility (ARIA, semantic HTML, keyboard navigation)
- ✅ Ensure testability (`data-testid` on all interactive elements)
- ✅ Validate diagrams visually with human eye
- ✅ Add Font Awesome Pro icons and Bootstrap tooltips to all buttons
- ✅ Check for existing GitHub issues before creating new ones
- ✅ Commit after each major step with Angular convention
