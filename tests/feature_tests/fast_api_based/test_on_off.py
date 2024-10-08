from pytest_bdd import scenario


# from .conftest

# @given("a running state machine on a server")


# from ..conftest

# @given("a machine that is Off")


# @given("a machine that is On")

# --- Whens ---

# from ..conftest

# @when("I command it again to switch On", target_fixture="failed_result")

# @when("I command it to switch off", target_fixture="command_results")

# @when(
#    "(in the background) I command it to switch off", target_fixture="command_results"
# )

# --- Thens ---

# from .conftest

# @then("the server should reject the command")

# from ..conftest

# @then("the server should first be busy")

# @then("the server should be on")

# @then("the server should be off")


@scenario("test_on_off.feature", "Switch System On")
def test_server_on():
    """"""


@scenario("test_on_off.feature", "Switch System Off")
def test_server_off():
    """"""


@scenario("test_on_off.feature", "Background Switch System On")
def test_back_server_on():
    """"""


@scenario("test_on_off.feature", "Background Switch System Off")
def test_back_server_off():
    """"""


@scenario("test_on_off.feature", "Commanding System on before finished")
def test_commanding_on_before_finished():
    """"""
