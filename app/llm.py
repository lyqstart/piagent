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

    def complete(self, messages: list[Message]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return response.choices[0].message.content or ""
    