from contextlib import ExitStack
from typing import ContextManager, TypeVar

T = TypeVar("T")


class StackableContext:
    """Enable contexts to be loaded as an execution stack for a particular test.

    This allows a tester to specify at particular points in the code execution to
    load a setup and 'tear down' as a stack.

    E.g.:

    .. code-block:: python

        @pytest.fixture()
        def stack():
            with ExitStack() as stack:
                yield stack

        @contextmanager
        def my_context():
            set_up()
            yield
            tear_down()

        def test_it(stack):
            context = StackableContext(stack)
            # failures in code before this point will not cause tear_down() to be called
            # this will result in set_up() being called
            context.push_context_onto_test(my_context())
            # test will fail but then pytest will call tear_down() after logging FAIL
            assert False


    """

    def __init__(
        self,
        session_stack: ExitStack,
        test_stack: None | ExitStack = None,
    ) -> None:
        """Initialise object.

        The objects gets ExitStack objects as input arguments.
        The underlying implication is that the client has setup these
        exit stack objects within a pytest fixture with scope corresponding
        to the type of stack (e.g. session will be scope = 'session'):

        .. code-block:: python

            @pytest.fixture(scope='session')
            def session_stack():
                with ExitStack() as stack:
                    yield stack

            @pytest.fixture
            def test_stack():
                with ExitStack() as stack:
                    yield stack

            @pytest.fixture
            def context_with_session_and_function_scope(session_stack, test_stack):
                return StackableContext(session_stack, test_stack)

            @pytest.fixture
            def context_with_only_session_scope(session_stack, test_stack):
                # cm's pushed on test stack will only exit at the end of session
                return StackableContext(session_stack)

            @pytest.fixture
            def context_with_only_test_scope(test_stack):
                # cm's pushed on session stack will exit at the end of test
                # use this if you don't want to discremenate between session and test scope
                return StackableContext(test_stack)

        Note that if only a test_session is given the session stack will be used
        for all contextmanagers (session and normal calls). This allows for optionally
        changing teardowns that normally occur at the end of a test to only occur at the
        end of a session.

        Note a test session can specifically be set after initialisation also.

        :param session_stack: The ExitStack object to use for sessions,
            if no test_stack is given then the session stack will be used
            as a test_session also.
        :param test_stack: The ExitStack object to use for each test call,
            defaults to None
        """
        self._session_stack = session_stack
        # if only one stack is given then session = test
        if not test_stack:
            test_stack = session_stack  # we treat session stack as a test stack
        self._test_stack = test_stack

    def push_context_onto_test(self, c_m: ContextManager[T]) -> T:
        """Set a contextmanager to call its exit parts at the end of a test.

        The entry part will be called immediately.
        If the object was initialised without any explicit test_stack given,
        it will uses the test_session. This means the teardown will only occur
        at the end of a session even though the client set it to happen at the end
        of a test.

        :param c_m: the contextmanager object.
        :return: The result of the first part executing on the context manager.
            Note the exit part will execute after the test function has exited.
        """
        return self._test_stack.enter_context(c_m)

    def push_context_onto_session(self, c_m: ContextManager[T]) -> T:
        """Place a context manager on the execution stack in a session wide scope.

        :param c_m: The context manager object.
        :return: The result of the first part executing on the context manager.
            Note if no test stack was given the session will still exit after test function ended.
        """
        return self._session_stack.enter_context(c_m)

    def set_test_stack(self, test_stack: ExitStack):
        """Set a function scoped test stack after initialisation.

        :param test_stack: A exit stack scoped test function wide.
        """
        self._test_stack = test_stack
