import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    api_key: str
    base_url: str
    model: str

def get_settings(model: str | None = None) -> Settings:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    env_model = os.getenv("LLM_MODEL", "").strip()

    final_model = model or env_model or "glm-5.1"

    if not api_key:
        raise ValueError("缺少环境变量 LLM_API_KEY")
    
    if not base_url:
        raise ValueError("缺少环境变量 LLM_BASE_URL")
    
    return Settings(api_key=api_key, base_url=base_url, model=final_model)