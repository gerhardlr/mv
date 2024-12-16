from time import sleep
import os
from typing import Any
from tango import DeviceProxy, EventType


def call_back(event):
    print(f"{event}")


def test_pub_sub():
    dev_name = "mv/statemachine/1"
    host = os.getenv("SERVER_IP", "127.0.0.1")
    port = os.getenv("SERVER_PORT", "30002")
    proxy = DeviceProxy(f"tango://{host}:{port}/{dev_name}#dbase=no")
    sub_id = proxy.subscribe_event("agg_state", EventType.CHANGE_EVENT, call_back)
    while True:
        try:
            print(f"{proxy.read_attribute('agg_state')}")
        except:
            pass
        sleep(1)


if __name__ == "__main__":
    test_pub_sub()
