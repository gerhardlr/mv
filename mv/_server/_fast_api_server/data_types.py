from typing import Any
from pydantic import BaseModel


class DelayArgs(BaseModel):
    delay: float | None


class ConfigArgs(BaseModel):
    delay: float | None
    config: dict[str, Any] | None
