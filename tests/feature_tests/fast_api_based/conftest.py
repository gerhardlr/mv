from assertpy import assert_that
from mv.client import Proxy
from requests import HTTPError
from pytest_bdd import given, then

from mv.client import RealClient, set_use_server_ws

from .subscriber import Subscriber
from ..contextmanagement import StackableContext

# --- Givens ---


@given("a running state machine on a server", target_fixture="setup")
def given_a_running_state_machhine_on_a_server(context: StackableContext):
    """"""
    client = RealClient()
    proxy = Proxy(client)
    subscriber = Subscriber()
    set_use_server_ws()
    context.push_context_onto_test(proxy.listening())
    return proxy, subscriber


# --- Thens ---


@then("the server should reject the command")
def the_server_should_reject_the_command(failed_result: None | HTTPError):
    assert_that(failed_result).is_instance_of(HTTPError)
