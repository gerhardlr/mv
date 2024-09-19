from .client import TangoProxy

def ping():
    print(TangoProxy().ping())
