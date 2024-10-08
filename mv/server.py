import uvicorn
import os
from ._server._fast_api_server.fast_api_server import app


__all__ = ["app"]


def serve():
    server_port = int(os.getenv("SERVER_PORT", "30000"))
    if log_level := os.getenv("LOG_LEVEL") == "debug":
        uvicorn.run(app, host="0.0.0.0", port=server_port, log_level=log_level)
    else:
        uvicorn.run(app, host="0.0.0.0", port=server_port)


if __name__ == "__main__":
    serve()
