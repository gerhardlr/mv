from time import sleep
from .client import TangoProxy


def ping():
    print(TangoProxy().ping())
