Feature: Configure State Machine Tests

    Scenario: Configure Scan
        Given a running state machine on a server
        Given a machine that is in IDLE state
        When I configure it for a scan
        Then the machine should first go into CONFIGURING state
        Then the machine should go into READY state and remain there

    Scenario: Clear Configure
        Given a running state machine on a server
        Given a machine that is in READY state
        When I clear the configuration
        Then the machine should be in IDLE state

    Scenario: Background Configure Scan
        Given a running state machine on a server
        Given a machine that is in IDLE state
        When (in the background) I configure it for a scan
        Then the machine should first go into CONFIGURING state
        Then the machine should go into READY state and remain there

    Scenario: Background Clear Configure
        Given a running state machine on a server
        Given a machine that is in READY state
        When (in the background) I clear the configuration
        Then the machine should be in IDLE state

    Scenario: Configure Scan when state machine is CONFIGURING
        Given a running state machine on a server
        Given a machine that is in IDLE state
        When (in the background) I configure it for a scan
        When I command it again to configure
        Then the server should reject the command