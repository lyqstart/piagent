from pydantic import BaseModel
from typing import Literal, Any

Role = Literal["system", "user", "assistant", "tool"]

class AgentMessage(BaseModel):
    role: Role
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    
# 兼容当前项目，先不一次性改完所有引用
Message = AgentMessage