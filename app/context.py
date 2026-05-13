from dataclasses import dataclass
from pathlib import Path

@dataclass
class ContextBundle:
    project_context: str = ""

class ContextBuilder:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
    
    def build(self) -> ContextBundle:
        project_context = self._load_project_context()
        return ContextBundle(project_context=project_context)
    
    def _load_project_context(self) -> str:
        candidates = [
            self.project_root / "PROJECT_CONTEXT.md",
            self.project_root / "AGENTS.md",
            self.project_root / "README.md",
        ]

        for path in candidates:
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    return content
        
        return ""

