from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class CreateLabRequest(BaseModel):
    seed: Optional[int] = Field(None, ge=1, le=100000)

class ActionEnum(str, Enum):
    start_generation = "start_generation"
    stop_generation = "stop_generation"
    set_paused = "set_paused"
    set_temporary_errors = "set_temporary_errors"
    inject_malformed = "inject_malformed"
    restore = "restore"

class CommandRequest(BaseModel):
    command_id: str = Field(..., min_length=1)
    action: ActionEnum
    value: Optional[bool] = None

    class Config:
        extra = "forbid"
