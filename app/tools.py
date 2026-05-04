import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ToolRegistry:
    def __init__(self):
        self._tools = {
            "get_time": self.get_time,
        }

        self._timezone_aliases = {
            "上海": "Asia/Shanghai",
            "中国": "Asia/Shanghai",
            "北京时间": "Asia/Shanghai",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "asia/shanghai": "Asia/Shanghai",

            "洛杉矶": "America/Los_Angeles",
            "美国洛杉矶": "America/Los_Angeles",
            "los angeles": "America/Los_Angeles",
            "los_angeles": "America/Los_Angeles",
            "america/los_angeles": "America/Los_Angeles",
            "pst": "America/Los_Angeles",
            "us/pacific": "America/Los_Angeles",

            "纽约": "America/New_York",
            "new york": "America/New_York",
            "america/new_york": "America/New_York",
            "est": "America/New_York",

            "伦敦": "Europe/London",
            "london": "Europe/London",
            "europe/london": "Europe/London",

            "东京": "Asia/Tokyo",
            "tokyo": "Asia/Tokyo",
            "asia/tokyo": "Asia/Tokyo",

            "utc": "UTC",
        }

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "获取指定城市或时区的当前时间。优先传 IANA 时区名，例如 Asia/Shanghai、America/Los_Angeles。也支持常见城市名，如 上海、洛杉矶、东京、伦敦。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "城市名或 IANA 时区名，例如 上海、Asia/Shanghai、洛杉矶、America/Los_Angeles"
                            }
                        },
                        "required": ["timezone"],
                    },
                },
            }
        ]

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

        if tool_name not in self._tools:
            return json.dumps(
                {"error": f"未知工具: {tool_name}"},
                ensure_ascii=False,
            )

        try:
            result = self._tools[tool_name](**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps(
                {"error": str(e)},
                ensure_ascii=False,
            )

    def normalize_timezone(self, timezone: str) -> str:
        value = timezone.strip()
        if not value:
            raise ValueError("timezone 不能为空")

        normalized_key = value.lower().strip()
        normalized_key = normalized_key.replace("_", " ")

        if normalized_key in self._timezone_aliases:
            return self._timezone_aliases[normalized_key]

        if "/" in value:
            return value

        return value

    def get_time(self, timezone: str) -> dict:
        normalized_timezone = self.normalize_timezone(timezone)

        try:
            now = datetime.now(ZoneInfo(normalized_timezone))
        except ZoneInfoNotFoundError:
            raise ValueError(
                f"未找到时区: {timezone}。标准写法示例: Asia/Shanghai, America/Los_Angeles"
            )

        return {
            "input_timezone": timezone,
            "normalized_timezone": normalized_timezone,
            "current_time": now.isoformat(timespec="seconds"),
        }