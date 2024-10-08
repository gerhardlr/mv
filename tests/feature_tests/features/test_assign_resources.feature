Feature: Assign Resources State Machine Tests

    Scenario: Assign Resources
        Given a running state machine on a server
        Given a machine that is On
        When I assign resources to it
        Then the machine should first go into RESOURCING state
        Then the machine should go into IDLE state and remain there

    Scenario: Release Resources
        Given a running state machine on a server
        Given a machine that is in IDLE state
        When I release the resources
        Then the machine should first go into RESOURCING state
        Then the machine should be in EMPTY state

    Scenario: Background Assign Resources
        Given a running state machine on a server
        Given a machine that is On
        When (in the background) I assign resources to it
        Then the machine should first go into RESOURCING state
        Then the machine should go into IDLE state and remain there

    Scenario: Background Release Resources
        Given a running state machine on a server
        Given a machine that is in IDLE state
        When (in the background) I release the resources
        Then the machine should first go into RESOURCING state
        Then the machine should be in EMPTY state

    Scenario: Assign Resources when state machine is RESOURCING
        Given a running state machine on a server
        Given a machine that is On
        When (in the background) I assign resources to it
        When I command it again to assign resources
        Then the server should reject the command