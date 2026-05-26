Feature: FOB-TEAMS-VIEW-1 View Team Details, Join, and Leave
  As a methodology author (Maria)
  I want to view a team's details, playbooks, and members — and join or leave teams
  So that I can decide whether to participate and access shared methodologies

  Background:
    Given Maria is authenticated in FOB
    And the "Usability" team exists with:
      | field       | value                                          |
      | Description | Best practices for usable software development |
      | Visibility  | Public                                         |
      | Join Policy | Auto-approve                                   |
      | Category    | Engineering                                    |
      | Admin       | Mike Chen (mchen)                              |
    And the "Usability" team has 127 members
    And the "Usability" team has playbooks:
      | name                       | version |
      | React Frontend Development | 1.2     |
      | Accessible Design Patterns | 0.9     |

  # ── Navigation ────────────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-01 Navigate to team detail from the team browser
    Given Maria is on /teams/
    When she clicks on the "Usability" team card
    Then she is redirected to /teams/<pk>/
    And the page title reads "Usability"
    And data-testid="team-detail-page" is present

  # ── Info card ─────────────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-02 Team detail info card shows all metadata
    Given Maria is on the "Usability" team detail page
    Then data-testid="team-info-card" shows:
      | field       | value                                          |
      | Name        | Usability                                      |
      | Description | Best practices for usable software development |
      | Category    | Engineering                                    |
      | Visibility  | Public                                         |
      | Join Policy | Auto-approve                                   |
      | Members     | 127                                            |
      | Admin       | Mike Chen                                      |

  # ── Playbooks tab ─────────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-03 Playbooks tab lists all team playbooks with links
    Given Maria is on the "Usability" team detail page
    When she clicks the "Playbooks" tab (data-testid="team-tab-playbooks")
    Then she sees a table with rows:
      | name                       | version |
      | React Frontend Development | v1.2    |
      | Accessible Design Patterns | v0.9    |
    And each row has a [View] link pointing to /playbooks/<pk>/

  Scenario: FOB-TEAMS-VIEW-04 Empty playbooks tab shows placeholder
    Given the "Usability" team has no playbooks submitted
    When Maria is on the Playbooks tab
    Then she sees "This team has no playbooks yet."

  # ── Members tab ───────────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-05 Members tab shows member list with roles and join dates
    Given Maria is on the "Usability" team detail page
    When she clicks the "Members" tab (data-testid="team-tab-members")
    Then she sees a table with columns: Name, Username, Role, Joined
    And Mike Chen is in the list with role "Admin"
    And the table shows at most 25 members per page

  # ── Join / Leave buttons — visibility rules ───────────────────────────────

  Scenario: FOB-TEAMS-VIEW-06 Non-member sees [Join Team] button on a public team
    Given Maria is NOT a member of "Usability"
    When she is on the "Usability" team detail page
    Then a [Join Team] button is visible (data-testid="team-join-btn")
    And no [Leave Team] button is visible
    And no [Manage Team] button is visible

  Scenario: FOB-TEAMS-VIEW-07 Member sees [Leave Team] button instead of [Join Team]
    Given Maria IS a member (not admin) of "Usability"
    When she is on the "Usability" team detail page
    Then a [Leave Team] button is visible (data-testid="team-leave-btn")
    And no [Join Team] button is visible

  Scenario: FOB-TEAMS-VIEW-08 Admin sees [Manage Team] button and no join/leave buttons
    Given Maria is the admin of the "UX" team
    When she is on the "UX" team detail page
    Then a [Manage Team] button is visible (data-testid="team-manage-btn")
    And no [Join Team] button is visible
    And no [Leave Team] button is visible

  # ── Join — auto-approve ───────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-09 Join a team with Auto-approve policy adds Maria immediately
    Given Maria is NOT a member of "Usability" (Join Policy: Auto-approve)
    When she is on the "Usability" team detail page
    And she clicks [Join Team]
    Then Maria is immediately added to the "Usability" team
    And a success banner reads "You've joined the Usability team."
    And the [Join Team] button is replaced by [Leave Team]
    And the member count increments to 128
    And the team's playbooks appear accessible on Maria's dashboard
    And the browser console logs "[teams] joined team: Usability"

  # ── Join — requires approval ───────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-10 Join request sent for a team requiring approval
    Given the "UX" team exists with Join Policy "Requires Approval"
    And Maria is NOT a member of "UX"
    When she is on the "UX" team detail page
    And she clicks [Join Team]
    Then a success banner reads "Your request to join 'UX' has been sent. Awaiting approval."
    And the [Join Team] button changes to a disabled "Request Pending" state (data-testid="team-join-pending-btn")
    And the "UX" team admin (Maria's other account or Mike) receives a notification about the request
    And Maria is NOT yet listed as a member in the Members tab

  Scenario: FOB-TEAMS-VIEW-11 Pending request cannot be submitted twice
    Given Maria has a pending join request for "UX"
    When she revisits the "UX" team detail page
    Then the [Join Team] button remains in "Request Pending" state (disabled)
    And no second request is submitted

  # ── Join — invite only ────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-12 Invite-only team shows no Join button and an explanation
    Given the "Acme, INC" team exists with Join Policy "Invite Only"
    And Maria is NOT a member of "Acme, INC"
    When she is on the "Acme, INC" team detail page
    Then no [Join Team] button is visible
    And a notice reads "This team accepts new members by invitation only."

  # ── Leave team ────────────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-13 Regular member leaves a team and loses access to team playbooks
    Given Maria is a member (not admin) of "Usability"
    And she has access to "React Frontend Development" via the team
    When she is on the "Usability" team detail page
    And she clicks [Leave Team]
    Then a confirmation dialog appears:
      """
      Leave team 'Usability'? You will lose access to playbooks shared by this team.
      """
    When she confirms
    Then Maria is removed from the "Usability" team
    And a banner reads "You have left the Usability team."
    And "React Frontend Development" no longer appears on Maria's dashboard
    And Maria's personally owned playbooks are NOT affected

  Scenario: FOB-TEAMS-VIEW-14 Leave team confirmation cancelled keeps Maria as member
    Given Maria is a member of "Usability"
    When she clicks [Leave Team] and then clicks [Cancel] in the confirmation dialog
    Then she stays on the "Usability" team detail page
    And her membership is unchanged

  Scenario: FOB-TEAMS-VIEW-15 Admin cannot leave team without first transferring admin
    Given Maria is the admin of the "UX" team which has other members
    When she clicks [Leave Team]
    Then a warning dialog appears:
      """
      You are the admin of 'UX'. Transfer admin rights to another member before leaving.
      """
    And the leave action is blocked
    And Maria remains the admin of "UX"

  # ── Hidden team access control ────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-16 Hidden team detail page is inaccessible to non-members
    Given the "Acme, INC" team has Visibility "Hidden"
    And Mike is NOT a member of "Acme, INC"
    When Mike navigates directly to /teams/<acme-pk>/
    Then he receives a 404 Not Found response

  # ── Unauthenticated ───────────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-17 Unauthenticated access is redirected to login
    Given Maria is not logged in
    When she navigates to /teams/<pk>/
    Then she is redirected to the login page
    And after login she is returned to /teams/<pk>/

  # ── Email notifications ────────────────────────────────────────────────

  Scenario: FOB-TEAMS-VIEW-18 Auto-join sends confirmation email to the user
    Given Maria is NOT a member of "Usability" (Join Policy: Auto-approve)
    When she clicks [Join Team] and is immediately added
    Then Maria receives an email at her registered address with:
      | field   | value                                              |
      | Subject | You've joined the Usability team                   |
      | Body    | contains team name, description, link to /teams/<pk>/ |
    And the email contains a [View Team] button linking to /teams/<pk>/

  Scenario: FOB-TEAMS-VIEW-19 Join request sends approval-request email to the team admin
    Given the "UX" team exists with Join Policy "Requires Approval"
    And Maria is NOT a member of "UX"
    When she clicks [Join Team]
    Then the admin of "UX" receives an email with:
      | field   | value                                                           |
      | Subject | New join request for your team "UX"                            |
      | Body    | contains requester name, username, and request timestamp       |
    And the email contains a [Review Requests] button linking to /teams/<pk>/manage/?tab=join-requests
    And the email does NOT grant approve/reject without login (all actions require authentication)
