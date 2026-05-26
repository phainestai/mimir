# Mimir User Journey

## Personas

**Mike Chen** - FOB Administrator  
Senior developer at a tech community. Maintains shared playbooks for common development patterns. Has the **Administrator** role in FOB, which grants Accept/Reject PIP permissions — he reviews Galdr's recommendations and applies final decisions on proposed Playbook changes.

**Maria Rodriguez** - UX Consultant  
Runs an independent UX consulting practice. Needs to organize her personal workflows, collaborate with her team, and leverage community methodologies.

---

---

## System Architecture Note

See [System Architecture Overview](../architecture/SAO.md) for full component details, domain model, MCP configuration, and design principles.

---

## ⚠️ Critical Architectural Principle

**Playbooks Are STATIC Reference Material (Like a Book)**

- **Mimir playbooks** = Documentation and guidance ONLY
  - Show activity structure, descriptions, best practices
  - NO work item tracking, NO status indicators, NO checkmarks
  - Think of them as reference books or documentation wiki pages

- **Work item tracking** = Happens ONLY in external systems
  - GitHub Issues, Jira Tickets, Atlassian boards
  - Status, progress, assignments managed there
  - Actual work execution tracked there

- **AI/MCP integration** = Cross-references between the two
  - Reads static playbook from Mimir: "Activity 1: Setup Project - install dependencies, configure environment"
  - Reads live status from GitHub: "Issue #47: Setup React project - Status: Closed"
  - Provides combined context: "According to the playbook, Activity 1 covers setup. GitHub shows issue #47 for this work is complete."

**Example**:
- **FOB displays**: "Activity 1: Setup Project" with rich Markdown guidance (static)
- **GitHub displays**: "Issue #47: Setup React project structure - Closed on Nov 15" (live tracking)
- **AI combines**: "Per the React Frontend Development playbook, you need to set up the project. GitHub issue #47 shows this work is complete."

**This separation ensures**:
- Playbooks remain reusable across projects and teams
- Work tracking stays in familiar developer tools
- No duplicate tracking systems

---

## Journey: From Discovery to Contribution

### Act 0: System Entry & Authentication

**Context**: Users access Mimir entirely through the FOB web application at `http://localhost:8000`. There is no separate central server — everything lives in FOB.

#### Screen: FOB Login Page
Any user navigates to the FOB login page:
- Email field
- Password field
- "Remember me" checkbox
- "Forgot password?" link
- "Sign up" link (→ Registration, covered in Act 1)
- "Login" button

#### Screen: FOB Dashboard (Returning User)
After login, the user lands on the FOB dashboard (see Act 1.5 for full layout). Maria sees her recent playbooks and quick actions.

#### Screen: FOB Admin Dashboard (Administrator View)
Mike (FOB Administrator) logs in and additionally sees:
- **Admin** link in the top navigation → opens Django Admin
- In Django Admin, Mike has access to:
  - Users and roles
  - Teams
  - PIPs (pending Galdr review and pending Admin decision)
  - Notifications
- MCP server status indicator: ✓ Running

**Note**: Django Admin is the interface for Administrator-level operations (PIP Accept/Reject). Regular users do not see the Admin link.

#### Error Path: FOB Startup Failed
If the FOB web server is unreachable:
- Browser shows connection error
- User restarts the FOB process: `python manage.py runserver 8000`
- MCP server restart: configured separately via FastMCP

---

### Act 0.1: The Foundation (Mike's Setup)

**Context**: Mike wants to share his React development methodology with the community. He authors the playbook directly in FOB.

#### Screen: FOB Dashboard
Mike logs into FOB. He sees the main dashboard with his playbooks and team management tools.

#### Screen: FOB Create Playbook Wizard
Mike clicks "Create New Playbook" and enters:
- **Name**: "React Frontend Development"
- **Description**: "Component architecture, state management, and testing patterns"
- **Category**: Development
- **Status**: Draft (starts at v0.1)

#### Screen: FOB Playbook Editor
Mike structures his playbook using the FOB editor:
- Adds Workflows: "Setup", "Component Development", "Testing"
- Adds Activities: "Setup Project", "Create Components", "Implement State Management"
- Adds Artifacts: "Component Library", "State Diagram", "Test Suite"
- Links Activities with upstream/downstream artifact relationships

#### Screen: Playbook visibility (FOB today)
Mike keeps visibility **Private (only me)** on the playbook wizard. In the current FOB build, only the owner can access and edit playbooks via the GUI and MCP. **Family** and **Local only** are stored as metadata for future Homebase sync; they do not grant access to other users yet. Team assignment and public/team visibility are planned (Act 11 / Homebase); REST API group sharing exists outside the GUI.

#### Action: Release Playbook
Mike is satisfied with the playbook and clicks **[Release]** on the playbook detail page:
- Confirmation modal: "Release 'React Frontend Development' as v1.0?"
- "Once released, direct edits are locked. Changes require a PIP."
- Mike confirms → playbook status changes to **Released v1.0**

**Result**: The playbook is now available to all members of the Usability team as a stable v1.0 reference. Future changes require PIPs reviewed by Galdr and approved by an Administrator.

---

### Act 1: Maria's Onboarding

**Context**: Maria heard about Mimir and wants to try it for her UX practice. She registers directly in the FOB application.

#### Screen: FOB Registration Page
Maria navigates to the FOB registration page at `http://localhost:8000/register`:
- Email: dpetelin@gmail.com
- Password: (creates secure password)
- First name / Last name: Maria Rodriguez
- ☐ **"I agree to the [Terms of Service] and [Privacy Policy]"** (required checkbox; links open in new tab)
- Clicks **[Create account]**

The [Create account] button is **disabled** until the checkbox is ticked. If Maria submits without ticking (e.g. via keyboard), a validation error appears: *"You must accept the Terms of Service to register."*

`accepted_tos_at` (timestamp) is recorded on the user record at the moment of registration.

#### Screen: FOB Email Verification

After registration Maria is redirected to the **login page** with the message:
> Account created. Please check your inbox and verify your email before logging in.

She cannot log in until she verifies. If she tries:
- Login is refused with: *"Please verify your email address before logging in. Check your inbox for a verification link."*
- A **[Re-send verification email]** link is shown inline on the login form.

She clicks the link in the email → her address is marked **Verified** → she is redirected to the login page with a success message and can now authenticate normally.

#### Screen: FOB Registration Success — Authentication Token
After email verification, Maria sees her account details page in FOB:
- **Congratulations!** Your Mimir account is active.
- **Your Authentication Token** (copy button):
  ```
  Token: mimir_a8f3d9e2b1c4567890abcdef12345678
  ```
- **Important**: Save this token securely. You'll need it to configure the Mimir MCP server in your IDE.
- Options:
  - "Copy Token to Clipboard"
  - "Regenerate Token" (invalidates old token)
  - "Go to Dashboard"

**Note**: This token authenticates the FastMCP server to the FOB REST API. The MCP server is a container that talks to FOB via `BASE_URL/api/…` — it cannot work without a reachable FOB. Set `BASE_URL` to either your **local FOB** (`http://localhost:8000`) or a **hosted FOB** (`https://mimir.featurefactory.io`).

#### Screen: FOB MCP Configuration Guide
FOB shows a one-time guide for configuring the MCP server in the user's IDE.

**Important**: The MCP server is a container that calls FOB's REST API — it requires a live, reachable FOB at all times. Choose one:
- **Local FOB** — FOB running on your machine or inside your network (default)
- **Hosted FOB** — connect to `https://mimir.featurefactory.io` (no local install needed)

```json
{
  "mimir": {
    "command": "python",
    "args": ["-m", "mcp_integration.server"],
    "env": {
      "BASE_URL": "http://localhost:8000",
      "TOKEN": "mimir_a8f3d9e2b1c4567890abcdef12345678"
    }
  }
}
```

- `BASE_URL` is pre-filled with `http://localhost:8000` (local FOB). Change to `https://mimir.featurefactory.io` if using the hosted instance.
- [Copy Config Snippet] button
- "Paste this into your Cursor or Windsurf MCP settings"
- [Go to Dashboard] button

#### Screen: FOB External MCP Configuration
Maria **separately configures external MCP servers in Windsurf/Cursor**:
- GitHub MCP for work item management
- (Optional: Jira MCP, GitLab MCP, etc.)

**Result**: Maria now has a working FOB account with her MCP server configured to talk to FOB via `BASE_URL` + `TOKEN`.

---

### Act 1.5: FOB Navigation Structure

**Context**: Understanding the persistent navigation and UI structure of FOB.

#### Screen: FOB Main Interface Layout
Maria's FOB web GUI (http://localhost:8000) has a consistent layout:

**Top Navigation Bar** (persistent across all screens):
- **Logo**: "Mimir" (links to Dashboard)
- **Search**: Global search bar (playbooks, teams, activities)
- **Navigation Menu**:
  - Home (Dashboard)
  - Playbooks
  - Workflows, Phases, Activities, Artifacts, Agents, Skills, Rules
  - PIPs (with **status-change count pill** — see below)
- **Notifications**: Bell icon with badge count (unread notifications) — *when implemented*
- **User Menu**: Click **your username** in the top-right to open a dropdown:
  - **[View Profile]** → **FOB-PROFILE-1** (`/auth/user/profile/`) — name, email, API token (show / copy / **regenerate** with password), PIPs you created, playbooks you own, teams you belong to
  - **[Log Out]**

Staff users may also use dashboard shortcuts (e.g. Django admin) where applicable; primary account + token management for everyone is **FOB-PROFILE-1**.

#### Screen: FOB-PROFILE-1 (My Profile)

Maria opens **View Profile** from the username menu.

- **Account card**:
  - First name, last name, username (Django user fields).
  - **Email** — shown alongside a status pill:
    - ✅ **Verified** (green badge) — email has been confirmed.
    - ⚠️ **Not verified** (orange badge) — email unconfirmed; a **[Re-send verification email]** button appears inline. An unverified email means the account cannot log in — this badge should only be visible if a staff admin is viewing the profile on behalf of the user, or immediately after an email change before the session terminates.
  - **[Edit]** button in the card header → `FOB-PROFILE-EDIT-1`.
- **API token (MCP / REST)**: DRF `Token` used as `Authorization: Token <key>`; [Show] / [Copy]; **Regenerate token** requires **current password** and invalidates the previous key immediately.
- **My PIPs**: PIPs where Maria is the submitter (`created_by`), with links to each PIP.
- **My playbooks**: Playbooks Maria authors (`author`), with links to each playbook.
- **My Teams**: Teams Maria belongs to (as admin or member), showing role badge, member count, and a [View] link to each team detail page. Teams where she is admin show a crown icon. Hidden teams are included.

#### Email Verification Flow

**Registration:**
1. FOB sends a verification email with a one-click link (`/auth/user/verify-email/<token>/`).
2. Maria cannot log in until the link is clicked — the login view refuses unverified credentials.
3. The login page shows a **[Re-send verification email]** link for users who are blocked.
4. Clicking the link marks the email **Verified** → redirects to login with success message.
5. Token expires after **24 hours**; an expired link shows an error with a fresh [Re-send] option.
6. Staff / superuser accounts are automatically considered verified and are never blocked.

**Changing email** (`FOB-PROFILE-EDIT-1`):
- The edit form shows an orange warning banner **client-side** as soon as the email field is changed:
  > ⚠️ Changing your email will require re-verification. You will be logged out and your API token invalidated until the new address is verified.
- On **[Save changes]**:
  1. New email is saved.
  2. Active session is terminated immediately.
  3. API (DRF) token is invalidated — MCP sessions using that token stop working.
  4. Verification email is sent to the new address.
  5. Maria is redirected to the login page: *"Email updated. Please verify your new address before logging in again."*
- After verifying the new email, a **new API token is generated automatically** on first login.
- Staff / superuser accounts skip all of the above — no logout, no token invalidation, email saved immediately.

---

**Left Sidebar** (contextual, shown on detail pages):
- Quick links based on current context
- Recently viewed playbooks
- Active playbook indicator

**PIPs Tab — Count Pill Behaviour**:
The **PIPs** nav item shows an orange count pill (e.g., `PIPs 3`) whenever there are PIPs whose status changed since the user last:
- Visited the FOB-PIP-LIST screen, **or**
- Called the `list_pips` MCP tool

The pill counts PIPs where `status_changed_since_last_view = true`. It resets to zero (pill disappears) as soon as the list is opened or `list_pips` is called. This applies per-user — Maria's pill tracks her own PIPs; Mike's Admin view tracks all PIPs.

---

#### Screen: FOB Dashboard (Main Landing Page)

**Context**: The dashboard is the main landing page after login. It provides quick access to Maria's work and shows what she's been using recently.

**Layout**:

**Section 1: My Playbooks** (Top section)
- Grid/list of 5 most recently accessed playbooks
- Each playbook card shows:
  - Name and description
  - Version badge
  - Status badge (Draft/Released)
  - Last accessed timestamp (e.g., "Opened 2 hours ago")
- [View All Playbooks] link → FOB-PLAYBOOKS-LIST+FIND-1
- Empty state: "No playbooks yet" with [Create Playbook] button

**Section 2: Recently Used** (Middle section - informer style)
- **Purpose**: Show what Maria has been actively working with and how often
- **NOT an audit trail**: Does not track all user actions, only tracks access/usage for quick navigation
- Table showing:
  - **Item Name** | **Type** | **Times Used** | **Last Used** | **Quick Action**
