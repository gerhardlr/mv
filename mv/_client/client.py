import requests
from fastapi.testclient import TestClient

class RealClient(TestClient):

    base_url = "http://127.0.0.1:8000/"

    def __init__(self):
        pass

    def get(self,path):
        return requests.get(f"{self.base_url}{path}")

    def post(self, path: str, **kwargs):
        return requests.post(f"{self.base_url}{path}", **kwargs)