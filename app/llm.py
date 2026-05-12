from openai import OpenAI
from app.messages import Message
from app.config import Settings

class LLMClient:
    def __init__(self, settings: Settings):
        self.client = OpenAI(
            api_key = settings.api_key,
            base_url = settings.base_url,
        )
        self.model = settings.model

    def transform_context(self, messages: list[Message]) -> list[dict]:
        # 先做最小版：当前先不裁剪、不注入，直接返回
        return list(messages)

    def convert_to_llm_messages(self, messages: list[Message]) -> list[dict]:
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
