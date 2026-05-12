import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent
from app.session import SessionManager

app = typer.Typer()

def start_chat(
    *,
    model: str = "",
    title: str = "",
    session_id: str = "",
    reset: bool = False,
    verbose: bool = True,
) -> None:
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)

    session_manager = SessionManager("sessions")
    session_store = session_manager.create_store(
        session_id = session_id or None,
        reset= reset,
        model = settings.model,
        title = title,
    )

    metadata = session_store.load_metadata()

    print(f"[green]当前会话:[/green] {session_store.session_id}")
    print(f"[green]会话标题：[/green] {metadata.title or '(无标题)'}")

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
def run(
    model: str = "", 
    reset: bool = False, 
    session_id:str = "", 
    title: str = "", 
    verbose: bool = True):
    
    start_chat(
        model=model,
        reset=reset,
        session_id=session_id,
        title=title,
        verbose=verbose,
    )

@app.command()
def resume(
    session_id: str = "",
    model: str = "",
    verbose: bool = True,
):
    session_manager = SessionManager("sessions")
    
    if not session_manager.session_exists(session_id):
        print(f"[red]会话不存在: {session_id} [/red]")
        return
    
    start_chat(
        model = model,
        session_id = session_id,
        title = "",
        reset = False,
        verbose = verbose,
    )

@app.command("list-sessions")
def list_sessions():
    session_manager = SessionManager("sessions")
    sessions = session_manager.list_sessions()

    print(f"[green]sessions目录:[/green] {session_manager.session_dir}")
    if not sessions:
        print("[yellow]没有找到任何会话记录。[/yellow]")
        return
    
    print("[green]已有会话:[/green]")
    for s in sessions:
        title = s.title or "(无标题)"
        model = s.model or "unknown model"
        print(
            f"- {s.session_id}\n"
            f"  title: {title}\n"
            f"  model: {model}\n"
            f"  updated: {s.updated_at}\n"
            f"  messages: {s.message_count}")


if __name__ == "__main__":
    app()
