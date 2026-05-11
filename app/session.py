from pathlib import Path
from app.messages import Message
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from app.messages import Message

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

@dataclass
class SessionMetadata:
    session_id: str
    created_at: str
    updated_at: str
    model: str = ""
    title: str = ""
    message_count: int = 0


class SessionStore:
    def __init__(self, session_file: str, model: str = "", title: str = ""):
        self.session_file = Path(session_file).resolve()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self.model = model
        self.title = title
        self.meta_file = self.session_file.with_suffix(".meta.json")
        self._ensure_metadata()

    def append_message(self, message: Message) -> None:
        with self.session_file.open("a", encoding="utf-8") as f:
            f.write(message.model_dump_json() + "\n")
        
        metadata = self.load_metadata()
        metadata.updated_at = now_iso()
        metadata.message_count += 1

        if not metadata.title and message.role == "user" and message.content:
            metadata.title = self._build_title(message.content)
        
        if not metadata.model and self.model:
            metadata.model = self.model
        
        self._save_metadata(metadata)

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
        if self.meta_file.exists():
            self.meta_file.unlink()
        self._ensure_metadata()

    def load_metadata(self) -> SessionMetadata:
        if not self.meta_file.exists():
            return self._ensure_metadata()
        
        data = json.loads(self.meta_file.read_text(encoding="utf-8"))
        return SessionMetadata(**data)

    def _save_metadata(self, metadata: SessionMetadata) -> None:
        self.meta_file.write_text(
            json.dumps(asdict(metadata), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    
    def _ensure_metadata(self) -> None:
        if self.meta_file.exists():
            return
        
        created_at = now_iso()
        metadata = SessionMetadata(
            session_id = self.session_id,
            created_at = created_at,
            updated_at = created_at,
            model = self.model,
            title = self.title,
            message_count = 0,
        )
        self._save_metadata(metadata)

    def set_title(self, title: str) -> None:
        metadata = self.load_metadata()
        metadata.title = title.strip()
        metadata.updated_at = now_iso()
        self._save_metadata(metadata)

    def _build_title(self, text: str, limit: int = 30) -> str:
        text = " ".join(text.strip().split())
        if len(text) <= limit:
            return text
        return text[:limit] + "..."

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
    
    def create_store(
        self, 
        session_id: str | None =None, 
        reset: bool = False,
        model: str = "",
        title: str = "",) -> SessionStore:
        final_session_id = session_id or self.create_session_id()
        store = SessionStore(
            session_file=str(self.get_session_path(final_session_id)),
            model = model,
            title = title,
        )

        if reset:
            store.clear()
            if title:
                store.set_title(title)

        return store
    
    def list_sessions(self) -> list[SessionMetadata]:
        data_files = [
            p for p in self.session_dir.iterdir()
            if p.is_file()
            and p.suffix in {".json", ".json1"}
            and p.stem.startswith("ses_")
            and not p.name.endswith(".meta.json")
        ]

        sessions: list[SessionMetadata] = []

        for data_file in data_files:
            meta_file = data_file.with_suffix(".meta.json")
            
            if meta_file.exists():
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                sessions.append(SessionMetadata(**data))
                continue

            stat = data_file.stat()
            line_count = 0
            with data_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        line_count += 1
            
            sessions.append(
                SessionMetadata(
                    session_id = data_file.stem,
                    created_at = datetime.fromtimestamp(stat.st_ctime).isoformat(timespec="seconds"),
                    updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    model="",
                    title="",
                    message_count=line_count,
                )
            )
            
        sessions.sort(key= lambda s: s.updated_at, reverse=True)
        return sessions
      
