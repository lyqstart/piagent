from app.messages import Message
from app.llm import LLMClient
from app.tools import ToolRegistry
from app.events import EventHandler

class AgentLoop:
    def __init__(
        self, 
        llm: LLMClient, 
        tool_registry: ToolRegistry, 
        max_steps: int = 8,
        event_handler: EventHandler | None = None
    ):
    
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.event_handler = event_handler

    def _emit(self, event_type: str, payload: dict) -> None:
        if self.event_handler:
            self.event_handler(event_type, payload)

    def run(self, messages: list[Message]) -> list[Message]:
        new_messages: list[Message] = []
        working_messages = list(messages)

        self._emit(
            "loop_start",
            {
                "message_count": len(working_messages),
            },
        )

        for step in range(1, self.max_steps + 1):
            self._emit(
                "llm_request_start",
                {
                    "step": step,
                    "message_count": len(working_messages),
                },
            )

            response = self.llm.create_response(
                messages = working_messages,
                tools = self.tool_registry.schemas(),
            )           

            assistant = response.choices[0].message
            assistant_tool_calls = None

            if assistant.tool_calls:
                assistant_tool_calls = [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in assistant.tool_calls
                ]
            
            assistant_message = Message(
                role="assistant",
                content=assistant.content,
                tool_calls=assistant_tool_calls,
            )

            new_messages.append(assistant_message)
            working_messages.append(assistant_message)

            self._emit(
                "llm_response",
                {
                    "step": step,
                    "content": assistant.content,
                    "tool_call_count": len(assistant.tool_calls or [])
                },
            )

            if not assistant.tool_calls:
                self._emit(
                    "loop_end",
                    {
                        "step": step,
                        "reason": "final_answer",
                    },
                )
                return new_messages
            
            for tool_call in assistant.tool_calls:
                self._emit(
                    "tool_call_start",
                    {
                        "step": step,
                        "tool_name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                        "tool_call_id": tool_call.id,
                    },
                )

                tool_result = self.tool_registry.execute_tool_call(tool_call)

                tool_message = Message(
                    role="tool",
                    content=tool_result,
                    name=tool_call.function.name,
                    tool_call_id=tool_call.id,
                )

                new_messages.append(tool_message)
                working_messages.append(tool_message)

                self._emit(
                    "tool_call_end",
                    {
                        "step": step,
                        "tool_name": tool_call.function.name,
                        "tool_call_id": tool_call.id,
                        "result": tool_result,
                    },
                )
        
        self._emit(
            "loop_end",
            {
                "max_steps": self.max_steps,
                "reason": "max_steps_exceeded",
            },
        )

        raise RuntimeError(f"工具循环超过最大步数 {self.max_steps}")