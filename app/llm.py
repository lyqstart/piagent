from openai import OpenAI
from app.messages import Message
from app.config import Settings

class LLMClient:
    def __init__(self, settings: Settings, max_context_messages: int = 8):
        self.client = OpenAI(
            api_key = settings.api_key,
            base_url = settings.base_url,
        )
        self.model = settings.model
        self.max_context_messages = max_context_messages

    def transform_context(self, messages: list[Message]) -> list[dict]:
        print("LLMClient: transform_context")
        print("  原始消息数:", len(messages))
        
        if len(messages) <= self.max_context_messages:
            transformed = list(messages)
            print("  未裁剪")
            print("  输出消息数:", len(transformed))
            return transformed

        system_message = None
        other_messages = messages

        if messages and messages[0].role == "system":
            system_message = messages[0]
            other_messages = messages[1:]

        keep_count = self.max_context_messages
        if system_message is not None:
            keep_count -= 1
        
        trimmed_messages = other_messages[-keep_count:]

        if system_message is not None:
            transformed = [system_message] + trimmed_messages
        else:
            transformed = trimmed_messages
        
        print("  已裁剪")
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
