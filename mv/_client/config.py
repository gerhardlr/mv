import os

SERVER_IP = os.getenv("SERVER_IP", "127.0.0.1")
SERVER_PORT = os.getenv("SERVER_PORT", "8000")


def get_server_address() -> str:
    return f"http://{SERVER_IP}:{SERVER_PORT}/"


def get_ws_address() -> str:
    return f"ws://{SERVER_IP}:{SERVER_PORT}"
