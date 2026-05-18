Feature: FOB-EMAIL-VERIFY-1 Email address verification
  As a methodology author (Maria)
  I want my email address to be verified
  So that FOB can trust my identity and I can log in and use the platform

  # ── Post-registration ────────────────────────────────────────────────────

  Scenario: FOB-EMAIL-VERIFY-01 Verification email sent on registration
    Given Maria has just created a new account with email "dpetelin@gmail.com"
    Then she receives an email with subject "Verify your Mimir email address"
    And the email contains a verification link matching /auth/user/verify-email/<token>/
    And she is redirected to the login page with message:
      """
      Account created. Please check your inbox and verify your email before logging in.
      """

  Scenario: FOB-EMAIL-VERIFY-02 Unverified user cannot log in
    Given Maria has registered but not yet verified her email
    When she enters valid credentials on the login page
    And she clicks [Login]
    Then she is NOT authenticated
    And she sees the message:
      """
      Please verify your email address before logging in.
      Check your inbox for a verification link.
      """
    And a [Re-send verification email] link is shown on the login page

  Scenario: FOB-EMAIL-VERIFY-03 Clicking verification link logs user in
    Given Maria's email is "Not verified"
    And she has a valid verification link in her inbox
    When she clicks the verification link
    Then her email is marked as "Verified"
    And she sees a success message "Your email address has been verified. You can now log in."
    And she is redirected to the login page

  Scenario: FOB-EMAIL-VERIFY-04 Expired verification link shows error with re-send option
    Given Maria's verification link is more than 24 hours old
    When she clicks the expired link
    Then she sees an error message "This verification link has expired."
    And she sees a [Re-send verification email] button
    When she clicks [Re-send verification email]
    Then she sees "A new verification email has been sent to dpetelin@gmail.com"

  Scenario: FOB-EMAIL-VERIFY-05 Already-verified link is handled gracefully
    Given Maria's email is already "Verified"
    When she clicks an old verification link
    Then she sees "Your email address is already verified."
    And she is redirected to the login page

  Scenario: FOB-EMAIL-VERIFY-06 Re-send verification email from login page
    Given Maria is on the login page and sees the "verify your email" message
    When she clicks [Re-send verification email]
    Then she sees "A new verification email has been sent to dpetelin@gmail.com"
    And the link is valid for 24 hours

  # ── Email change → re-verification lockout ───────────────────────────────

  Scenario: FOB-EMAIL-VERIFY-07 Changing email logs user out and revokes token
    Given Maria is authenticated with email "dpetelin@gmail.com"
    And she has an active API token
    When she changes her email to "dpetelin-new@gmail.com" on the Edit Profile form
    And she clicks [Save changes]
    Then her session is terminated immediately
    And her API token is invalidated
    And a verification email is sent to "dpetelin-new@gmail.com"
    And she is redirected to the login page with message:
      """
      Email updated. Please verify your new address before logging in again.
      """

  Scenario: FOB-EMAIL-VERIFY-08 Re-verified user can log in and gets a new token
    Given Maria's email was changed and is "Not verified"
    When she clicks the verification link in her new inbox
    Then her email is marked as "Verified"
    And she is redirected to the login page with message "Your email address has been verified. You can now log in."
    When she logs in with valid credentials
    Then she is authenticated and redirected to FOB-DASHBOARD-1
    And a new API token is generated for her automatically

  # ── Staff bypass ──────────────────────────────────────────────────────────

  Scenario: FOB-EMAIL-VERIFY-09 Staff accounts skip verification entirely
    Given Maria is a staff or superuser account
    When she changes her email on the Edit Profile form
    Then her session is NOT terminated
    And her API token is NOT invalidated
    And no verification email is sent
    And her email shows the "Verified" badge immediately
