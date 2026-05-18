Feature: ✅ FOB-ONBOARDING-1 First-Time User Onboarding
  As a new user (Maria)
  I want to complete onboarding after verifying my email
  So that I understand how to use FOB before working on my first playbook

  # Flow: Register → verify email → sign in → FOB-ONBOARDING-1 (first login only)

  Scenario: ✅ FOB-FIRST-RUN-01 Onboarding shown on first login after email verification
    Given Maria has registered and verified her email
    When she signs in for the first time
    Then she lands on FOB-ONBOARDING-1
    And she sees a "Welcome to Mimir" message
    And she sees an onboarding steps overview

  Scenario: FOB-FIRST-RUN-02 Create first playbook during onboarding
    Given Maria is in onboarding
    When she clicks [Create My First Playbook]
    Then she is guided through playbook creation
    And she creates a sample playbook

  Scenario: FOB-FIRST-RUN-03 Tour of features
    Given Maria completed her first playbook in onboarding
    When she proceeds with the tour
    Then she sees highlights of: Workflows, Activities, Artifacts, API Token

  Scenario: ✅ FOB-FIRST-RUN-04 Skip onboarding
    Given Maria is in onboarding
    When she clicks [Skip Tour]
    Then she is redirected to FOB-DASHBOARD-1
    And onboarding is not shown again on subsequent logins

  Scenario: FOB-FIRST-RUN-05 Complete onboarding
    Given Maria finished the tour
    When she clicks [Get Started]
    Then onboarding is marked complete
    And she is redirected to FOB-DASHBOARD-1
    And onboarding is not shown again on subsequent logins

  Scenario: ✅ FOB-FIRST-RUN-06 Subsequent logins skip onboarding
    Given Maria has already completed or skipped onboarding
    When she signs in again
    Then she is redirected directly to FOB-DASHBOARD-1
    And FOB-ONBOARDING-1 is not shown
