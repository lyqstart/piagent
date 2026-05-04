from app.messages import Message
from app.llm import LLMClient
from app.session import SessionStore
from app.tools import ToolRegistry
from app.loop import AgentLoop
from app.events import EventHandler

class Agent:
    def __init__(self, llm: LLMClient, 
                 system_prompt: str | None = None,
                 session_store: SessionStore | None = None,
                 event_handler: EventHandler | None = None
                 ):
        self.llm = llm
        self.session_store = session_store
        self.tool_registry = ToolRegistry()
        self.loop = AgentLoop(
            llm = self.llm,
            tool_registry= self.tool_registry,
            event_handler= event_handler,
        )
        
        if self.session_store:
            self.messages:list[Message] = self.session_store.load_messages()
        else:
            self.messages:list[Message] = []

        if system_prompt and not self.messages:
            self._append_message(Message(role="system", content=system_prompt))

    def _append_message(self, message: Message) -> None:
        self.messages.append(message)
        if self.session_store:
            self.session_store.append_message(message)

    def add_user_message(self, content: str)-> None:
        self._append_message(Message(role="user", content=content))
    

    def run(self, prompt: str) -> str:
        self.add_user_message(prompt)

        new_messages = self.loop.run(self.messages)

        for message in new_messages:
            self._append_message(message)
        
        for message in new_messages:
            if message.role == "assistant" and not message.tool_calls:
                return message.content or ""
            
        return ""
    
    def get_history(self) -> list[Message]:
        return self.messages