import requests
from fastapi.testclient import TestClient

from .config import get_server_address


class RealClient(TestClient):

    def __init__(self):
        self.base_url = get_server_address()

    def get(self, path):
        return requests.get(f"{self.base_url}{path}")

    def post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", **kwargs)
