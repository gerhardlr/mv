from assertpy import assert_that
from fastapi.testclient import TestClient
import pytest

from mv.client import Proxy


def execute_post_off(client: TestClient):
    result = client.post("switch_off",json = {"delay": 10})
    assert_that(result.status_code).is_equal_to(200)

@pytest.mark.usefixtures("use_real_server")
def test_post_real_off(client):
    execute_post_off(client)

def test_post_off(client):
    execute_post_off(client)

# tests involing the proxy

def test_proxy_get(proxy: Proxy):
    assert_that(proxy.state).is_none()    

def test_proxy_command_on(proxy: Proxy):
    proxy.command_on(delay=1)
    assert_that(proxy.state).is_equal_to("ON")

@pytest.mark.usefixtures("use_real_server")
def test_proxy_real_command_on(proxy: Proxy):
    proxy.command_on(delay=1)
    assert_that(proxy.state).is_equal_to("ON")