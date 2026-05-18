Feature: FOB-PROFILE-EDIT-1 Edit My Profile and Manage API Token
  As a methodology author (Maria)
  I want to update my account fields and rotate my API token
  So that my identity is current and my MCP / REST integrations stay secure

  Background:
    Given Maria is authenticated in FOB
    And she is on FOB-PROFILE-VIEW-1
    And she clicks [Edit] in the Account card header

  # ── Edit form — navigation ────────────────────────────────────────────────

  Scenario: FOB-PROFILE-EDIT-00 Edit button opens the edit form
    Then she is redirected to FOB-PROFILE-EDIT-1 at /auth/user/profile/edit/
    And the page title reads "Edit profile"
    And data-testid="profile-edit-form" is present
    And the form is pre-populated with her current first name, last name, and email
    And the Username field is disabled (cannot be changed)

  Scenario: FOB-PROFILE-EDIT-00b Cancel returns to profile view without changes
    Given she is on the Edit Profile form
    When she clicks [Cancel]
    Then she is redirected to FOB-PROFILE-VIEW-1
    And no data has been changed

  # ── Edit form — happy path ────────────────────────────────────────────────

  Scenario: FOB-PROFILE-EDIT-00c Save name-only changes
    Given she is on the Edit Profile form
    When she changes First name to "Marie" and leaves email unchanged
    And she clicks [Save changes]
    Then she is redirected to FOB-PROFILE-VIEW-1
    And a success banner reads "Profile updated."
    And the Account card shows "First name: Marie"
    And no verification email is sent
    And her session remains active

  # ── Email change + verification lockout ──────────────────────────────────

  Scenario: FOB-PROFILE-EDIT-05 Warning banner appears when email field is changed
    Given Maria's current email is "dpetelin@gmail.com"
    And she is on the Edit Profile form
    When she changes the Email field to "dpetelin-new@gmail.com"
    Then an orange warning banner appears below the Email field (data-testid="email-change-warning"):
      """
      ⚠️ Changing your email will require re-verification.
      You will be logged out and your API token invalidated until the new address is verified.
      """
    And the banner appears client-side on input (before submit)

  Scenario: FOB-PROFILE-EDIT-06 Saving a changed email logs user out and revokes token
    Given she changes the Email field to "dpetelin-new@gmail.com"
    When she clicks [Save changes]
    Then her session is terminated
    And her API token is invalidated
    And a verification email is sent to "dpetelin-new@gmail.com"
    And she is redirected to the login page with warning banner:
      """
      Email updated. Please verify your new address before logging in again.
      """

  Scenario: FOB-PROFILE-EDIT-07 No warning shown when email field is unchanged
    Given she is on the Edit Profile form
    When she changes only her First name (email field is untouched)
    Then the email verification warning banner is not shown

  # ── Edit form — validation ────────────────────────────────────────────────

  Scenario: FOB-PROFILE-EDIT-08 Email field is required
    Given she is on the Edit Profile form
    When she clears the Email field and clicks [Save changes]
    Then she sees an inline error on the email field:
      "Email is required."
    And she stays on FOB-PROFILE-EDIT-1

  Scenario: FOB-PROFILE-EDIT-09 Email must be unique across accounts
    Given another user already has email "taken@example.com"
    When Maria changes her email to "taken@example.com" and clicks [Save changes]
    Then she sees an inline error on the email field:
      "That email is already used by another account."
    And she stays on FOB-PROFILE-EDIT-1
    And her email is unchanged

  # ── Token regeneration (on FOB-PROFILE-VIEW-1) ───────────────────────────

  # These scenarios act on the Regenerate token form embedded in the profile view,
  # submitted via POST to /auth/user/profile/regenerate-token/.

  Scenario: FOB-PROFILE-EDIT-01 Regenerate token with correct password
    Given the Regenerate token form is visible (data-testid="profile-token-regenerate-form")
    When she enters her current password in data-testid="profile-token-regenerate-password"
    And she clicks [Regenerate token] (data-testid="profile-token-regenerate-submit")
    Then she is redirected back to FOB-PROFILE-VIEW-1
    And a success banner reads:
      "Your API token was regenerated. Update MCP, scripts, and any clients that use the old token."
    And the token field shows a new token value
    And the old token no longer authenticates API requests

  Scenario: FOB-PROFILE-EDIT-02 Regenerate token rejected when password is wrong
    Given the Regenerate token form is visible
    When she enters an incorrect password and clicks [Regenerate token]
    Then she is redirected back to FOB-PROFILE-VIEW-1
    And an error banner reads "Incorrect password. Your API token was not changed."
    And the token value is unchanged

  Scenario: FOB-PROFILE-EDIT-03 Regenerate token rejected when password field is empty
    Given the Regenerate token form is visible
    When she submits the form with an empty password field
    Then she is redirected back to FOB-PROFILE-VIEW-1
    And an error banner reads "Enter your current password to regenerate the API token."
    And the token value is unchanged

  Scenario: FOB-PROFILE-EDIT-04 POST endpoint requires authentication
    Given Maria is not logged in
    When a POST request is sent to /auth/user/profile/regenerate-token/
    Then the response is a redirect to the login page
