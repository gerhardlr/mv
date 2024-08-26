import pytest
from pytest_bdd.parser import Feature, Scenario, Step
from _pytest.fixtures import TopRequest
import logging
import os

logger = logging.getLogger()


@pytest.fixture(name="start", autouse=True)
def fxt_start():
    pass


def pytest_bdd_before_step(
    request: TopRequest, feature: Feature, scenario: Scenario, step: Step, step_func
):
    logger.info(f"STEP: {step.keyword} {step.name}")
    if os.getenv("DEBUG_LOGS"):
        logger.info(
            f'{step_func.__name__}:("{step_func.__code__.co_filename}:'
            f'{step_func.__code__.co_firstlineno}"'
        )
