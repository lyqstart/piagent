from app.messages import Message
from app.llm import LLMClient
from app.session import SessionStore

class Agent:
    def __init__(self, llm: LLMClient, system_prompt: str | None = None,
                 session_store: SessionStore | None = None,):
        self.llm = llm
        self.session_store = session_store
        
        if self.session_store:
            self.messages:list[Message] = self.session_store.load_messages()
        else:
            self.messages:list[Message] = []

        if system_prompt and not self.messages:
            system_message = Message(role="system", content=system_prompt)
            self.messages.append(system_message)
            if self.session_store:
                self.session_store.append_message(system_message)

    def add_user_message(self, content: str)-> None:
        message = Message(role="user", content=content)
        self.messages.append(message)
        if self.session_store:
            self.session_store.append_message(message)
    
    def add_assistant_message(self, content: str):
        message = Message(role="assistant", content=content)
        self.messages.append(message)
        if self.session_store:
            self.session_store.append_message(message)

    def run(self, prompt: str) -> str:
        self.add_user_message(prompt)
        answer = self.llm.complete(self.messages)
        self.add_assistant_message(answer)
        return answer
    
    def get_history(self) -> list[Message]:
        return self.messages