- Item types: Playbook, Workflow, Activity
- Sorted by: Last Used (most recent first)
- Shows: Last 10 items
- **Times Used**: Simple counter incremented each time item is viewed/accessed
  - Playbook: Viewed detail page
  - Workflow: Viewed detail page
  - Activity: Viewed detail page
- **Quick Action**: [View] button → navigates to item's detail page
- Example rows:
  - "React Frontend Development" | Playbook | 15 times | 2 hours ago | [View]
  - "Component Development" | Workflow | 8 times | 3 hours ago | [View]
  - "Setup Project" | Activity | 12 times | 5 hours ago | [View]
- Empty state: "No recent usage yet"

**⚠️ IMPORTANT**: This is NOT a comprehensive audit log or activity tracking system. It only tracks views/access for the purpose of showing recently used items as quick navigation shortcuts. It does not track create/update/delete operations.

**Section 3: Quick Actions** (Bottom section)
- Three prominent action buttons:
  - [+ New Playbook] → FOB-PLAYBOOKS-CREATE_PLAYBOOK-1
    - Icon: fa-plus-circle
    - Tooltip: "Create a new playbook from scratch"
  - [Import Playbook] → Import feature (disabled in MVP)
    - Icon: fa-file-import
    - Tooltip: "Import playbook from JSON file (coming soon)"
    - Disabled state with gray styling
  - [Browse Teams] → FOB-TEAMS-LIST
    - Icon: fa-users
    - Tooltip: "Browse teams and their shared playbooks"

Maria uses this dashboard to quickly resume her work and navigate to frequently accessed items.

#### Screen: FOB Notification Center
Maria clicks the bell icon (badge shows "3"):
- Dropdown panel appears:
  - "New user wants to join UX team" (12 min ago) [View Request]
  - "Your PIP 'Add Accessibility Audit' has been reviewed" (2 hours ago) [View PIP]
  - "Tom joined Usability team" (1 day ago) [Dismiss]
- "Mark all as read" button
- "View all notifications" link → Full notification page

#### Screen: FOB Notifications (Full View)
Clicking "View all notifications" opens dedicated page:
- Tabs: "All", "Pending Actions", "Updates", "Mentions"
- Filterable list of all notifications
- Each notification has:
  - Icon (team, playbook, sync, error, etc.)
  - Message
  - Timestamp
  - Action buttons (context-specific)
  - Dismiss button

#### Screen: FOB Global Search
Maria types "React" in search bar:
- Live dropdown suggestions appear:
  - **Playbooks** (2):
    - React Frontend Development (Usability)
    - React Testing Patterns (Archived)
  - **Activities** (5):
    - Setup React Project
    - Create React Components
    - ...
  - **Teams** (0)
- "See all results" link → Full search results page

#### Screen: FOB Search Results
Full search page with filters:
- **Left sidebar filters**:
  - Type: Playbooks, Activities, Artifacts, Goals, Teams
  - Status: Active, Disabled, Archived
  - Source: Local, Owned
- **Results list** with relevance ranking
- **Empty state**: "No results found" with suggestions

---

### Act 2: PLAYBOOKS - Complete CRUDLF

**Context**: After onboarding, Maria needs to manage playbooks - the top-level container for methodologies. She can create her own, view downloaded ones, edit them, and delete obsolete ones.

**Pattern**: Playbook follows the standard CRUDLF pattern with LIST+FIND as the entry point.

#### Screen: FOB-PLAYBOOKS-LIST+FIND-1

Maria clicks "Playbooks" in the main navigation. The playbooks list page appears (this is the entry point for all playbook operations, marked with bold border in flow diagrams):

**Layout** (MVP card grid):
- **Header**: "Playbooks" with [Create New Playbook] primary action
- **Card grid**: Owned playbooks and other authors' **public, non-draft** playbooks in one section
  - Owned cards: Delete + View actions
  - Other authors' cards: "by {username}" subtitle, View only (read-only)
- **Empty State** (only when the user has zero owned playbooks AND no visible public playbooks from others):
  - "No playbooks yet"
  - [Create New Playbook] button
- Draft playbooks with Public visibility remain **owner-only** until released

**Example Data**:
- "React Frontend Development" | Mike Chen | v1.2 | Active | Downloaded
- "UX Research Methodology" | Maria Rodriguez | v2.1 | Active | Owned
- "Design System Patterns" | Community | v1.0 | Disabled | Downloaded

Maria sees her existing playbooks and can search/filter to find specific ones.

---

#### Screen: FOB-PLAYBOOKS-CREATE_PLAYBOOK-1

Maria clicks [Create New Playbook]. The creation wizard opens:

**Wizard Step 1: Basic Information**
- **Name**: Text input (required)
  - Example: "Product Discovery Framework"
  - Validation: Unique name, 3-100 characters
- **Description**: Textarea (required)
  - Example: "Comprehensive methodology for discovering and validating product opportunities"
  - Validation: 10-500 characters
- **Category**: Dropdown (required)
  - Options: Design, Development, Research, Management, Product, Other
- **Tags**: Multi-select/token input (optional)
  - Example: "product management, discovery, validation, user research"
- **Visibility**: Dropdown
  - Private (only me) — default; owner-only access in FOB/MCP
  - Family (coming soon) — disabled; metadata for future Homebase
  - Local only (coming soon) — disabled; metadata for future Homebase
  - Help text explains owner-only access today
- [Cancel] [Next: Add Workflows →] buttons

**Wizard Step 2: Add Workflows** (optional first workflow)
- "You can add workflows now or later"
- [Skip for Now] [Add First Workflow] buttons
- If Add First Workflow clicked:
  - Quick workflow creation inline
  - Workflow name and description fields
  - [Add Workflow] [Cancel] buttons

**Wizard Step 3: Publishing Settings**
- **Status**: Radio buttons
  - ○ Draft (v0.1 — fully editable via GUI and MCP)
  - ○ Released (v1.0 — read-only; changes via PIP only)
  - Note: "Draft playbooks can be edited directly. Released playbooks require PIP (Process Improvement Proposal) for any changes."
- **Initial Version**: Auto-set based on status (Draft → v0.1, Released → v1.0)
- Review summary of playbook being created
- [Cancel] [Create Playbook] buttons

**Success Flow**:
- Playbook created in local FOB
- Success notification: "Playbook 'Product Discovery Framework' created successfully"
- Redirects to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 for the new playbook
- New playbook appears in FOB-PLAYBOOKS-LIST+FIND-1

**Error Handling**:
- Duplicate name: "A playbook with this name already exists. Please choose a different name."
- Validation errors highlighted inline with red borders and error messages
- [Fix Errors] to return to form

---

#### Playbook Versioning & Lifecycle System

**Context**: Mimir implements automatic versioning to track playbook evolution while enforcing change control for released methodologies.

**Versioning Rules**:

1. **Draft Status** (v0.1, v0.2, v0.3, ...):
   - New playbooks start at **v0.1**
   - Every change automatically increments version by 0.1
   - Changes include:
     - Editing playbook metadata (name, description, etc.)
     - Adding/editing/deleting workflows
     - Adding/editing/deleting activities in workflows
     - Adding/editing/deleting any related entities
   - Draft playbooks are **fully editable** via GUI and MCP
   - Version increments happen automatically (transparent to user)

2. **Released Status** (v1.0, v2.0, v3.0, ...):
   - When user releases a draft playbook → version becomes **v1.0**
   - Released playbooks are **read-only** in GUI and MCP
   - Any attempt to edit shows message:
     - "This playbook is Released and cannot be edited directly. Please submit a PIP (Process Improvement Proposal) to make changes."
   - Changes can only be made via **PIP workflow** (ACT 9)
   - Each approved PIP increments major version (1.0 → 2.0 → 3.0)

**Example Lifecycle**:
```
Create Playbook (Draft)     → v0.1
Add 2 workflows              → v0.2  (auto-increment)
Edit playbook description    → v0.3  (auto-increment)
Add 5 activities to workflow → v0.4  (auto-increment)
Edit activity #3             → v0.5  (auto-increment)
[User clicks "Release"]      → v1.0  (status: Released)
[Try to edit - blocked]      → Error: "Use PIP to change"
Submit PIP with changes      → PIP workflow
PIP approved and merged      → v2.0  (new released version)
```

**Status Badge Colors**:
- Draft: Yellow/Warning (editable, evolving)
- Released: Blue/Primary (stable, controlled)
- Active: Green/Success (deprecated status, use Draft or Released)
- Disabled: Gray/Secondary (archived, not in use)

**User Actions**:
- **Release Draft**: Draft v0.x → Released v1.0
  - One-way operation (cannot revert to draft)
  - Accessible from playbook detail page
  - Confirmation modal explains implications
- **Submit PIP**: Only way to change Released playbooks
  - Creates PIP proposal with proposed changes
  - Requires review/approval workflow
  - See ACT 9: PIPs for complete flow

**MCP Integration**:
- MCP can read both draft and released playbooks
- MCP can suggest edits only to draft playbooks
- For released playbooks, MCP suggests creating PIP instead
- MCP tools check playbook status before allowing mutations

Maria now understands that her new draft playbooks will auto-version as she works on them, and once released, they become controlled artifacts that require formal change proposals.

---

#### Screen: FOB-PLAYBOOKS-VIEW_PLAYBOOK-1

Maria clicks [View] on "React Frontend Development" from the list. The detail view opens:

**Layout**:
- **Header**:
  - Playbook name: "React Frontend Development" (h1)
  - Version badge: v1.0 (or v0.3 if draft)
  - Status badge: Draft (yellow) / Released (blue) / Disabled (gray)
  - Author: Mike Chen (Usability team)
  - Last modified: 2 weeks ago
- **Top Actions**:
  - [Edit] button (if draft and owned - disabled for released with tooltip: "Released playbooks require PIP")
  - [Release] button (if draft and owned - promotes to v1.0 released status)
  - [Submit PIP] button (if released and owned - opens PIP creation flow)
  - [Delete] button (if owned)
  - [Export JSON] button (if authored)
  - [Duplicate] button
  - [Disable]/[Enable] toggle
  - [...More] dropdown

