from pathlib import Path
from app.messages import Message
from uuid import uuid4
from datetime import datetime

class SessionStore:
    def __init__(self, session_file: str):
        self.session_file = Path(session_file).resolve()
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

    @property
    def session_id(self) -> str:
        return self.session_file.stem


class SessionManager:
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir).resolve()
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create_session_id(self) -> str:
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        short_id = uuid4().hex[:8]
        return f"ses_{now}_{short_id}"
    
    def get_session_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.json"
    
    def create_store(self, session_id: str | None =None, reset: bool = False) -> SessionStore:
        final_session_id = session_id or self.create_session_id()
        store = SessionStore(str(self.get_session_path(final_session_id)))

        if reset:
            store.clear()

        return store
    
    def list_session_ids(self) -> list[str]:
        if not self.session_dir.exists():
            return []
        
        files = [
            p for p in self.session_dir.iterdir()
            if p.is_file() and p.suffix in ".json"
        ]

        files.sort(key= lambda p: p.stat().st_mtime, reverse=True)
        return [f.stem for f in files]


    
