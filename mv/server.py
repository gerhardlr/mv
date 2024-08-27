import uvicorn
from ._server.fast_api_server import app


__all__ = ["app"]


def serve():
    uvicorn.run(app, host="0.0.0.0", port=8000)

