import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent
from app.session import SessionManager

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
def run(model: str = "", reset: bool = False, session_id:str = "", verbose: bool = True):
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)

    session_manager = SessionManager("sessions")
    session_store = session_manager.create_store(
        session_id = session_id or None,
        reset= reset,
    )

    print(f"[green]当前会话:[/green] {session_store.session_id}")

    agent = Agent(
        llm = llm,
        system_prompt=(
            "你是一个简洁、准确的 AI 助手。"
            "当用户询问当前时间时，优先调用 get_time。"
            "当用户要求读取本地文本文件时，调用 read_text_file。"
            "当用户要求写入本地文本文件时，调用 write_text_file。"
            "不要假装已经读取或写入文件，必须依赖工具结果回答。"
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

@app.command("list-sessions")
def list_sessions():
    session_manager = SessionManager("sessions")
    session_ids = session_manager.list_session_ids()

    print(f"[green]sessions目录:[/green] {session_manager.session_dir}")
    if not session_ids:
        print("[yellow]没有找到任何会话记录。[/yellow]")
        return
    
    print("[green]会话列表:[/green]")
    for sid in session_ids:
        print(f" - {sid}")


if __name__ == "__main__":
    app()
