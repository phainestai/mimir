Feature: FOB-PROFILE-VIEW-1 View My Profile
  As a methodology author (Maria)
  I want to view my account details, API token, PIPs, and playbooks in one place
  So that I can see who I am in the system and what I own

  Background:
    Given Maria is authenticated in FOB
    And Maria has first name "Denis", last name "Petelin", username "dpetelin", email "dpetelin@gmail.com"
    And Maria has an API token issued

  Scenario: FOB-PROFILE-VIEW-01 Open profile from username dropdown
    Given Maria is anywhere in FOB
    When she clicks her username in the top navigation bar
    Then a dropdown opens with items:
      | item         |
      | View Profile |
      | Logout       |
    When she clicks [View Profile]
    Then she is redirected to FOB-PROFILE-VIEW-1 at /auth/user/profile/
    And the page title reads "My profile"
    And data-testid="profile-page" is present

  Scenario: FOB-PROFILE-VIEW-02 Account card shows identity fields
    Given Maria is on FOB-PROFILE-VIEW-1
    Then the Account card displays:
      | field      | value                    |
      | First name | Denis               |
      | Last name  | Petelin             |
      | Email      | dpetelin@gmail.com  |
      | Username   | dpetelin (monospace)|
    And each field is read-only (not an editable input)

  Scenario: FOB-PROFILE-VIEW-02b Email row shows Verified badge when email is confirmed
    Given Maria's email "dpetelin@gmail.com" has been verified
    When she is on FOB-PROFILE-VIEW-1
    Then the email row shows a green "Verified" badge (data-testid="email-verified-badge")
    And the [Re-send verification email] button is not present

  # NOTE: Scenarios 02c and 02d apply only to staff/superuser accounts.
  # Regular users with an unverified email are blocked at login and cannot reach this page.
  # Staff bypass the login gate so they can see and manage their own unverified state.

  Scenario: FOB-PROFILE-VIEW-02c Staff user sees Not Verified badge and re-send button
    Given Maria is a staff account
    And her email "dpetelin@gmail.com" has NOT been verified
    When she is on FOB-PROFILE-VIEW-1
    Then the email row shows an orange "Not verified" badge (data-testid="email-unverified-badge")
    And a [Re-send verification email] button is visible (data-testid="resend-verification-btn")

  Scenario: FOB-PROFILE-VIEW-02d Staff user re-sends verification email
    Given Maria is a staff account with an unverified email
    And she is on FOB-PROFILE-VIEW-1
    When she clicks [Re-send verification email]
    Then she stays on FOB-PROFILE-VIEW-1
    And a success message appears: "A verification email has been sent to dpetelin@gmail.com"
    And the [Re-send verification email] button shows a cooldown state to prevent spam

  Scenario: FOB-PROFILE-VIEW-03 API token is hidden by default
    Given Maria is on FOB-PROFILE-VIEW-1
    Then the token field data-testid="profile-token-field" is present
    And the input type is "password" (value is masked)
    And the [Show] button is visible (data-testid="profile-token-toggle")
    And the [Copy] button is visible (data-testid="profile-token-copy")

  Scenario: FOB-PROFILE-VIEW-04 Reveal token with Show button
    Given Maria is on FOB-PROFILE-VIEW-1
    When she clicks [Show]
    Then the token field type changes to "text" (value is visible)
    And the [Show] button label changes to [Hide]
    When she clicks [Hide]
    Then the token field type returns to "password"

  Scenario: FOB-PROFILE-VIEW-05 Copy token to clipboard
    Given Maria is on FOB-PROFILE-VIEW-1
    When she clicks [Copy]
    Then the raw token value is written to the clipboard
    And the browser console logs "[profile] token copied to clipboard"

  Scenario: FOB-PROFILE-VIEW-06 My PIPs table shows her submissions
    Given Maria has submitted PIPs:
      | title                        | playbook                    | status    |
      | Add accessibility audit step | React Frontend Development  | submitted |
      | Refactor BPE-02 guidance     | FeatureFactory v3.8         | draft     |
    When Maria is on FOB-PROFILE-VIEW-1
    Then data-testid="profile-pips-table" shows both rows
    And each row displays: title, playbook name, status badge, [View] link
    And [View] links point to /pips/<pk>/

  Scenario: FOB-PROFILE-VIEW-07 Empty PIPs state
    Given Maria has created no PIPs
    When she is on FOB-PROFILE-VIEW-1
    Then the PIPs card shows "You have not created any PIPs yet."
    And data-testid="profile-pips-table" is not present

  Scenario: FOB-PROFILE-VIEW-08 My Playbooks table shows her authored playbooks
    Given Maria owns playbooks:
      | name                        | version | status   |
      | Product Discovery Framework | 1.0     | released |
      | Agile Sprint Retrospectives | 0.2     | draft    |
    When Maria is on FOB-PROFILE-VIEW-1
    Then data-testid="profile-playbooks-table" shows both rows
    And each row displays: name, version (e.g. "v1.0"), status badge, [View] link
    And [View] links point to /playbooks/<pk>/

  Scenario: FOB-PROFILE-VIEW-09 Empty Playbooks state
    Given Maria owns no playbooks
    When she is on FOB-PROFILE-VIEW-1
    Then the Playbooks card shows "You do not own any playbooks yet."
    And data-testid="profile-playbooks-table" is not present

  Scenario: FOB-PROFILE-VIEW-10 Unauthenticated access is redirected
    Given Maria is not logged in
    When she navigates to /auth/user/profile/
    Then she is redirected to the login page
    And after login she returns to /auth/user/profile/
