import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


def get_redis_host() -> str:
    return REDIS_HOST


def get_redis_port() -> int:
    return REDIS_PORT
