from app.messages import Message
from app.llm import LLMClient

class Agent:
    def __init__(self, llm: LLMClient, system_prompt: str = ""):
        self.llm = llm
        self.messages: list[Message] = []

        if system_prompt:
            self.messages.append(Message(role="system", content=system_prompt))

    def add_user_message(self, content: str)-> None:
        self.messages.append(Message(role="user", content=content))
    
    def add_assistant_message(self, content: str):
        self.messages.append(Message(role="assistant", content=content))

    def run(self, prompt: str) -> str:
        self.add_user_message(prompt)
        answer = self.llm.complete(self.messages)
        self.add_assistant_message(answer)
        return answer
    
    def get_history(self) -> list[Message]:
        return self.messages