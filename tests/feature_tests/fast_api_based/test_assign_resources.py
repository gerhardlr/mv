from pytest_bdd import scenario


# from .conftest

# @given("a running state machine on a server")


# from ..conftest

# @given("a machine that is On")

# --- Whens ---

# from ..conftest

# @when("I assign resources to it",


# --- Thens ---


# from ..conftest

# @then("the machine should first go into RESOURCING state",

# @then("the machine should go into IDLE state and remain there",


@scenario("test_assign_resources.feature", "Assign Resources")
def test_assign_resources():
    """"""


@scenario("test_assign_resources.feature", "Release Resources")
def test_release_resources():
    """"""


@scenario("test_assign_resources.feature", "Background Assign Resources")
def test_background_assign_resources():
    """"""


@scenario("test_assign_resources.feature", "Background Release Resources")
def test_background_release_resources():
    """"""


@scenario(
    "test_assign_resources.feature", "Assign Resources when state machine is RESOURCING"
)
def test_assign_resources_when_state_is_resourcing():
    """"""
