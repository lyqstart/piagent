from openai import OpenAI
from app.messages import Message
from app.config import Settings

class LLMClient:
    def __init__(
            self, 
            settings: Settings, 
            max_context_messages: int = 8,
            project_context: str = "",
    ):
        self.client = OpenAI(
            api_key = settings.api_key,
            base_url = settings.base_url,
        )
        self.model = settings.model
        self.max_context_messages = max_context_messages
        self.project_context = project_context.strip()

    def build_fixed_context(self, messages: list[Message]) -> list[Message]:
        fixed: list[Message] = []

        if messages and messages[0].role == "system":
            fixed.append(messages[0])

        if self.project_context:
            fixed.append(
                Message(role="system", content=f"项目上下文：\n{self.project_context}")
            )
        
        return fixed
    
    def build_rolling_context(self, messages: list[Message], fixed_count: int) -> list[Message]:
        rolling = messages[1:] if messages and messages[0].role == "system" else list(messages)

        keep_count = self.max_context_messages - fixed_count
        if keep_count <= 0:
            return []
        
        return rolling[-keep_count:]

    def transform_context(self, messages: list[Message]) -> list[dict]:
        print("LLMClient: transform_context")
        print("  原始消息数:", len(messages))
        
        fixed = self.build_fixed_context(messages)
        rolling = self.build_rolling_context(messages, fixed_count=len(fixed))
        transformed = fixed + rolling

        print("  固定上下文数:", len(fixed))
        print("  滚动上下文数:", len(rolling))
        print("  输出消息数:", len(transformed))
        print("  输出消息角色:", [m.role for m in transformed])

        return transformed

    def convert_to_llm_messages(self, messages: list[Message]) -> list[dict]:
        print("LLMClient: convert_to_llm_messages")
        print("  输入消息角色:", [m.role for m in messages])

        api_messages: list[dict] =[]

        for message in messages:
            item = {"role": message.role}

            if message.content is not None:
                item["content"] = message.content
            
            if message.name is not None:
                item["name"] = message.name
            
            if message.tool_call_id is not None:
                item["tool_call_id"] = message.tool_call_id
            
            if message.tool_calls is not None:
                item["tool_calls"] = message.tool_calls

            api_messages.append(item)
        
        print("  转换后消息数:", len(api_messages))
        return api_messages
    

    def complete(self, messages: list[Message]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return response.choices[0].message.content or ""
    
    def _to_api_message(self, messages:list[Message]) -> list[dict]:
        api_messages: list[dict] = []

        for message in messages:
            item = {"role": message.role}

            if message.content is not None:
                item["content"] = message.content

            if message.name is not None:
                item["name"] = message.name

            if message.tool_call_id is not None:
                item["tool_call_id"] = message.tool_call_id
            
            if message.tool_calls is not None:
                item["tool_calls"] = message.tool_calls
            
            api_messages.append(item)

        return api_messages
        
    def create_response(self, messages: list[Message], tools: list[dict] | None = None) :
        transformed_messages = self.transform_context(messages)
        llm_messages = self.convert_to_llm_messages(transformed_messages)

        if tools:
            return self.client.chat.completions.create(
                model=self.model,
                messages=llm_messages,
                tools=tools
            )
        
        return self.client.chat.completions.create(
            model=self.model,
            messages= llm_messages
        )
