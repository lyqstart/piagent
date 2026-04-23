from pathlib import Path
from app.messages import Message

class SessionStore:
    def __init__(self, session_file: str = "sessions/current.json"):
        self.session_file = Path(session_file)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
    def append_message(self, message: Message) -> None:
        with self.session_file.open("a", encoding="utf-8") as f:
            f.write(message.model_dump_json() + "\n")

    def load_messages(self) -> list[Message]:
        if not self.session_file.exists():
            return []
        
        messages: list[Message] = []
        with self.session_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                messages.append(Message.model_validate_json(line))
        return messages

    def clear(self) -> None:
        if self.session_file.exists():
            self.session_file.unlink()