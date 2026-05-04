import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, Callable
from pathlib import Path

ToolHandler = Callable[..., Any]

class ToolRegistry:
    def __init__(self):
        self._schemas: dict[str, dict] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._register_builtin_tools()

    def register_tool(
        self,
        *,
        name: str,
        description: str,
        parameters: dict,
        handler: ToolHandler,            
    ) -> None:
        self._schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }

        self._handlers[name] = handler

    def schemas(self) -> list[dict]:
        return list(self._schemas.values())
    
    def execute_tool_call(self, tool_call) -> str:
        tool_name = tool_call.function.name
        raw_arguments = tool_call.function.arguments or "{}"

        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return json.dumps(
                {"error": f"工具参数不是合法 JSON: {raw_arguments}"},
                ensure_ascii=False,
            )
        
        handler = self._handlers.get(tool_name)
        if handler is None:
            return json.dumps(
                {"error": f"未知工具: {tool_name}"},
                ensure_ascii=False,
            )
        
        try:
            result = handler(**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"error": str(e)},
                ensure_ascii=False,
            )
        
    def _register_builtin_tools(self) -> None:
        self.register_tool(
            name="get_time",
            description=(
                "获取指定时区的当前时间"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA 时区名，例如 Asia/Shanghai 或 America/Los_Angeles"
                    }
                },
            },
            handler=self.get_time,
        )

        self.register_tool(
            name="read_text_file",
            description="读取本地文本文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要读取的本地文件路径",
                    }
                },
                "required": ["path"],
            },
            handler=self.read_text_file,
        )

        self.register_tool(
            name="write_text_file",
            description="写入本地文本文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要写入的本地文件路径",
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的文本内容",
                    },
                },
                "required": ["path", "content"],
            },
            handler=self.write_text_file,
        )

    def get_time(self, timezone: str = "Asia/Shanghai") -> dict:
        now = datetime.now(ZoneInfo(timezone))
        return {
            "tool": "get_time",
            "timezone": timezone,
            "current_time": now.isoformat(timespec="seconds"),
        }

    def read_text_file(self, path: str) -> dict:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if not file_path.is_file():
            raise ValueError(f"不是一个文件: {path}")
        
        content = file_path.read_text(encoding="utf-8")
        return {
            "tool": "read_text_file",
            "path": path,
            "content": content,
        }
    
    def write_text_file(self, path: str, content: str) -> dict:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {
            "tool": "write_text_file",
            "path": path,
            "content": content,
        }

