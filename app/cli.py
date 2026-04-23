import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent
from app.session import SessionStore

app = typer.Typer()

@app.command()
def run(model: str = "", reset: bool = False):
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)
    session_store = SessionStore("sessions/current.json")

    if reset:
        session_store.clear()

    agent = Agent(
        llm = llm,
        system_prompt="你是一个嗯。简洁、准确的 AI 助手。",
        session_store=session_store
    )
    print("[green]进入多轮对话模式，输入 exit 结束。[/green]")

    while True:
        user_input = input("You> ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            print("[yellow]对话结束。[/yellow]")
            break

        answer = agent.run(user_input)
        print(f"[cyan]AI>[/cyan] {answer}")

if __name__ == "__main__":
    app()
