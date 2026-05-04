import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent
from app.session import SessionStore

app = typer.Typer()

def console_event_handler(event_type: str, payload: dict) -> None:
    if event_type == "loop_start":
        print(f"[magenta]EVENT[/magenta]: loop_start | messages={payload['message_count']}")
    elif event_type == "llm_request_start":
        print(
            f"[magenta]EVENT[/magenta]: llm_request_start | "
            f"step={payload['step']} messages={payload['message_count']}"
        )
    elif event_type == "llm_response":
        print(
            f"[magenta]EVENT[/magenta] llm_response | "
            f"step={payload['step']} tool_calls={payload['tool_call_count']}"
        )
    elif event_type == "tool_call_start":
        print(
            f"[magenta]EVENT[/magenta] tool_call_start | "
            f"step={payload['step']} tool={payload['tool_name']}"
        )
    elif event_type == "tool_call_end":
        print(
            f"[magenta]EVENT[/magenta] tool_call_end | "
            f"step={payload['step']} tool={payload['tool_name']}"
        )
    elif event_type == "loop_end":
        print(f"[magenta]EVENT[/magenta] loop_end | reason={payload['reason']}")

@app.command()
def run(model: str = "", reset: bool = False, verbose: bool = True):
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)
    session_store = SessionStore("sessions/current.json")

    if reset:
        session_store.clear()

    agent = Agent(
        llm = llm,
        system_prompt=(
            "你是一个简洁、准确的 AI 助手。"
            "当用户询问当前时间时，必须优先调用 get_time 工具，不要自己猜。"
        ),
        session_store=session_store,
        event_handler = console_event_handler if verbose else None,
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