**Tabs**:
1. **Overview Tab** (default):
   - **Description**: Full playbook description
   - **Quick Stats Card**:
     - Workflows: 3
     - Phases: 8 (optional, may show "N/A" if workflow doesn't use phases)
     - Activities: 24
     - Artifacts: 12
     - Agents: 5
     - Skills: 24
     - Goals: 6 (note: Goal deferred to v2.1, shows "Coming soon")
   - **Metadata**:
     - Category: Development
     - Tags: react, frontend, component-architecture
     - Created: 3 months ago
     - Source: Downloaded from Usability team
   - **Workflows Section**:
     - List of workflows in this playbook
     - Each workflow shows: Name, Description, Activity count
     - [View Workflow] link for each → jumps to ACT 3: WORKFLOWS

2. **Workflows Tab**:
   - Full list of workflows with filtering
   - Workflow dependency visualization (if any)
   - [Add Workflow] button (if editable)

3. **History Tab**:
   - Version timeline: v1.0, v1.1, v1.2
   - Each version shows:
     - Version number, Date, Author, Change summary
     - [View This Version] [Compare with Current] buttons
   - PIP history (proposals that led to new versions)

4. **Settings Tab** (if owned):
   - Visibility settings
   - Publishing settings
   - Sharing options
   - [Transfer Ownership] button

**Version Comparison View** (if clicked from History):
- Split-pane diff viewer
- Left: Selected version | Right: Current version
- Highlighting: Added (green), Removed (red), Modified (yellow)
- Shows differences in workflows, activities, artifacts

**Navigation**:
- [Back to Playbooks List] link at top
- Breadcrumb: Playbooks > React Frontend Development > Overview

Maria can explore the complete playbook structure, drill into workflows, view version history, and understand the methodology comprehensively.

---

#### Screen: FOB-PLAYBOOKS-EDIT_PLAYBOOK-1

Maria clicks [Edit] on her "Product Discovery Framework" draft playbook (v0.3). The edit form opens:

**Access Control**:
- **Draft playbooks**: Fully editable, version auto-increments on save
- **Released playbooks**: Edit button disabled/blocked
  - Shows error: "This playbook is Released and cannot be edited directly. Please submit a PIP (Process Improvement Proposal) to make changes."
  - Redirects to playbook detail page

**Form Layout** (similar to CREATE wizard but single page):
- **Basic Information Section**:
  - Name: Pre-populated, editable (triggers version increment)
  - Description: Pre-populated, editable textarea (triggers version increment)
  - Category: Pre-populated dropdown (triggers version increment)
  - Tags: Pre-populated multi-select (triggers version increment)
  - Visibility: Pre-populated dropdown (Private default; Family/Local disabled with help text)
    - Note: Owner-only access in FOB/MCP; visibility does not share playbooks with others today

- **Status Section**:
  - Current Version: v0.3 (read-only, shows current version)
  - Current Status: Draft / Released / Disabled radio buttons
  - Note: "Draft playbooks auto-increment version on every save (v0.3 → v0.4). Use Release button to publish as v1.0."

- **Workflows Section**:
  - List of current workflows
  - [Edit Workflow] [Remove Workflow] buttons per workflow
  - [Add New Workflow] button
  - Note: "Removing a workflow will delete all its phases, activities, and downstream entities"

**Validation**:
- Same validation as CREATE
- Additional check: Cannot remove last workflow if playbook is Active
- Warn if removing workflows that have work items linked (via external MCP)

**Actions**:
- [Cancel] - Returns to VIEW without saving, confirmation if changes made
- [Save Changes] - Saves and auto-increments version for draft playbooks
  - Draft: v0.3 → v0.4 automatically
  - Note: Only available for draft playbooks

**Success Flow**:
- Changes saved
- Version automatically incremented (v0.3 → v0.4)
- Success notification: "Playbook updated successfully (v0.4)"
- If visibility changed: Value saved as metadata only (no sharing impact in FOB today)
- Returns to FOB-PLAYBOOKS-VIEW_PLAYBOOK-1
- Updated data and new version visible in FOB-PLAYBOOKS-LIST+FIND-1

**Permission Handling**:
- Downloaded playbooks (not owned): Edit button disabled or opens read-only view
- Tooltip: "You cannot edit playbooks from other authors. Create a local copy or submit a PIP."
- [Create Local Copy] button offered as alternative

---

#### Screen: FOB-PLAYBOOKS-DELETE_PLAYBOOK-1 (Confirmation Modal)

Maria clicks [Delete] on an old "Test Playbook 123" she no longer needs. A confirmation modal appears:

**Modal Layout**:
- **Title**: "Delete Playbook?"
- **Icon**: Warning triangle (red)
- **Playbook Info**:
  - Name: "Test Playbook 123"
  - Version: v1.0
  - Author: Maria Rodriguez
  - Created: 2 weeks ago

**Impact Statement**:
"This will permanently delete:"
- ✗ 2 Workflows
- ✗ 0 Phases (if phases exist, shows count)
- ✗ 8 Activities
- ✗ 5 Artifacts
- ✗ 3 Agents
- ✗ 8 Skills
- ✗ All version history

**Warnings**:
- "This action cannot be undone"
- If playbook has external work items linked:
  - Warning: "This playbook has 3 GitHub issues linked. Work items will remain but lose playbook context."
- If visibility is family or local (metadata label only):
  - Note: Label is informational; no other FOB users lose access on delete

**Confirmation**:
- Checkbox: ☐ "I understand this will permanently delete the playbook and all related content"
- Text input: "Type the playbook name to confirm" (must match exactly)
  - Placeholder: "Test Playbook 123"

**Actions**:
- [Cancel] - Closes modal, no changes
- [Delete Playbook] - Disabled until checkbox checked and name entered correctly
  - Button turns red when enabled
  - Final confirmation: "Are you absolutely sure?" (if high-impact)

**Success Flow**:
- Playbook and all related entities deleted from local graph
- Success notification: "Playbook 'Test Playbook 123' deleted"
- Modal closes
- Returns to FOB-PLAYBOOKS-LIST+FIND-1
- Deleted playbook no longer in list
- Team/family sharing notifications: not implemented in FOB

**Special Cases**:
- **Cannot Delete Downloaded Playbooks**: Modal shows:
  - "You cannot delete playbooks from other authors"
  - "Instead, you can Disable this playbook to hide it from your views"
  - [Disable Playbook] [Cancel] buttons
- **Delete Draft**: Simpler confirmation, less dramatic warnings

Maria confirms deletion by typing the name and checking the box. The playbook and all its contents are permanently removed.

---

**Act 2 Summary**: Maria can now perform complete CRUDLF operations on Playbooks:
- ✅ **LIST+FIND**: Browse, search, and filter all playbooks
- ✅ **CREATE**: Create new playbooks with wizard guidance
- ✅ **VIEW**: Explore playbook details, workflows, and history
- ✅ **EDIT**: Update playbook metadata, workflows, and settings
- ✅ **DELETE**: Remove playbooks with full impact warnings

**Navigation Flow**: Dashboard → Playbooks LIST+FIND (entry point) → Individual operations (CREATE/VIEW/EDIT/DELETE) → Back to LIST+FIND

**Next**: Maria proceeds to manage Workflows within her playbooks (ACT 3).

---

### Act 3: WORKFLOWS - Complete CRUDLF

**Context**: Within a playbook, Maria needs to manage workflows - the execution sequences that contain activities. A playbook typically has multiple workflows representing different paths or phases of the methodology.

**Pattern**: Workflow follows standard CRUDLF with LIST+FIND as entry point. Workflows are always scoped within a parent playbook.

**Important Note**: Workflows MAY optionally contain Phases for grouping Activities, but Phases are not required. See Act 4 for Phase management.

#### Screen: FOB-WORKFLOWS-LIST+FIND-1

From FOB-PLAYBOOKS-VIEW_PLAYBOOK-1, Maria clicks on the "Workflows" tab or [View Workflows] button. The workflows list appears:

**Layout**:
- **Breadcrumb**: Playbooks > React Frontend Development > Workflows
- **Header**: "Workflows in React Frontend Development" with count (e.g., "3 workflows")
- **Context Banner**: Shows parent playbook info (name, version, author)
- **Top Actions**:
  - [Create New Workflow] button (primary)
  - [Import Workflow from Template] button
  - [Reorder Workflows] button (drag-and-drop mode)
- **Search & Filter**:
  - Search: "Find workflows..."
  - Filter by: Has Phases (Yes/No), Activity count range, Status
- **Workflows Table**:
  - Name | Description | Activities | Phases | Order | Actions
  - Drag handle for reordering
- **Row Actions**:
  - [View] → FOB-WORKFLOWS-VIEW_WORKFLOW
  - [Edit] → FOB-WORKFLOWS-EDIT_WORKFLOW
  - [Delete] → FOB-WORKFLOWS-DELETE_WORKFLOW modal
  - [Duplicate] 
  - [...More]
- **Empty State**:
  - "No workflows yet"
  - "Create your first workflow to organize activities"
  - [Create Workflow] button

**Example Data**:
- "Component Development" | 8 Activities | 2 Phases | Order: 1
- "State Management Setup" | 6 Activities | 0 Phases | Order: 2
- "Testing & Documentation" | 10 Activities | 3 Phases | Order: 3

**Visualization Toggle**:
- [List View] / [Flow View] toggle
- Flow View shows workflows as connected boxes with activity counts

Maria sees all workflows in the playbook and their structure.

---

#### Screen: FOB-WORKFLOWS-CREATE_WORKFLOW-1

Maria clicks [Create New Workflow]. Creation form opens:

**Form Fields**:
- **Name**: Text input (required)
  - Example: "Design System Integration"
  - Validation: Unique within playbook, 3-100 chars
- **Description**: Textarea (required)
  - Example: "Integrate design tokens and component library into the React application"
  - 10-500 chars
- **Parent Playbook**: Read-only display (already scoped)
  - Shows: "React Frontend Development v1.2"
- **Order/Sequence**: Number input or "Add to end" checkbox
  - Default: Adds after last workflow
  - Can specify position: 1, 2, 3, etc.
- **Phase Organization**: Radio buttons
  - ○ No phases (Activities directly in workflow)
  - ○ Use phases (Group activities into phases)
  - Tooltip: "Phases are optional. Use them to organize activities into logical groups or stages."
- **Initial Setup** (collapsible section):
  - "Add first activity now?" checkbox
  - If checked: Quick activity creation fields appear
  - [Skip - Add Activities Later] option

**Actions**:
- [Cancel] [Create Workflow]

**Success Flow**:
- Workflow created within playbook
- Success notification: "Workflow 'Design System Integration' created in React Frontend Development"
- Redirects to FOB-WORKFLOWS-VIEW_WORKFLOW-1
- New workflow appears in FOB-WORKFLOWS-LIST+FIND-1 at specified order

**Validation**:
- Duplicate name within playbook: Error message
- If "Use phases" selected: Note shown that phases can be added in edit view

---

#### Screen: FOB-WORKFLOWS-VIEW_WORKFLOW-1

Maria clicks [View] on "Component Development" workflow. Detail view opens:

**Layout**:
- **Breadcrumb**: Playbooks > React Frontend Development > Workflows > Component Development
- **Header**:
  - Workflow name: "Component Development"
  - Parent playbook badge with link
  - Order badge: "#1 of 3"
- **Top Actions**:
  - [Edit Workflow]
  - [Delete Workflow]
  - [Duplicate]
  - [Reorder] (move up/down)
  - [...More]

**Tabs**:

1. **Overview Tab**:
   - **Description**: Full workflow description
   - **Stats**:
     - Activities: 8
     - Phases: 2 (or "No phases used")
     - Estimated effort: Calculated from activities
   - **Phase Summary** (if using phases):
     - Phase 1: "Foundation" (3 activities)
     - Phase 2: "Implementation" (5 activities)
     - Note: "Phases are optional groupings. Activities can be reorganized without phases."
   - **Activities Summary**:
     - List of activities in execution order
     - Shows dependencies (upstream/downstream)
     - [View Full Activity List] → jumps to Activities tab

2. **Activities Tab**:
   - Full activity list with filtering
   - Grouped by phase (if using phases) or flat list
   - Activity dependency graph visualization
   - [Add Activity] button → jumps to ACT 5: ACTIVITIES-CREATE
   - [Manage Phases] button (if using phases) → jumps to ACT 4: PHASES

3. **Dependencies Tab**:
   - Visual DAG (Directed Acyclic Graph) of activity dependencies
   - Shows upstream/downstream relationships
   - Identifies critical path
   - Warns about circular dependencies (validation error)

4. **Structure Tab** (if using phases):
   - Phase breakdown with activities per phase
   - [Reorganize Phases] button
   - [Convert to Non-Phased] button (warning: removes phase groupings)

**Navigation**:
- [Back to Workflows] → returns to LIST+FIND
- [View Parent Playbook] → FOB-PLAYBOOKS-VIEW_PLAYBOOK
- Quick links to activities and phases

Maria can explore the workflow structure, see activity organization, and understand execution flow.

---

#### Screen: FOB-WORKFLOWS-EDIT_WORKFLOW-1

Maria clicks [Edit Workflow]. Edit form opens:

**Form Layout**:
- **Basic Info Section**:
  - Name: Editable
  - Description: Editable textarea
  - Order: Number input with [Move Up] [Move Down] buttons
  
- **Phase Organization Section**:
  - Current: "Uses 2 phases" or "No phases"
  - [Change Phase Structure] button opens modal:
    - Convert to phased/non-phased
    - Warning: "This will reorganize activities"
    - [Cancel] [Convert] buttons

- **Activities Section**:
  - List of activities in this workflow
  - Drag-and-drop reordering
  - [Add Activity] [Remove Activity] per row
  - Shows activity dependencies
  - Warning if removing activity with dependencies

- **Phases Section** (if using phases):
  - List of phases with activity counts
  - [Add Phase] [Edit Phase] [Remove Phase] buttons
  - [Manage Phases] → jumps to ACT 4: PHASES-LIST+FIND

**Validation**:
- Cannot remove all activities from an active workflow
- Cannot create circular dependencies
- Warning if reordering breaks logical flow

**Actions**:
- [Cancel] [Save Changes]

**Success Flow**:
- Workflow updated
- Success notification: "Workflow updated successfully"
- Returns to FOB-WORKFLOWS-VIEW_WORKFLOW-1
- Changes reflected in FOB-WORKFLOWS-LIST+FIND-1

---

#### Screen: FOB-WORKFLOWS-DELETE_WORKFLOW-1 (Confirmation Modal)

Maria clicks [Delete] on an obsolete workflow. Confirmation modal appears:

**Modal Layout**:
- **Title**: "Delete Workflow?"
- **Workflow Info**: "Component Development" in "React Frontend Development"
- **Impact Statement**:
  "This will permanently delete:"
  - ✗ 8 Activities
  - ✗ 2 Phases (if applicable)
  - ✗ 12 Artifacts (produced by activities)
  - ✗ 8 Skills (activity guides)
  - ✗ All activity dependencies

**Warnings**:
- "This action cannot be undone"
- "Parent playbook will be updated to v1.1 (local)"
- If workflow has activities with work items:
  - "5 GitHub issues are linked to activities in this workflow"

**Confirmation**:
- Checkbox: "I understand this will delete all activities and related content"
- Type workflow name to confirm

**Actions**:
- [Cancel] [Delete Workflow]

**Success Flow**:
- Workflow and all activities/phases/artifacts deleted
- Success notification: "Workflow 'Component Development' deleted"
- Returns to FOB-WORKFLOWS-LIST+FIND-1
- Remaining workflows reordered automatically

Maria confirms and the workflow is removed from the playbook.

---

---

### Act 3.5: MCP Workflow Synchronization (Export/Edit/Import)

**Context**: Maria wants to leverage her AI assistant (Windsurf/Cursor) to collaboratively edit workflow activities. The MCP server provides tools to export workflows as markdown files, edit them locally with AI assistance, and import changes back with automatic change tracking.

**Use Case**: Maria has a "Frontend Development" workflow with 15 activities. She wants to refine the activity descriptions, reorder steps, and add new activities using her AI assistant's help. Instead of clicking through the GUI, she exports the workflow to `.windsurf/workflows/FFE/`, edits the markdown files with AI assistance, and imports the changes back.

**Important**: This feature respects the playbook versioning system:
- **Draft playbooks**: Changes imported directly, version auto-increments
- **Released playbooks**: Changes create PIPs automatically (see Act 9)

---

#### MCP Tool: `export_workflow_to_local`

**Purpose**: Export a workflow and its activities as markdown files to `.windsurf/workflows/` or `.cursor/workflows/` for local editing.

**MCP Call**:
```python
# AI assistant calls this via MCP
mcp.export_workflow_to_local(
    workflow_id=42,
    target_directory=".windsurf/workflows",  # or ".cursor/workflows"
    folder_name="FFE"  # Optional, defaults to workflow slug
)
```

**What It Does**:
1. Creates folder: `.windsurf/workflows/FFE/`
2. Generates `_workflow.md` with workflow metadata:
   ```markdown
   # Frontend Development Workflow
   
   **Playbook**: React Frontend Development v0.5 (Draft)
   **Workflow ID**: 42
   **Description**: Complete frontend development process from setup to deployment
   **Phase Organization**: Uses phases (Foundation, Implementation, Testing)
   **Total Activities**: 15
   **Export Date**: 2026-02-05 11:45 UTC
   
   ## Activities
   See individual activity files: FFE-01-*.md through FFE-15-*.md
   ```

3. Creates one `.md` file per activity:
   - Filename pattern: `FFE-{order:02d}-{slug}.md`
   - Example: `FFE-01-Setup_Project.md`, `FFE-02-Configure_Build.md`
   
4. Activity file format:
   ```markdown
   # Activity: Setup Project
   
   **Activity ID**: 123
   **Order**: 1
   **Phase**: Foundation (optional)
   **Dependencies**: None (or list of upstream activity IDs)
   
   ## Description
   Initialize the React project with proper tooling and configuration.
   
   ## Guidance
   1. Run `npx create-react-app my-app --template typescript`
   2. Configure ESLint and Prettier
   3. Set up folder structure: src/components, src/utils, src/hooks
   4. Install core dependencies: react-router-dom, axios
   
   ## Artifacts Produced
   - Project Structure (artifact_id: 456)
   - Configuration Files (artifact_id: 457)
   
   ## Artifacts Consumed
   None
   
   ## Notes
   Use TypeScript template for better type safety.
   ```

**Success Response**:
```json
{
  "status": "exported",
  "workflow_id": 42,
  "workflow_name": "Frontend Development",
  "export_path": "/Users/maria/project/.windsurf/workflows/FFE",
  "files_created": [
    "_workflow.md",
    "FFE-01-Setup_Project.md",
    "FFE-02-Configure_Build.md",
    "... (15 total activity files)"
  ],
  "message": "Workflow exported successfully. Edit files locally and use import_workflow_from_local to apply changes."
}
```

**GUI Integration**:
- Available from FOB-WORKFLOWS-VIEW_WORKFLOW-1
- New button: [Export to AI Workspace] with icon `fa-file-export`
- Tooltip: "Export workflow activities as markdown files for AI-assisted editing"
- Opens modal to select target directory and folder name
- Shows success message with file count and path

---

#### Local Editing Phase

**Context**: Maria and her AI assistant now have markdown files to work with.

**Typical Workflow**:
1. Maria asks AI: "Review the FFE workflow activities and suggest improvements"
2. AI reads all `FFE-*.md` files
3. AI suggests: "Activity 3 should come before Activity 2 for better dependency flow"
4. Maria: "Make that change and also add a new activity for API integration testing"
5. AI edits the files:
   - Renames `FFE-02-*.md` → `FFE-03-*.md`
   - Renames `FFE-03-*.md` → `FFE-02-*.md`
   - Creates `FFE-16-API_Integration_Testing.md`
   - Updates `_workflow.md` to reflect 16 activities
6. Maria reviews the changes in her IDE's diff view
7. Maria: "Looks good, import these changes back to FOB"

**File Editing Rules**:
- **Add activity**: Create new `FFE-XX-Name.md` file
- **Remove activity**: Delete the `.md` file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies in markdown
- **Change phase**: Update the `Phase:` field in frontmatter

---

#### MCP Tool: `import_workflow_from_local`

**Purpose**: Import edited workflow files back into FOB, with automatic change detection and protocol generation.

**MCP Call**:
```python
# AI assistant calls this via MCP
mcp.import_workflow_from_local(
    workflow_id=42,
    source_directory=".windsurf/workflows/FFE",
    auto_apply=False  # If True, applies immediately for draft playbooks
)
```

**What It Does**:

**Step 1: Change Detection**
- Compares local `.md` files with current FOB workflow state
- Identifies:
  - **New activities**: Files that don't match existing activity IDs
  - **Modified activities**: Files with changed content (description, guidance, dependencies)
  - **Deleted activities**: FOB activities missing from local files
  - **Reordered activities**: Changed order numbers
  - **Phase changes**: Activities moved between phases

**Step 2: Generate Upload Protocol**
- Creates `_Upload_Protocol.md` in the same directory:

```markdown
# Upload Protocol: Frontend Development Workflow

**Generated**: 2026-02-05 12:15 UTC
**Workflow**: Frontend Development (ID: 42)
**Playbook**: React Frontend Development v0.5 (Draft)
**Source**: .windsurf/workflows/FFE/

## Change Summary

**Total Changes**: 4
- New Activities: 1
- Modified Activities: 2
- Deleted Activities: 0
- Reordered Activities: 2

## Detailed Changes

### 1. NEW ACTIVITY: API Integration Testing
**File**: FFE-16-API_Integration_Testing.md
**Order**: 16
**Phase**: Testing
**Rationale**: [AI/User should fill this in]

**Description**:
Test API integration points with backend services.

**Action**: CREATE

---

### 2. MODIFIED: Setup Project
**File**: FFE-01-Setup_Project.md
**Activity ID**: 123
**Changes**:
- Description updated (added TypeScript configuration details)
- Guidance section expanded with 2 new steps

**Rationale**: [AI/User should fill this in]

**Action**: UPDATE

---

### 3. REORDERED: Configure Build → Order 3 (was 2)
**File**: FFE-03-Configure_Build.md (renamed from FFE-02)
**Activity ID**: 124
**Rationale**: [AI/User should fill this in]

**Action**: REORDER

---

### 4. REORDERED: Install Dependencies → Order 2 (was 3)
**File**: FFE-02-Install_Dependencies.md (renamed from FFE-03)
**Activity ID**: 125
**Rationale**: [AI/User should fill this in]

**Action**: REORDER

---

## Approval Options

### Option A: Apply Immediately (Draft Playbooks Only)
If this playbook is in Draft status, changes can be applied directly.
- Workflow will be updated
- Playbook version will auto-increment (v0.5 → v0.6)
- No PIP required

**Command**: `mcp.apply_upload_protocol(protocol_file="_Upload_Protocol.md")`

### Option B: Submit as PIP (Released Playbooks)
If this playbook is Released, changes must go through PIP workflow.
- PIP will be created with these changes
- Requires review and approval
- Upon approval, playbook version increments (v1.0 → v2.0)

**Command**: `mcp.create_pip_from_protocol(protocol_file="_Upload_Protocol.md")`

### Option C: Cancel
Discard these changes and keep FOB workflow unchanged.

---

## Edit This Protocol

**IMPORTANT**: Review and edit the **Rationale** fields above before applying.

Explain WHY each change improves the workflow. Good rationales help reviewers understand the value of changes, especially for PIPs.

**Example Good Rationale**:
"Reordered to ensure dependencies are installed before build configuration, preventing build errors during setup."

**Example Poor Rationale**:
"Changed order" ← Too vague, doesn't explain benefit
```

**Step 3: User Review & Edit**
- User (Maria) reviews `_Upload_Protocol.md`
- Fills in rationale fields
- Can modify the protocol:
  - Remove changes she doesn't want
  - Add more context to rationales
  - Adjust change descriptions

**Step 4: Application**

**For Draft Playbooks** (auto_apply=True or manual approval):
```python
mcp.apply_upload_protocol(
    protocol_file=".windsurf/workflows/FFE/_Upload_Protocol.md"
)
```

**Response**:
```json
{
  "status": "applied",
  "workflow_id": 42,
  "playbook_version": "v0.6",  # Auto-incremented
  "changes_applied": {
    "new_activities": 1,
    "modified_activities": 2,
    "reordered_activities": 2,
    "deleted_activities": 0
  },
  "message": "Changes applied successfully. Playbook version incremented to v0.6."
}
```

**For Released Playbooks**:
```python
mcp.create_pip_from_protocol(
    protocol_file=".windsurf/workflows/FFE/_Upload_Protocol.md",
    pip_title="Improve Frontend Development workflow activity flow"
)
```

**Response**:
```json
{
  "status": "pip_created",
  "pip_id": 789,
  "pip_title": "Improve Frontend Development workflow activity flow",
  "workflow_id": 42,
  "playbook_id": 15,
  "changes_count": 4,
  "next_steps": "PIP submitted for review. Track status at FOB-PIPS-VIEW_PIP-789",
  "message": "PIP created successfully. Changes will be applied upon approval."
}
```

---

**Act 3 Summary**: Maria can now manage workflows:
- ✅ **LIST+FIND**: Browse workflows within a playbook
- ✅ **CREATE**: Create new workflows with optional phase organization
- ✅ **VIEW**: Explore workflow structure, activities, and dependencies
- ✅ **EDIT**: Update workflow details, reorder, manage activities
- ✅ **DELETE**: Remove workflows with impact warnings
- ✅ **EXPORT**: Export workflows to AI workspace as markdown files
- ✅ **IMPORT**: Import edited workflows with change tracking and protocol generation
- ✅ **SYNC**: Bidirectional sync between FOB structured data and AI workspace files

**Key Points**: 
- Workflows MAY use Phases for grouping, but Phases are optional (see Act 4)
- MCP workflow sync respects versioning: Draft = direct apply, Released = PIP workflow
- Upload Protocol provides change tracking and rationale documentation

**Next**: Maria can optionally organize workflow activities into Phases (ACT 4).

---

### Act 4: PHASES - Complete CRUDLF ⚠️ **OPTIONAL ENTITY**

**Context**: Phases are OPTIONAL groupings for activities within workflows. Maria can choose to use phases for organizing complex workflows into stages, or she can manage activities directly without phases. Not all workflows need phases.

**Pattern**: Standard CRUDLF, but with prominent "OPTIONAL" messaging throughout.

**⚠️ IMPORTANT NOTE**: Phase is an OPTIONAL entity. Workflows function perfectly without phases. Use phases only when logical grouping adds value to your workflow organization.

#### Screen: FOB-PHASES-LIST+FIND-1

From FOB-WORKFLOWS-VIEW_WORKFLOW-1, if workflow uses phases, Maria clicks [Manage Phases]. The phases list appears:

**Layout**:
- **Breadcrumb**: Playbooks > React Frontend > Workflows > Component Development > Phases
- **Header**: "Phases in Component Development workflow"
- **Optional Badge**: Prominent yellow badge: "⚠️ OPTIONAL FEATURE - Phases are not required"
- **Info Banner**:  
  "Phases are optional groupings for activities. Your workflow can function without phases. Use phases to organize activities into logical stages if it helps your methodology."
- **Top Actions**:
  - [Create New Phase] button
  - [Remove All Phases] button (converts workflow to non-phased)
  - [Reorder Phases] (drag-and-drop)
- **Phases Table**:
  - Name | Description | Activities | Order | Actions
  - Drag handles for reordering
- **Row Actions**:
  - [View] → FOB-PHASES-VIEW_PHASE
  - [Edit] → FOB-PHASES-EDIT_PHASE
  - [Delete] → FOB-PHASES-DELETE_PHASE
  - [Move Activities to Other Phase]
- **Empty State** (for workflows without phases):
  - "This workflow doesn't use phases"
  - "Activities are organized directly in the workflow"
  - "Add phases if you want to group activities into stages"
  - [Add First Phase] [Keep Without Phases] buttons

**Example Data**:
- "Foundation" | Setup and configuration | 3 Activities | Order: 1
- "Implementation" | Core development work | 5 Activities | Order: 2

---

#### Screen: FOB-PHASES-CREATE_PHASE-1

Maria clicks [Create New Phase]:

**Form**:
- **Phase Name**: Text input
  - Example: "Integration Testing"
- **Description**: Textarea
  - Example: "Integrate and test all components together"
- **Parent Workflow**: Read-only (scoped)
- **Order**: Number or "Add to end"
- **Assign Activities**: Multi-select
  - List of unassigned activities in workflow
  - Or: [Skip - Assign Later]
- **Optional Reminder**: Info box
  - "Remember: Phases are optional. You can manage activities without phase grouping."

**Actions**: [Cancel] [Create Phase]

**Success Flow**:
- Phase created in workflow
- Success: "Phase 'Integration Testing' created"
- Redirects to FOB-PHASES-VIEW_PHASE-1

---

#### Screen: FOB-PHASES-VIEW_PHASE-1

Maria views phase details:

**Layout**:
- **Header**: Phase name with "Optional grouping" badge
- **Stats**: Activities in this phase, Order in workflow
- **Activities List**:
  - All activities assigned to this phase
  - [View Activity] links → ACT 5
  - [Move to Different Phase] buttons
  - [Remove from Phase] (makes activity unassigned)
- **Phase Navigation**:
  - [Previous Phase] [Next Phase] buttons
  - Link back to workflow view

---

#### Screen: FOB-PHASES-EDIT_PHASE-1

Edit phase details, reorder, reassign activities.

**Form**: Name, Description, Order, Activity assignments

**Special Options**:
- [Merge with Another Phase]
- [Split Phase] (divide activities into two phases)
- [Dissolve Phase] (remove phase, keep activities in workflow)

---

#### Screen: FOB-PHASES-DELETE_PHASE-1

Confirmation modal:

**Impact**:
- "Activities in this phase will remain in the workflow (unassigned to any phase)"
- Shows: 5 activities will become ungrouped
- Note: "Deleting a phase does NOT delete activities"

**Actions**: [Cancel] [Delete Phase]

**Success**: Phase removed, activities remain in workflow

---

**Act 4 Summary**: Maria can optionally use phases:
- ✅ **LIST+FIND**: View phases in a workflow (if used)
- ✅ **CREATE**: Add phases to group activities
- ✅ **VIEW**: See phase organization
- ✅ **EDIT**: Reorganize phases and activities
- ✅ **DELETE**: Remove phases without losing activities

**⚠️ Key Reminder**: Phases are OPTIONAL. Workflows work perfectly without them.

**Next**: Maria manages Activities - the core work units (ACT 5).

---

### Act 5: ACTIVITIES - Complete CRUDLF

**Context**: Activities are the core work units in a methodology. Each activity represents a specific task or action to be performed. Activities have dependencies, produce artifacts, are performed by agents, and have detailed skill guides.

**Pattern**: Standard CRUDLF. Activities are the heart of the workflow execution.

#### Screen: FOB-ACTIVITIES-LIST+FIND-1

From FOB-WORKFLOWS-VIEW_WORKFLOW-1, Maria clicks [View Activities]:

**Layout**:
- **Breadcrumb**: Playbooks > React Frontend > Workflows > Component Development > Activities
- **Header**: "Activities in Component Development" (8 activities)
- **View Modes**:
  - [List View] / [Dependency Graph] / [Timeline View]
- **Top Actions**:
  - [Create New Activity]
  - [Import from Template]
  - [Bulk Edit Dependencies]
- **Filters**:
  - By Phase (if workflow uses phases)
  - By assigned Agent
  - By status (Has Skill, Has Artifacts, etc.)
  - By dependencies (Blocked, Ready, Completed)
- **Activities Table**:
  - Name | Description | Phase | Agent | Artifacts | Upstream | Downstream | Actions
- **Row Actions**:
  - [View] → FOB-ACTIVITIES-VIEW_ACTIVITY
  - [Edit] → FOB-ACTIVITIES-EDIT_ACTIVITY
  - [Delete] → FOB-ACTIVITIES-DELETE_ACTIVITY
  - [Link Skill] → ACT 8 (select from playbook-scoped skills)
  - [Link Artifacts] → ACT 6
- **Dependency Visualization**:
  - DAG showing activity flow
  - Critical path highlighted
  - Click nodes to view activity details

**Example Data**:
- "Setup Component Structure" | Phase: Foundation | Agent: Cautious Developer | 1 Artifact | No upstream | 2 downstream
- "Implement Base Components" | Phase: Implementation | Agent: Cautious Developer | 3 Artifacts | 1 upstream | 1 downstream

---

#### Screen: FOB-ACTIVITIES-CREATE_ACTIVITY-1

Maria clicks [Create New Activity]:

**Form**:
- **Name**: Text input
  - Example: "Design Token Integration"
- **Guidance**: Rich Markdown editor (8-row textarea)
  - Example: "## Overview\n\nIntegrate design system tokens into component library\n\n## Steps\n\n1. Review design tokens\n2. Implement token mapping..."
  - **Full Markdown Support**:
    - Headers (# ## ###), Lists, Tables, Code blocks
    - **Mermaid Diagrams**: Sequence, class, flow diagrams
    - Images, Links, Bold, Italic, Inline code
  - Placeholder shows example structure
  - **Note**: Guidance is static reference material - like a technical book chapter
- **Parent Workflow**: Read-only
- **Phase Assignment** (if workflow uses phases):
  - Dropdown: Select phase or "No phase"
  - **Note**: Phases are optional - not all workflows use them
- **Order**: Number input or auto-assigned
  - Auto-increments if blank
- **Has Dependencies**: Checkbox (informational only)
  - **IMPORTANT**: This is a documentation flag, not enforcement
  - Indicates this activity should be done after prerequisites
  - Does NOT track specific dependency relationships
  - Does NOT prevent execution
  - **Future Enhancement**: Will be replaced with actual M2M dependency tracking
- **Artifacts Section**:
  - "What does this activity produce?"
  - [Link Existing Artifacts] or [Create New Artifact]
  - Can specify multiple artifacts
- **Estimated Effort**: Optional
  - Hours or story points
- **Link Skills**: Checkbox list (optional, zero or more)
  - Shows skills from the same playbook
  - Select one or more skills (e.g. "Deploy to AWS Beanstalk" and "Deploy to AWS with EKS" for a deployment-style activity)
  - [Create New Skill] link → ACT 8 if needed skill doesn't exist

**Actions**: [Cancel] [Create Activity]

**Success Flow**:
- Activity created in workflow
- Success: "Activity 'Design Token Integration' created"
- Redirects to FOB-ACTIVITIES-VIEW_ACTIVITY-1

---

#### Screen: FOB-ACTIVITIES-VIEW_ACTIVITY-1

Maria views activity details:

**Layout**:
- **Header**: Activity name with phase badge (if applicable)
- **Metadata**:
  - Parent workflow link
  - Assigned agent
  - Phase (if applicable): "Foundation" with link
  - Created/Modified dates
- **Tabs**:

1. **Overview Tab**:
   - **Guidance**: Rendered Markdown with syntax highlighting
     - Mermaid diagrams rendered as SVG
     - Code blocks with language-specific formatting
     - Tables, images, formatted lists
   - Phase assignment (if using phases)
   - Order number in workflow
   - **Has Dependencies**: Info badge (documentation only)
   - Created/Updated timestamps
   - **Note**: View Artifacts, Agents, Skills in separate tabs

2. **Dependencies Tab**: (Future Enhancement)
   - **Current State**: Only shows "Has Dependencies" flag
   - **Planned**: Full dependency management
     - **Upstream**: Activities that should complete first
     - **Downstream**: Activities that depend on this one
     - Dependency graph visualization
     - M2M relationship tracking
   - **Note**: Currently activities have only a boolean flag, not actual dependency relationships

3. **Artifacts Tab**:
   - List of artifacts produced by this activity
   - [View Artifact] links → ACT 6
   - [Add New Artifact] [Link Existing] buttons

4. **Skills Tab**:
   - Shows all linked skills with Capability Domain and Technology Stack badges
   - If no skills linked: "No skills linked" with [Link Skills] button
   - If linked: list of skill titles with [View Skill] links → ACT 8
   - [Change Skills] opens Activity edit form checkbox list

5. **Work Items Tab**:
   - GitHub issues, Jira tickets linked via external MCP
   - [Create Work Item] button (opens MCP interface)
   - Status of linked items

---

#### Screen: FOB-ACTIVITIES-EDIT_ACTIVITY-1

Edit activity:

**Form**: All fields from CREATE, pre-populated

**Additional Options**:
- **Dependency Management**:
  - Drag-and-drop dependency editor
  - Visual validation (highlights circular dependencies in red)
- **Move to Different Phase**: Dropdown (if workflow uses phases)
- **Reassign Agent**: Dropdown
- **Artifact Management**:
  - Add/remove artifact associations
  - [Create New Artifact] inline

**Validation**:
- Cannot create circular dependencies
- Warns if removing dependencies breaks workflow logic
- Warns if reassigning agent affects other activities

**Actions**: [Cancel] [Save Changes]

---

#### Screen: FOB-ACTIVITIES-DELETE_ACTIVITY-1

Confirmation modal:

**Impact Statement**:
- "This will permanently delete the activity"
- Shows affected items:
  - ⚠️ Linked skill M2M rows will be removed (skills themselves remain in playbook)
  - ⚠️ 2 Downstream activities will lose upstream dependency
  - ⚠️ 3 Artifacts may become orphaned
  - ⚠️ 5 GitHub issues will lose activity context

**Dependency Warning**:
- "2 activities depend on this one:"
  - "Implement Base Components"
  - "Component Testing"
- "Deleting will break their upstream dependencies"

**Confirmation**:
- Checkbox: "I understand the impact"
- Type activity name

**Actions**: [Cancel] [Delete Activity]

**Success**: Activity deleted, workflow updated

---

**Act 5 Summary**: Maria manages activities:
- ✅ **LIST+FIND**: Browse and filter activities with dependency visualization
- ✅ **CREATE**: Create activities with dependencies, agents, and artifacts
- ✅ **VIEW**: Explore activity details, dependencies, artifacts, and skills
- ✅ **EDIT**: Update activity details and reorganize dependencies
- ✅ **DELETE**: Remove activities with full dependency impact warnings

**Next**: Maria defines Artifacts produced by activities (ACT 6).

---

### Act 6: ARTIFACTS - Complete CRUDLF (No More "Deliverable"!)

**Context**: Artifacts are outputs produced by activities. They represent tangible results like documents, code, designs, reports, etc. **Note**: Formerly called "Deliverable" - now consistently called "Artifact".

**Pattern**: Standard CRUDLF. Artifacts are linked to producing activities.

#### Screen: FOB-ARTIFACTS-LIST+FIND-1

From workflow or activity view, Maria navigates to Artifacts:

**Layout**:
- **Header**: "Artifacts" with count
- **Scope Selector**:
  - "All Playbooks" / "Current Playbook" / "Current Workflow"
- **Top Actions**:
  - [Create New Artifact]
  - [Import Artifacts]
- **Filters**:
  - By type (Document, Code, Design, Data, Report, etc.)
  - By producing activity
  - By workflow
  - Orphaned (no producing activity)
- **Artifacts Table**:
  - Name | Type | Description | Produced By | Workflow | Actions
- **Row Actions**:
  - [View] → FOB-ARTIFACTS-VIEW_ARTIFACT
  - [Edit] → FOB-ARTIFACTS-EDIT_ARTIFACT
  - [Delete] → FOB-ARTIFACTS-DELETE_ARTIFACT

**Example Data**:
- "Component Library" | Code | "Reusable React components" | Activity: "Build Components" | Workflow: Component Dev
- "Design Tokens" | Design | "Color, spacing, typography tokens" | Activity: "Design System Setup" | Workflow: Component Dev
- "Test Report" | Document | "Unit and integration test results" | Activity: "Run Tests" | Workflow: Testing

---

#### Screen: FOB-ARTIFACTS-CREATE_ARTIFACT-1

Create new artifact:

**Form**:
- **Name**: Text input
  - Example: "API Documentation"
- **Type**: Dropdown
  - Options: Document, Code, Design, Data, Report, Specification, Other
- **Description**: Textarea
  - Example: "Complete REST API documentation with examples"
- **Produced By**: Activity selector (required)
  - Dropdown or search for activity
  - "Which activity creates this artifact?"
- **Format/Extension**: Optional
  - Example: ".md", ".pdf", ".json"
- **Template**: Optional checkbox
  - "Use this as a template for similar artifacts"
- **External Link**: Optional URL
  - Link to actual artifact (GitHub, Figma, Google Docs, etc.)

**Actions**: [Cancel] [Create Artifact]

**Success**: Artifact created and linked to activity

---

#### Screen: FOB-ARTIFACTS-VIEW_ARTIFACT-1

View artifact details:

**Layout**:
- **Header**: Artifact name with type badge
- **Metadata**:
  - Type, Format
  - Produced by: [Activity name] with link
  - Parent workflow, playbook
  - External link (if provided)
- **Tabs**:

1. **Overview Tab**:
   - Full description
   - Producing activity details
   - Consumers: Activities that use this artifact (if any)
   - Related artifacts (similar type or workflow)

2. **Usage Tab**:
   - List of activities that reference this artifact
   - Usage context
   - Dependencies

3. **History Tab**:
   - Creation date, author
   - Modification history
   - Versions (if artifact has versions)

---

#### Screen: FOB-ARTIFACTS-EDIT_ARTIFACT-1

Edit artifact: Form with all fields from CREATE, pre-populated

**Special Options**:
- [Change Producing Activity]: Dropdown
  - Warning if changing: "This may affect workflow understanding"
- [Mark as Template]
- [Update External Link]

---

#### Screen: FOB-ARTIFACTS-DELETE_ARTIFACT-1

Confirmation modal:

**Impact**:
- "This will remove the artifact"
- Warning: "Activity 'Build Components' will no longer have this artifact listed as output"
- If other activities reference it: List shown

**Note**: "This does NOT delete the actual file/document, only the artifact metadata in Mimir"

**Actions**: [Cancel] [Delete Artifact]

---

**Act 6 Summary**: Maria manages artifacts (no more "Deliverable"!):
- ✅ **LIST+FIND**: Browse all artifacts with filtering
- ✅ **CREATE**: Define new artifacts produced by activities
- ✅ **VIEW**: See artifact details and usage
- ✅ **EDIT**: Update artifact information
- ✅ **DELETE**: Remove artifact metadata

**Terminology Note**: Always use "Artifact", never "Deliverable".

**Next**: Maria defines Agents who perform activities (ACT 7).

---

### Act 7: AGENTS - Complete CRUDLF

**Context**: Agents are AI assistants defined at the playbook level. Each agent represents a named AI persona (e.g., "Cautious Developer (drdobbs-v2)") with a description of its capabilities and guidelines. Agents are assigned to Activities (M2M) to indicate which AI assistant should perform or assist with that activity.

**Pattern**: Standard CRUDLF scoped to a Playbook. Agents are assigned to Activities from the Activity detail page.

#### Screen: FOB-AGENTS-LIST+FIND-1

Maria clicks the **Agents** tab inside a playbook's detail page.

**Layout**:
- **Breadcrumb**: Playbooks > React Frontend Development > Agents
- **Header**: "Agents in React Frontend Development" with count badge
- **Top Actions**:
  - [Create New Agent]
- **Agents Table**:
  - Name | Description | Activities | Actions
- **Row Actions**: [View] [Edit] [Delete]
- **Filter**: Search by name; filter by "Used in Activities" / "Unused"
- **Empty state**: "No agents yet" + [Create First Agent] button

**Example Data**:
- "Cautious Developer (drdobbs-v2)" | "Careful, test-driven frontend implementation" | 12 Activities
- "UX Reviewer" | "Reviews screens against usability heuristics" | 8 Activities
- "Deployment Bot" | "Runs CI/CD checks and deployment steps" | 5 Activities

---

#### Screen: FOB-AGENTS-CREATE_AGENT-1

Create agent:

**Form**:
- **Name**: Text input (required)
  - Example: "Cautious Developer (drdobbs-v2)"
  - Tip: include the model/version slug for clarity
- **Description**: Textarea (required)
  - Example: "Careful, test-driven frontend implementation agent. Reviews code for regressions before committing."

**Actions**: [Cancel] [Create Agent]

**Success**: Redirects to FOB-AGENTS-VIEW_AGENT-1 for the new agent.

---

#### Screen: FOB-AGENTS-VIEW_AGENT-1

View agent details:

**Header**: Agent name, parent playbook badge, timestamps

**Sections**:
1. **Description**: Full agent description
2. **Used in Activities**: All activities that reference this agent
   - Grouped by Workflow
   - Each entry is a clickable link → Activity detail page

**Actions**: [Edit Agent] [Delete Agent]

---

#### Screen: FOB-AGENTS-EDIT_AGENT-1

Edit agent: Update Name and Description fields. Same form as Create.

---

#### Screen: FOB-AGENTS-DELETE_AGENT-1

Confirmation modal:

**Impact**: "This agent is assigned to 12 activities. Deleting it will remove the assignment from all of them."

**Options**:
- [Delete Agent] — removes agent and all activity assignments
- [Cancel]

---

**Act 7 Summary**: Maria manages agents:
- ✅ **LIST+FIND**: Browse all agents in a playbook, filter by usage
- ✅ **CREATE**: Define new agent personas with name and description
- ✅ **VIEW**: See agent details and which activities use it
- ✅ **EDIT**: Update agent name and description
- ✅ **DELETE**: Remove agent with clear impact warning

**Next**: Maria creates detailed Skill guides for activities (ACT 8).

---

### Act 8: SKILLS - Complete CRUDLF + Link

**Context**: Skills are reusable, tech-specific guides that live at the **playbook level**. Each skill describes *how* to perform a capability (e.g., "Build a Form") using a specific technology (e.g., "React+Redux"). Activities reference skills via **M2M** — an activity may link zero or more skills (e.g. a "Pick Deployment Style" activity may attach both "Deploy to AWS with Beanstalk" and "Deploy to AWS with EKS"). Skills carry two metadata fields: `capability_domain` (what it does) and `technology_stack` (how it does it). This enables the "Define Architecture" workflow to scan available skills and recommend tech stacks based on coverage.

**Pattern**: Standard CRUDLF + Link. Skills are playbook-scoped and reusable across activities.

**Relationship**: `Skill --FK--> Playbook`, `Activity --M2M--> Skill` (many-to-many)

#### Screen: FOB-SKILLS-LIST+FIND-1

Maria navigates to Skills from the playbook detail page:

**Layout**:
- **Header**: "Skills in [Playbook Name]"
- **Scope**: Playbook-scoped — shows all skills in the current playbook
- **Filters**:
  - By Capability Domain (autocomplete from existing values)
  - By Technology Stack (autocomplete from existing values)
  - Unlinked (skills with zero activity references)
- **Search**: Matches title, capability_domain, technology_stack, and content
- **Skills Table**:
  - Title | Capability Domain | Technology Stack | Activities (count) | Actions
- **Row Actions**: [View] [Edit] [Delete]
- **Create**: [Create New Skill] button

**Example Data**:
- "React Form Component" | GUI_FORM | React+Redux | 3 activities
- "Django CRUD View" | API_CRUD | Django+HTMX | 5 activities
- "DB Migration Script" | DB_MIGRATION | Alembic | 0 activities (unlinked)

---

#### Screen: FOB-SKILLS-CREATE_SKILL-1

Maria clicks [Create New Skill] from the playbook skills list:

**Form**:
- **Playbook Context**: Read-only badge showing parent playbook
  - Shows: "Create Skill in [Playbook Name]"
- **Title**: Text input (required)
  - Example: "React Form Component"
- **Capability Domain**: Text input with autocomplete from existing values
  - Example: "GUI_FORM", "API_CRUD", "DB_MIGRATION"
  - New values allowed (free-text tags)
- **Technology Stack**: Text input with autocomplete from existing values
  - Example: "React+Redux", "Django+HTMX", "FastAPI"
  - New values allowed (free-text tags)
- **Content**: Markdown editor
  - Step-by-step guidance, code blocks, examples, best practices
  - Supports: headings, bold, italic, lists, code blocks, links

**Actions**: [Cancel] [Create Skill]

**Success**: Skill created in playbook → redirects to FOB-SKILLS-VIEW_SKILL-1

---

#### Screen: FOB-SKILLS-VIEW_SKILL-1

View skill details:

**Layout**:
- **Header**: Skill title
- **Metadata Badges**: Capability Domain, Technology Stack, parent Playbook
- **Content**: Rendered Markdown (headings, code blocks, lists, etc.)
- **Referenced by Activities (N)**: List of activity names with workflow context
  - Each activity link navigates to FOB-ACTIVITIES-VIEW_ACTIVITY-1
- **Actions**:
  - [Edit Skill]
  - [Delete Skill]
- **Breadcrumb**: Playbooks > [Playbook] > Skills > [Skill Title]

---

#### Screen: FOB-SKILLS-EDIT_SKILL-1

Edit skill: All fields editable (Title, Capability Domain, Technology Stack, Content)

**Pre-populated**: All fields filled with current values

**Autocomplete**: Capability Domain and Technology Stack suggest existing values from the playbook

---

#### Screen: FOB-SKILLS-DELETE_SKILL-1

Confirmation modal:

**Display**: Skill title, Capability Domain badge, Technology Stack badge

**Impact**: "Referenced by N activities — M2M links to those activities will be removed"

**Note**: "Activities will remain, only the skill and its references are removed"

---

#### Linking: Activity ↔ Skill (via Activity Edit)

Skills are linked to activities through the Activity edit form:
- **Skills checkbox list**: Shows only skills from the same playbook; select zero or more
- **Multi-skill**: One activity may link multiple skills (e.g. deployment style alternatives)
- **Reusable**: Multiple activities can reference the same skill
- **MCP**: `link_skill_to_activity` adds to set; `unlink_skill_from_activity` requires `skill_id`; `set_activity_skills` replaces full set

**See**: `skills-link.feature` for full scenarios.

---

**Act 8 Summary**: Maria manages skills:
- ✅ **LIST+FIND**: Browse playbook skills with capability/tech filters
- ✅ **CREATE**: Create reusable, tech-specific skill guides at playbook level
- ✅ **VIEW**: Read skill content with metadata badges and activity references
- ✅ **EDIT**: Update skill details including capability and tech stack metadata
- ✅ **DELETE**: Remove skills (M2M links cleared automatically; activities remain)
- ✅ **LINK**: Link/unlink multiple skills per activity via Activity edit form and MCP

**Key Point**: M2M relationship — activities may have zero or more skills; one skill can serve many activities. Skills are playbook-scoped and carry `capability_domain` + `technology_stack` metadata for architecture advisory.

---

**🎉 Acts 2-8 Complete!** All 7 core entities (Playbooks, Workflows, Phases, Activities, Artifacts, Agents, Skills) now have full CRUDLF coverage with narrative explanations.

**Demo Playbook Available**: A Feature-Driven Development (FDD) demo playbook with 10 activities showcasing rich Markdown guidance is available via `python manage.py create_demo_fdd`. This demonstrates:
- Mermaid diagrams (class, sequence, flow)
- Code examples (Python, Bash, YAML)
- Tables and checklists
- Multi-level documentation structure

**Next**: Maria can propose improvements via PIPs (ACT 9) and manage import/export (ACT 10).

---

### Act 9: PIPs - Playbook Improvement Proposals

**Context**: As Maria uses playbooks (whether her own or those shared in a team), she discovers opportunities for improvement. A **PIP (Playbook Improvement Proposal)** is a versioned request to alter one specific Released playbook, containing an ordered list of typed **Changes**.

**Key Concepts**:
- A PIP targets exactly one Released playbook
- Each PIP contains one or more **Changes**, each typed as:
  - `ADD` — add a new Workflow / Activity / Skill / Agent / Artifact, appended at the end of its container or inserted **after a named sibling** (e.g., "insert after BPE-01")
  - `ALTER` — replace or update an existing entity's content
  - `DROP` — remove an existing entity (with rationale)
- After submission, **Galdr AI** automatically reviews each Change against the playbook context and writes a recommendation
- An **Administrator** (e.g., Mike) reviews Galdr's recommendations in **Django Admin** and makes the final Accept/Reject decision per Change
- Accepted Changes are applied atomically → playbook publishes a new major version
- The PIP submitter receives an **email** summarising the outcome per Change

---

#### Creating a PIP

**Trigger**: While using "React Frontend Development" (Released v1.0, authored by Mike), Maria notices it lacks accessibility considerations.

**Via AI Assistant (Cursor/MCP)**:

Maria asks her AI assistant:
```
> mimir: This React playbook is great, but it doesn't mention accessibility testing.
  I want to add an Activity "Accessibility Audit" after "Component Testing".
  Can you help me create a PIP for this?
```

AI responds:
```
I'll create a PIP for React Frontend Development v1.0.

Proposed Change:
  #1  ADD  Activity "Accessibility Audit"
      Insert after: "Component Testing"
      Guidance: "Ensure React components meet WCAG 2.1 AA standards.
                 Install axe-core and jest-axe; add a11y tests to the
                 component suite; configure automated checks in CI/CD."

Shall I submit this PIP?
```

Maria confirms: `> mimir: Yes, submit it.`

---

#### Screen: FOB-PIP-CREATE

Whether created via MCP or the FOB UI, the PIP creation form contains:

- **Target Playbook**: "React Frontend Development" v1.0 (locked — must be Released)
- **PIP Title**: "Add Accessibility Audit Activity"
- **Summary**: Brief rationale (required)
- **Change List** (ordered, one row per change):

| # | Type | Entity Type | Name / Target | Position | Content / Rationale |
|---|------|-------------|---------------|----------|---------------------|
| 1 | ADD  | Activity    | "Accessibility Audit" | After "Component Testing" | Full guidance text |

- [+ Add Change] — opens an inline row builder:
  - Type: ADD / ALTER / DROP
  - Entity Type: Workflow / Activity / Skill / Agent / Artifact
  - Name / Target: text field
  - Position (for ADD): "append" or "after [sibling name]"
  - Content / Rationale: Markdown textarea
- [Preview Diff] — shows the cumulative diff applied to the playbook
- [Save as Draft] — saves without submitting
- [Submit for Review] — transitions status to `Submitted`, triggers Galdr processing

---

#### PIP Lifecycle

```
Draft → Submitted → Processing (Galdr) → Reviewed → Accepted / Rejected (partial)
```

**Galdr Processing** (automated, runs immediately after submission):

1. Galdr reads the target Playbook in full: all Workflows, Activities, goals, Skills, Agents, Artifacts
2. For each Change:
   - Assesses consistency with the parent Workflow goals
   - Checks for upstream/downstream Activity impact
   - Writes a recommendation: `ACCEPT` / `REJECT` / `NEEDS_CLARIFICATION`
   - Attaches 1–3 sentence reasoning
3. PIP status → `Reviewed`
4. FOB notifies Administrators: "PIP-42 is ready for review"

---

#### Screen: FOB-PIP-LIST

Maria navigates to **PIPs** in the top nav. The list page loads and immediately clears the count pill (marking all PIPs as "seen").

**Layout**:
- **Header**: "PIPs" with total count badge (e.g., "PIPs (7)")
- **Tabs**:
  - "My PIPs" (default) — PIPs submitted by Maria
  - "All PIPs" (Administrators only) — every PIP in the system
- **Filter Bar**:
  - **Status** multi-select: ☐ Draft ☐ Submitted ☐ Processing (Galdr) ☐ Reviewed ☐ Accepted ☐ Rejected
  - **Target Playbook** dropdown: (all playbooks or pick one)
  - **Date range**: Submitted between [from] — [to]
  - [Clear Filters] button
- **Table columns**: PIP ID | Title | Target Playbook | Changes | Status | Submitted | Last Updated | Actions
- **Row indicators**:
  - 🔵 Blue dot on rows where status changed since last view (clears on row click / page load)
  - Status badge colour: Draft=gray, Submitted=blue, Processing=yellow, Reviewed=purple, Accepted=green, Rejected=red
- **Row actions** (dropdown per row):
  - [View] → FOB-PIP-DETAIL
  - [Edit] (Draft only)
  - [Discard] (Draft only)
- **Example rows** (with blue dot on PIP-42 since it just moved to Reviewed):

```
● PIP-42 | Add Accessibility Audit        | React Frontend Dev | 1 | Reviewed  | 2026-05-14 | 2026-05-15
  PIP-38 | State Management Patterns      | React Frontend Dev | 2 | Accepted  | 2026-04-20 | 2026-04-22
  PIP-35 | Drop Legacy IE Support         | React Frontend Dev | 1 | Rejected  | 2026-04-10 | 2026-04-11
  PIP-30 | Add Figma Integration Activity | UX Research        | 3 | Draft     | 2026-03-05 | 2026-03-05
```

- **Empty state** (no PIPs yet): "You haven't submitted any PIPs yet. Find a Released playbook you'd like to improve and click [Submit PIP]."
- **Pagination**: 20 per page

Opening the page resets the count pill to 0.

---

#### Screen: FOB-PIP-DETAIL

Maria opens PIP-42:
- **Header**: PIP ID, title, target playbook, submitter, status, timestamps
- **Summary**: Maria's rationale
- **Change List** — one card per change:

```
#1  [ ADD ] Activity "Accessibility Audit"  (after "Component Testing")
    Content: "Ensure React components meet WCAG 2.1 AA standards..."
    ──────────────────────────────────────────────────────────
    Galdr:  ACCEPT
    Reason: "Consistent with the Testing phase goal. No upstream
             conflicts detected. The new activity has a clear
             position in the workflow."
```

- **Status banner**: "Reviewed — awaiting Administrator decision"

---

#### Django Admin: Administrator Review (Mike)

Mike opens **Django Admin → PIPs → PIP-42**. He sees the standard Django Admin change-view for the PIP, with a read-only inline section showing Galdr's output per Change, and an editable decision field:

```
PIP: Add Accessibility Audit  [status: Reviewed]

Changes:
  #1  [ ADD ] Activity "Accessibility Audit"  (after "Component Testing")
      Galdr recommendation: ACCEPT
      Reasoning: Consistent with the Testing phase goal; no upstream
                 conflicts detected.
      Admin decision:  [ACCEPT ▾]   ← pre-filled from Galdr, editable
```

**Admin actions**:
- Override any Change decision: change `ACCEPT` → `REJECT` or vice versa
- Add a human note to any Change (optional)
- [Accept All & Apply] — applies all accepted Changes atomically
- [Reject All] — rejects the PIP without changes

**On submission**:
- Accepted Changes are applied to the playbook → "React Frontend Development" publishes v2.0
- Rejected Changes are discarded
- PIP status → `Accepted` (or `Partially Accepted` if mixed, or `Rejected`)
- Email sent to Maria (see Email Notification below)

---

#### Email Notification

After Mike's decision, the system sends Maria an email:

```
Subject: Your PIP "Add Accessibility Audit" — Accepted ✓

Hi Maria,

Your change request for "React Frontend Development" has been reviewed.

Change 1: ADD Activity "Accessibility Audit"  →  Accepted
  Reasoning: Consistent with testing goals; no upstream conflicts.

Overall: Accepted. Version 2.0 has been published with your changes.

— Mimir FOB
```

If partially accepted:
```
Subject: Your PIP "Update Testing Workflow" — Partially Accepted

Change 1: ADD Activity "Accessibility Audit"  →  Accepted
  Reasoning: Consistent with the Testing phase goal.

Change 2: ALTER Activity "Component Testing"  →  Rejected
  Reasoning: The proposed wording removes the required Artifact link
             to "Test Suite", breaking downstream dependencies.

Overall: Partially accepted. Version 2.0 published with Change 1 applied.
```

---

#### AI-Initiated PIPs

**Context**: AI observes Maria's work patterns and proactively suggests improvements.

**Scenario**: After Maria completes several components with accessibility features, the AI notices the pattern:

```
✓ Components created: Button, Card, Modal (all with focus traps, ARIA labels)
✓ Accessibility tests added to each component

I notice you're consistently adding accessibility features, but the playbook
doesn't call for focus trapping in modals. Should I propose a PIP to add:
  - ADD Activity "Focus Trap Guidelines"  (after "Create Components")
  - ALTER Activity "Component Testing" to reference a11y checklist

Would you like me to create this PIP?
```

Maria: `> mimir: Yes, create the PIP`

AI builds the Change list and calls `submit_pip` via MCP → standard Galdr review flow begins.

---

**Act 9 Summary**: Maria can evolve playbooks through PIPs:
- ✅ Create PIPs manually (GUI) or via AI (MCP)
- ✅ Structure Changes as typed ADD / ALTER / DROP per entity
- ✅ Insert new entities at a precise position within a container
- ✅ Track PIP status through the Galdr processing + Admin review lifecycle
- ✅ Receive per-Change email notification with reasoning
- ✅ Administrators review Galdr recommendations in Django Admin and override as needed

**Key Benefits**: Structured change control, AI-assisted pre-screening, transparent per-Change reasoning, automated application of accepted changes.

**Next**: Maria manages import/export operations (ACT 10).

---

### Act 10: IMPORT/EXPORT - Playbook Distribution

**Context**: Maria needs to share playbooks outside FOB — for backups, offline distribution, cross-instance transfer, or client delivery.

**Key Formats**:
- **JSON**: Structured data format for programmatic use
- **MPA** (Mimir Playbook Archive): Compressed package with metadata

#### Export Playbook

**Screen: FOB-PLAYBOOKS-VIEW_PLAYBOOK-1** (from Act 2)

Maria views her "UX Research Methodology" playbook and clicks **[Export]** from top actions.

**Export Modal**:
- **Format Options**:
  - ○ JSON (.json) - Raw structured data
  - ○ Mimir Playbook Archive (.mpa) - Packaged with metadata
- **Include Options** (checkboxes):
  - ☑ All workflows and activities
  - ☑ Artifacts and agents
  - ☑ Skills (activity guides)
  - ☑ Version history
  - ☐ PIP history (optional)
- **Security**:
  - ☐ Password protect (optional)
  - Password field (if checked)
- **Filename**: `ux-research-methodology-v2.1` (auto-generated, editable)
- [Cancel] [Export]

Maria selects **JSON format**, leaves all options checked, clicks [Export]:
- File saved: `ux-research-methodology-v2.1.json` to ~/Downloads
- Success notification: "Playbook exported successfully"
- **Use cases**:
  - Backup before major changes
  - Share with colleague via email
  - Import to another FOB instance
  - Version control (commit to git)

#### Export Scenarios

**Scenario A: Offline Distribution for Workshop**

Maria's colleague Alex needs the playbook for an offline workshop (no FOB access):
- Maria exports as `.mpa` with password protection
- Emails file to Alex: `ux-research-v2.1.mpa`
- Alex imports to his FOB (see Import section below)

**Scenario B: Client Delivery (IP Transfer)**

After transferring ownership to Acme client, Maria exports final version:
- Exports "UX Consulting" playbook as JSON
- Delivers to client as documentation artifact
- Client can import to their own FOB instance

**Scenario C: Backup Before Experimentation**

Before applying experimental PIPs:
- Maria exports current stable version
- Tests PIPs locally
- If issues arise: deletes modified version, re-imports from backup

---

#### Import Playbook

**Screen: FOB-PLAYBOOKS-LIST+FIND-1** (from Act 2)

Maria clicks [Import from JSON] button (top actions).

**Import Modal**:
- **File Upload Area**: "Drop JSON or MPA file here or click to browse"
- Accepted formats: `.json`, `.mpa`
- [Cancel] (disabled until file selected)

**Action: Select File**

Maria selects `design-system-patterns-v1.5.json` from downloads:
- Filename appears in modal
- System validates file format
- [Import] button becomes active

**Validation Process**:

System checks:
- ✓ Valid JSON structure
- ✓ Required fields present (id, name, version, workflows, activities)
- ✓ Schema compliance (Mimir data model)
- ✓ No circular dependencies
- ✓ Referenced entities exist

**Success Path** - Valid Playbook:

Shows preview:
- **Playbook**: "Design System Patterns"
- **Version**: 1.5
- **Author**: Community Contributors
- **Contents**:
  - 3 Workflows
  - 15 Activities
  - 12 Artifacts
  - 5 Agents
  - 8 Skills
- **Conflict Check**: "No conflicts with existing playbooks"
- Message: "This playbook will be added to your local FOB"
- [Cancel] [Import Playbook]

Maria clicks [Import Playbook]:
- Progress: "Importing playbook..."
- Playbook added to local database
- Success: "Design System Patterns v1.5 imported successfully"

**Screen: FOB-PLAYBOOKS-LIST+FIND-1** (Updated)

Imported playbook appears:
- **Design System Patterns** v1.5
- Status: Imported (local)
- Source: Imported from JSON
- Actions: [View] [Edit] [Export] [Delete]

---

**Error Path** - Invalid Playbook:

If validation fails:
- ✗ Error: "Invalid playbook format"
- Details: "Missing required field: 'activities'"
- OR: "Circular dependency detected in workflow 'Component Setup'"
- OR: "Schema version mismatch: File uses v2.0, FOB supports v1.5"
- [Close] [Try Another File]

**Error Path** - Conflict Detected:

If playbook with same ID exists:
- ⚠️ Warning: "Playbook 'Design System Patterns' already exists"
- **Options**:
  - ○ Skip import (keep existing)
  - ○ Replace existing (overwrites local version)
  - ○ Import as new copy (generates new ID)
- [Cancel] [Proceed]

---

**Import from MPA (Password Protected)**:

If importing `.mpa` file with password:
- Password prompt appears: "This archive is password protected"
- Password field: [____]
- [Cancel] [Unlock]

After correct password: Standard import flow continues

If wrong password: "Incorrect password. Please try again."

---

**Act 10 Summary**: Maria manages playbook distribution:
- ✅ Export playbooks as JSON or MPA
- ✅ Password-protect sensitive playbooks
- ✅ Import playbooks from files
- ✅ Validate imported data
- ✅ Handle conflicts and errors gracefully
- ✅ Distribute playbook files for offline reading (note: MCP always requires a live FOB — either local or hosted)

**Use Cases Covered**:
- Backups and version control
- Offline distribution (workshops, air-gapped environments)
- Cross-instance transfer
- Client deliverables
- Emergency recovery

**Next**: Maria manages her community networks (ACT 11: Team Management).

---

### Act 11: Building Her Network (Team Management)

**Context**: Maria wants to organize her practice - a public team for UX community, a private one for her client work, and join existing communities.

#### Screen: FOB Dashboard (First Login)
Maria opens her FOB application and sees the welcome dashboard:
- Empty playbook list (no playbooks yet)
- "Browse Teams" button
- "Create Team" button

#### Screen: FOB Create Team - UX Community
Maria clicks "Create Team" and fills out the form:
- **Team Name**: "UX"
- **Description**: "User Experience methodologies and best practices"
- **Visibility**: Public (appears in browse)
- **Join Policy**: Requires Approval (Maria will review requests)
- **Category**: Design
- Clicks "Create Team"

**Result**: Maria is now the admin of the "UX" team.

#### Screen: FOB Create Team - Client Work
Maria creates a second team for her consulting clients:
- **Team Name**: "Acme, INC"
- **Description**: "UX Consulting services for Acme Corporation"
- **Visibility**: Hidden (only visible to members she manually adds)
- **Join Policy**: Invite Only
- **Category**: Private
- Clicks "Create Team"

**Result**: Maria now manages two teams - one public, one hidden.

#### Screen: FOB Team Browser
Maria clicks "Browse Teams" to explore existing communities. She sees:
- Search bar and category filters
- List of public teams with descriptions and member counts
- "Usability" team catches her eye (Mike's community)

#### Screen: FOB Team Details - Usability
Maria clicks on "Usability" to see details:
- **Description**: "Best practices for usable software development"
- **Members**: 127 members
- **Playbooks**: 8 available playbooks (including Mike's React playbook)
- **Join Policy**: Auto-approve
- "Join Team" button

#### Action: Join Team
Maria clicks "Join Team". Because it's set to auto-approve:
- She's immediately added to the Usability team
- In-app notification: "You've joined the Usability team"
- **Confirmation email** sent to Maria with subject "You've joined the Usability team" and a [View Team] link
- She can now see available playbooks from this team

**Result**: Maria is now a member of three teams - two she created, one she joined.

#### Action: Join Team — Requires Approval
When a team has Join Policy "Requires Approval":
- Maria's request is queued; she sees a disabled "Request Pending" button
- The **team admin receives an email**: "New join request for your team" with a [Review Requests] link → `/teams/<pk>/manage/?tab=join-requests`
- All approve/reject actions require the admin to be logged in (no one-click links in email)

#### Action: Invite Members (Admin)
Maria manages her hidden "Acme, INC" team and wants to add client contacts:
- She opens Manage Team → **Invite** tab
- Enters comma-separated email addresses and an optional welcome message
- Clicks [Send Invites]

**For existing FOB users** (email matches a registered account):
- An invite email is sent: "You've been invited to join the Acme, INC team on Mimir"
- The email includes the optional welcome text and a [View Team] link
- The invitee appears in the **Join Requests** tab with an "Invited" badge
- Maria can Approve or Reject from the Join Requests tab as usual

**For new emails** (no FOB account found):
- A FOB account is auto-created with credentials derived from the email:
  - `username` = local part before `@` (e.g. `alice.roy` from `alice.roy@acme.com`)
  - `first_name` = local part up to the first `.`, or full local part if no dot (e.g. `alice`)
  - `last_name` = domain name without TLD (e.g. `acme` from `acme.com`)
  - `password` = random (account activation required)
- An **activation + invite** email is sent: "You've been invited to Mimir and the Acme, INC team"
- The email includes an [Activate Account & View Team] link
- The new user appears in the Join Requests tab with badge "Invited (new user)"

**Act 11 Summary**: Maria manages her professional network:
- ✅ Create teams (public and hidden)
- ✅ Browse and join existing teams
- ✅ Email confirmation on auto-join; email notification to admin on join request
- ✅ Invite members by email (existing users and auto-register new ones)
- ✅ Review and approve/reject join requests (including invited users)
- ✅ Manage team playbook submissions
- ✅ Transfer team admin rights
- ✅ Remove members (with knowledge loss consequences)

**Next**: Maria uses Mimir MCP for AI-assisted methodology execution (ACT 12).

---

### Act 12: MCP INTEGRATION - AI-Assisted Methodology Execution

**Context**: Maria works in Cursor (or Windsurf) with Mimir MCP providing playbook context via FastMCP → FOB REST API. External MCPs (GitHub, Jira) handle work items.

#### Setup: MCP Configuration

Maria's Cursor has two MCP servers configured:
1. **Mimir MCP** (FastMCP → `http://localhost:8000/api/`): Provides playbook context, activities, artifacts, PIP submission
2. **GitHub MCP** (external): Creates/tracks GitHub issues

**Important**: The MCP server (FastMCP container) requires a live FOB to function — it has no data of its own. `BASE_URL` points to either a **local FOB** (`http://localhost:8000`) or a **hosted FOB** (`https://mimir.featurefactory.io`). Without a reachable FOB, MCP tools will fail.

**Mimir MCP config** (in Cursor's MCP settings or `~/.cursor/mcp.json`):
```json
{
  "mimir": {
    "command": "python",
    "args": ["-m", "mcp_integration.server"],
    "env": {
      "BASE_URL": "http://localhost:8000",
      "TOKEN": "mimir_a8f3d9e2b1c4567890abcdef12345678"
    }
  }
}
```

FastMCP translates each MCP tool call into an authenticated REST request: `GET/POST BASE_URL/api/…` with `Authorization: Token TOKEN`. There is no direct database access from the MCP layer — all reads and writes go through FOB's validated API endpoints.

---

#### Using Active Playbook

**Screen: FOB Dashboard**

Maria activates "React Frontend Development" playbook:
- Clicks on playbook
- [Activate] button
- Success: "React Frontend Development v1.2 is now active"

**Windsurf/MCP Chat**

Maria asks her AI assistant:
```
> mimir: I'm starting a new React project. How do I set up the project structure?
```

**MCP Response** (from Mimir MCP):
```
Based on "React Frontend Development" playbook, Activity 1: Setup Project:

1. Initialize with Create React App or Vite
2. Folder structure:
   - /src/components (reusable UI)
   - /src/pages (page-level)
   - /src/hooks (custom hooks)
   - /src/state (state management)
3. Configure ESLint and Prettier  
4. Set up Jest + React Testing Library

Upstream: None
Downstream: Create Components, Implement State Management

Would you like me to create a GitHub issue to track this?
```

---

#### Creating Work Items via External MCP

Maria responds:
```
> mimir: Yes, create a GitHub issue for project setup
```

**GitHub MCP** (external server) creates issue:
- **Repo**: maria/acme-dashboard
- **Issue #47**: "Setup React project structure per React Frontend Development playbook"
- **Body**: Includes checklist from Activity 1 (context from Mimir MCP)
- **Labels**: setup, react, playbook

Link returned to Maria.

---

#### Context-Aware Guidance

After completing work, Maria asks:
```
> mimir: What's next per the React playbook?
```

**MCP Response** (coordinated):
```
Checking MIMR-47 status... (GitHub MCP) ✓ Project structure complete.

Next activity per "React Frontend Development" (Mimir MCP):
Activity 2: Create Components

Prerequisites complete ✓
Ready to start component development.

Options:
1. Show full Activity 2 details? (Mimir MCP)
2. Create GitHub issue for components? (GitHub MCP)
3. Open playbook in browser? (Mimir MCP)
```

---

#### Auto-Open Playbook in Browser

Maria: `> mimir: Open playbook in browser`

**MCP Action** (Mimir MCP):
- Sends command to open browser
- URL: `http://localhost:8000/playbooks/react-frontend-dev`
- Browser opens showing FOB-PLAYBOOKS-VIEW_PLAYBOOK-1 (Act 2)
- Activity 1 marked complete (linked to MIMR-47)
- Activity 2 highlighted as next step

---

**Act 12 Summary**: Maria uses Mimir MCP for AI-assisted methodology execution:
- ✅ Activate playbooks in FOB
- ✅ Query playbook context via AI (Windsurf/MCP)
- ✅ Get activity-specific guidance
- ✅ Create work items via external MCPs (GitHub, Jira)
- ✅ Track progress and dependencies
- ✅ Auto-open playbook details in browser

**Integration Architecture**:
- **Mimir MCP** (FastMCP → REST): Playbook context, activities, artifacts, PIP submission — calls `BASE_URL/api/…` with `TOKEN`
- **External MCPs**: Work item management (GitHub, Jira, GitLab, etc.)
- **AI Coordination**: Cursor/Windsurf AI coordinates between MCPs for seamless workflow

**Key Benefits**:
- Playbook guidance embedded in development workflow
- No context switching between IDE and playbook docs
- Automated work item creation with playbook context
- Dependency tracking and progress visibility

**Next**: Maria configures FOB settings (ACT 13).

---

### Act 13: Settings & Preferences

**Context**: Maria needs to configure her FOB and account settings.

**MVP (implemented today)** — **FOB-PROFILE-1** (`/auth/user/profile/`): profile fields, **MCP/REST API token** (show, copy, regenerate with password), my PIPs, my playbooks. Reach it from the **username** dropdown in the top navigation bar.

**Target (full FOB Settings)** — **FOB-SETTINGS-1** below: multi-section settings UI (storage, MCP snippet builder, notifications, etc.).

#### Screen: FOB Settings - Main
Maria opens the full FOB Settings experience (target — not fully implemented in MVP):
- **Sidebar navigation**:
  - Account
  - Storage
  - MCP Configuration
  - Notifications
  - Privacy
  - Advanced
- **Account section** (default):
  - Profile information
  - Email: dpetelin@gmail.com
  - Full name: Maria Rodriguez
  - [Change Password] button
  - [Two-Factor Authentication] toggle
  - **Authentication Token** (for MCP) — *in MVP, viewing and regenerating this token is on **FOB-PROFILE-1**; this screen duplicates the story for the full Settings UX*:
    - Token: `mimir_a8f3...45678` [Show] [Copy]
    - Token created: Nov 15, 2024
    - [Regenerate Token] button (invalidates old token, requires re-entering password)
  - [Delete Account] (danger zone)

#### Screen: FOB Settings - Storage
Maria clicks **Storage**:
- **Local Database**:
  - Location: /Users/maria/.mimir/data
  - Size: 2.3 GB (4 playbooks, 127 activities)
  - [Change Location] button
- **Cache**:
  - Cache size: 142 MB
  - [Clear Cache] button
- **Cleanup**:
  - Orphaned artifacts: 0
  - Old versions: 12 (keeping latest 5 per playbook)
  - [Run Cleanup] button

#### Screen: FOB Settings - MCP Configuration
Maria clicks **MCP Configuration**:
- **FastMCP Server**: Mimir MCP is a FastMCP process that wraps the FOB REST API
- **Configuration snippet** (copy into Cursor/Windsurf MCP settings):
  ```json
  {
    "mimir": {
      "command": "python",
      "args": ["-m", "mcp_integration.server"],
      "env": {
        "BASE_URL": "http://localhost:8000",
        "TOKEN": "mimir_a8f3d9e2b1c4567890abcdef12345678"
      }
    }
  }
  ```
  - `BASE_URL`: FOB server URL [Edit] — `http://localhost:8000` (local) or `https://mimir.featurefactory.io` (hosted)
  - `TOKEN`: Your FOB authentication token [Show] [Regenerate]
  - **Note**: MCP requires a live FOB — the FastMCP container calls `BASE_URL/api/…` and cannot operate without it
  - [Copy Config Snippet] button
  - [Test MCP Connection] button
- **Mimir MCP Features**:
  - Enable playbook context: [On/Off]
  - Enable PIP submission via MCP: [On/Off]
  - Enable AI-initiated PIPs: [On/Off]
- **External MCP Servers** (configured separately in Cursor/Windsurf):
  - GitHub MCP (for work item management)
  - Jira MCP (optional)
  - GitLab MCP (optional)
  - Note: "Work item creation/tracking handled by external MCPs, not Mimir MCP"

#### Screen: FOB Settings - Notifications
Maria clicks **Notifications**:
- **Notification Preferences**:
  - Team join requests: [On/Off]
  - Playbook updates available: [On/Off]
  - PIP submissions: [On/Off]
  - PIP decisions (email + in-app): [On/Off]
  - System errors: [On/Off] (cannot be disabled)
- **Notification Method**:
  - In-app notifications: [On/Off]
  - Browser notifications: [On/Off]
  - Email notifications: [On/Off]
- **Quiet Hours**:
  - Enable: [On/Off]
  - From: 22:00
  - To: 08:00

**Act 13 Summary**: Maria configures FOB:
- ✅ **MVP:** Profile and MCP authentication token (including regenerate) on **FOB-PROFILE-1** via username menu **(shipped)**; full multi-section Account UI below is the target
- ✅ Account settings (profile, password, 2FA, MCP authentication token) — *target*
- ✅ Storage management and cleanup
- ✅ FastMCP configuration (BASE_URL + TOKEN snippet)
- ✅ Notification preferences (including PIP decision emails)
- ✅ Privacy and advanced settings

**Next**: Maria handles errors and edge cases (ACT 14).

---

### Act 14: Error Recovery & Edge Cases

**Context**: Maria encounters various error scenarios and learns how to recover.

#### Error Scenario 1: Permission Denied

##### Screen: FOB Playbook Editor - Permission Error
Maria tries to edit Mike's React playbook:
- Error modal: 🚫 "Permission Denied"
- "You don't have permission to edit this playbook"
- **Reason**: "This playbook is owned by Mike Chen (Usability team)"
- **Options**:
  - "You can create a local copy and modify it"
  - "Submit a PIP to suggest changes"
- **Actions**:
  - [Create Local Copy] button
  - [Submit PIP] button
  - [Cancel]

Maria clicks [Submit PIP] which opens PIP creation flow.

**Result**: Clear error messaging with actionable recovery paths.

#### Error Scenario 2: Corrupted Playbook

##### Screen: FOB Dashboard - Playbook Error
A playbook shows error icon:
- Warning badge: ⚠️ on "Old Frontend Patterns" playbook card
- Click reveals: "Data corruption detected"
- **Details**:
  - Corrupted activities: 2 of 8
  - Last successful load: 3 days ago
  - Cause: Unknown (possibly interrupted write)
- **Recovery Actions**:
  - [Restore from Local Backup] button
  - [Import from Exported File] button (if previously exported)
  - [Delete Corrupted Data] button
  - [Export Salvageable Content] button

**Result**: Maria can recover from data corruption scenarios.

#### Empty State Scenarios

##### Screen: FOB Dashboard - No Playbooks
When Maria first starts (empty state):
- Illustration: Empty box graphic
- Heading: "No playbooks yet"
- Subtext: "Get started by creating a playbook, exploring team playbooks, or importing from a file"
- **Actions**:
  - [Create Your First Playbook] button (primary)
  - [Browse Teams] button
  - [Import from File] button
  - [Watch Tutorial] link

##### Screen: FOB Team Browser - No Results
Maria searches for non-existent team:
- Illustration: Magnifying glass
- Heading: "No teams found matching 'blockchain'"
- Subtext: "Try adjusting your search or browse all teams"
- **Suggestions**:
  - Similar teams: (list of related results)
  - [Clear Filters] button
  - [Create New Team] button

**Result**: Every empty or error state provides clear guidance and next steps.

---

**Act 14 Summary**: Maria handles errors gracefully:
- ✅ Permission errors with clear alternatives (local copy or PIP)
- ✅ Data corruption with backup/restore
- ✅ Empty states with helpful guidance

**Key Point**: All errors provide actionable recovery paths, never dead ends.

---

## Journey Complete

Maria's journey through Acts 0-14 demonstrates the complete Mimir MVP experience:

**Core CRUDLF Entities (Acts 2-8):**
- ✅ **Playbooks**: Top-level methodologies with versioning and team publishing
- ✅ **Workflows**: Execution sequences with optional phase organization  
- ✅ **Phases**: Optional activity groupings (clearly marked as optional)
- ✅ **Activities**: Core work units with dependencies, agents, and artifacts
- ✅ **Artifacts**: Outputs produced by activities (no more "Deliverable")
- ✅ **Agents**: AI assistant personas assigned to activities
- ✅ **Skills**: Step-by-step activity guides (1:1 with activities)

**Supporting Features (Acts 9-14):**
- ✅ **PIPs**: Structured improvement proposals (ADD/ALTER/DROP Changes) with Galdr AI review and Admin decision
- ✅ **Import/Export**: Offline distribution via JSON/MPA files
- ✅ **Team Management**: Public/private communities with admin workflows
- ✅ **MCP Integration**: AI-assisted methodology execution via FastMCP → REST API (BASE_URL + TOKEN)
- ✅ **Settings**: Account, token management, FastMCP config, notifications
- ✅ **Error Recovery**: Graceful handling of failure scenarios

**Key Achievements:**
- All 7 core entities have complete CRUDLF with LIST+FIND entry points
- Consistent naming: `FOB-{ENTITY}-{OPERATION}-{VERSION}`
- Phase explicitly marked as OPTIONAL throughout
- "Artifact" terminology (not "Deliverable")
- Detailed screen specifications ready for BDD feature files
- Structured PIP workflow with Galdr AI pre-screening + Admin decision + email notification
- FastMCP as API wrapper (no direct DB access from MCP layer)
- Error recovery paths for all scenarios

Maria now has a complete, production-ready methodology management system with team collaboration, Galdr-assisted PIP review, and AI integration via FastMCP.
