from pydantic import BaseModel
from typing import Literal

Role = Literal["system", "user", "assistant", "tool"]

class Message(BaseModel):
    role: Role
    content: str
    