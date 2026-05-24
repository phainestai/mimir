Feature: FOB-AUTH-LOGIN-1 Authentication and Login
  As a methodology author (Maria)
  I want to securely log into FOB
  So that I can access my playbooks

  # ── Login ────────────────────────────────────────────────────────────────

  Scenario: ✅ FOB-STARTUP-01 Sign in with valid credentials
    Given Maria is on the FOB login page at /auth/login/
    When she enters her username and password
    And she clicks [Sign in]
    Then she is authenticated
    And she is redirected to FOB-DASHBOARD-1

  Scenario: ✅ FOB-STARTUP-02 Sign in with invalid credentials
    Given Maria is on the FOB login page
    When she enters an invalid username or password
    And she clicks [Sign in]
    Then she sees "Invalid username or password." error (data-testid="login-error")
    And she is NOT authenticated

  Scenario: ✅ FOB-STARTUP-03 Password reset flow
    Given Maria forgot her password
    When she clicks [Forgot password?] on the login page
    And she enters her email
    Then she receives a reset link
    When she clicks the link and sets a new password
    Then she can sign in with the new password

  Scenario: ✅ FOB-STARTUP-04 Logout
    Given Maria is logged in
    When she clicks [Logout] from the username dropdown
    Then she is logged out
    And she is redirected to the login page

  Scenario: ✅ FOB-STARTUP-05 Remember me extends session
    Given Maria is on the login page
    When she ticks [Remember me for 30 days] and signs in
    Then her session cookie persists for 30 days

  # ── Guest-only guards (logged-in users) ───────────────────────────────────

  Scenario: FOB-AUTH-GUARD-01 Logged-in user cannot access login page
    Given Maria is logged in
    When she navigates to /auth/user/login/
    Then she is redirected to FOB-PROFILE-VIEW-1 at /auth/user/profile/
    And she does NOT see the login form

  Scenario: FOB-AUTH-GUARD-02 Logged-in user cannot access registration page
    Given Maria is logged in
    When she navigates to /auth/user/register/
    Then she is redirected to FOB-PROFILE-VIEW-1 at /auth/user/profile/
    And she does NOT see the registration form

  Scenario: FOB-AUTH-GUARD-03 Logged-in POST to login is redirected without re-auth
    Given Maria is logged in
    When she POSTs credentials to /auth/user/login/
    Then she is redirected to FOB-PROFILE-VIEW-1 at /auth/user/profile/
    And she remains authenticated as Maria

  # ── Registration ──────────────────────────────────────────────────────────

  Scenario: FOB-LOCAL-USER-CREATE-01 First-time user registration
    Given Maria is a new user
    When she navigates to the registration page at /auth/register/
    Then she sees fields in order:
      | field            | required |
      | First name       | yes      |
      | Last name        | yes      |
      | Username         | yes      |
      | Email address    | yes      |
      | Password         | yes      |
      | Confirm password | yes      |
    And she sees a required ToS checkbox:
      "I agree to the Terms of Service and Privacy Policy"
    And the [Create account] button is disabled until the checkbox is ticked
    When she fills in all fields and ticks the ToS checkbox
    And she clicks [Create account]
    Then her account is created with accepted_tos_at recorded
    And she is redirected to the login page with info banner:
      """
      Account created. Please check your inbox and verify your email before logging in.
      """

  Scenario: FOB-LOCAL-USER-CREATE-02 Registration blocked without ToS acceptance
    Given Maria is on the registration page
    When she fills in all fields but does NOT tick the ToS checkbox
    Then the [Create account] button is disabled
    And if she submits via keyboard she sees:
      "You must accept the Terms of Service to register."
    And no account is created

  Scenario: FOB-LOCAL-USER-CREATE-03 ToS and Privacy Policy links open in new tab
    Given Maria is on the registration page
    When she clicks [Terms of Service]
    Then the Terms of Service page opens in a new browser tab
    When she clicks [Privacy Policy]
    Then the Privacy Policy page opens in a new browser tab

  Scenario: FOB-LOCAL-USER-CREATE-04 Registration blocked for duplicate username
    Given an account already exists for username "taken"
    When Maria attempts to register with username "taken"
    And she clicks [Create account]
    Then she sees an inline error on the username field:
      "That username is already taken."
    And no new account is created

  Scenario: FOB-LOCAL-USER-CREATE-05 Registration blocked for duplicate email
    Given an account already exists for "used@example.com"
    When Maria attempts to register with email "used@example.com"
    And she clicks [Create account]
    Then she sees an inline error on the email field:
      "That email is already registered."
    And no new account is created

  Scenario: FOB-LOCAL-USER-CREATE-06 Password and confirm must match
    Given Maria is on the registration page
    When she enters different values in Password and Confirm password
    And she clicks [Create account]
    Then she sees an inline error:
      "Passwords do not match."
    And no account is created

  Scenario: FOB-LOCAL-USER-CREATE-07 Username must be 3–30 characters
    Given Maria is on the registration page
    When she enters username "ab" (too short)
    And she clicks [Create account]
    Then she sees an inline error on the username field:
      "Username must be between 3 and 30 characters."
    And no account is created

  Scenario: FOB-LOCAL-USER-CREATE-08 Password show/hide toggle
    Given Maria is on the registration page
    When she clicks the eye icon next to the Password field
    Then both Password and Confirm password fields reveal their values
    When she clicks the icon again
    Then both fields mask their values
