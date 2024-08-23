# This repo is a demonstration of testing a state machine running as a server

There are two levels of testing:
1. dev tests: for testing and developing the state machine server
2. feature tests: for testing the machine

The main purpose is to demonstrate how the features tests need to allow for working with a system whose state persists between tests and changes with a significant duration. The server serves its state as (1) a rest (call/return) interface; and (2) a websocket (pub/sub). Therefore, it allows for subscribing to the state changes whilst commanding states to be changed. Commanding the state to be changed can either be done as a "blocking call" or a non blocking call (background). The commands can be set with a specific duration to take place to simulate changes that may take some time. This allows for demonstrating the scenario where the system is busy changing state whilst attempting to perform a next command (resulting in am 405 error).

The interface to the server is done via an intermediate proxy object.

Although the dev tests can be ran with mock replacesments, the feature tests requires the fastapi dev server to be started (see below).

## Running the fastapi server in dev mode:

```
poetry run fastapi dev mv/server.py
```