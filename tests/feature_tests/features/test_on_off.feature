Feature: On/OFF State Machine Tests

    Scenario: Switch System On
        Given a running state machhine on a server
        Given a machine that is Off
        When I command it to switch on
        Then the server should be on

    Scenario: Switch System Off
        Given a running state machhine on a server
        Given a machine that is On
        When I command it to switch off
        Then the server should be off

    Scenario: Background Switch System On
        Given a running state machhine on a server
        Given a machine that is Off
        When (in the background) I command it to switch on
        Then the server should first be off
        Then the server should be on

    Scenario: Background Switch System Off
        Given a running state machhine on a server
        Given a machine that is On
        When (in the background) I command it to switch off
        Then the server should first be on
        Then the server should be off

    Scenario: Commanding System on before finished
        Given a running state machhine on a server
        Given a machine that is Off
        When (in the background) I command it to switch on
        When I command it again to switch On
        Then the server should reject the command