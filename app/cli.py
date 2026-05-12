import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent
from app.session import SessionManager
from app.messages import Message

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
    
    store = session_manager.get_store(session_id)
    store.ensure_title()
    
    start_chat(
        model = model,
        session_id = session_id,
        title = "",
        reset = False,
        verbose = verbose,
    )

@app.command("resume-latest")
def resume_latest(
    model : str = "",
    verbose: bool = True,
):
    session_manager = SessionManager("sessions")
    latest = session_manager.get_lastest_session()

    if latest is None:
        print("[red]没有可恢复的会话。[/red]")
        return 
    
    store = session_manager.get_store(latest.session_id)
    store.ensure_title()

    print(f"[green]恢复最近会话:[/green] {latest.session_id}")
    print(f"[green]会话标题：[/green] {latest.title or '(无标题)'}")

    start_chat(
        model = model,
        session_id = latest.session_id,
        title = "",
        reset = False,
        verbose = verbose,
    )

@app.command("rename-session")
def rename_session(
    session_id: str = typer.Option(..., "--session-id", help="会话ID"),
    title: str = typer.Option(..., "--title", help="新的会话标题"),
):
    session_manager = SessionManager("sessions")

    if not session_manager.session_exists(session_id):
        print(f"[red]会话不存在: {session_id} [/red]")
        return
    
    store = session_manager.get_store(session_id)
    store.set_title(title)

    metadata = store.load_metadata()
    print(f"[green]已更新会话标题:[/green] {metadata.session_id}")
    print(f"[green]新标题:[/green] {metadata.title}")

def format_message_brief(message: Message) -> str:
    role = message.role.upper()
    content = " ".join((message.content or "").strip().split())
    if len(content) > 100:
        content = content[:100] + "..."

    if message.role == "assistant" and message.tool_calls:
        return f"{role}: [tool_calls={len(message.tool_calls)}]"
    
    if message.role == "tool":
        tool_name = message.name or "unknown_tool"
        return f"{role}({tool_name}): {content}"
    
    return f"{role}: {content}"

def print_session_messages(messages: list[Message]) -> None:
    if not messages:
        print("[yellow]没有消息记录。[/yellow]")
        return
    
    print("[green]消息记录:[/green]")
    for index, message in enumerate(messages, start=1):
        print(f"{index}.{format_message_brief(message)}")

@app.command("show-session")
def show_session(
    session_id: str = typer.Option(..., "--session-id", help="会话ID"),
):
    session_manager = SessionManager("sessions")

    if not session_manager.session_exists(session_id):
        print(f"[red]会话不存在: {session_id} [/red]")
        return
    
    store = session_manager.get_store(session_id)
    messages = store.load_messages()
    metadata = store.load_metadata()

    print(f"[green]会话ID:[/green] {metadata.session_id}")
    print(f"[green]标题:[/green] {metadata.title or '(无标题)'}")
    print(f"[green]模型:[/green] {metadata.model or 'unknown model'}")
    print(f"[green]创建时间:[/green] {metadata.created_at}")
    print(f"[green]更新时间:[/green] {metadata.updated_at}")
    print(f"[green]消息数:[/green] {metadata.message_count}")

    print_session_messages(messages)

@app.command("list-sessions")
def list_sessions():
    session_manager = SessionManager("sessions")
    sessions = session_manager.list_sessions()

    print(f"[green]sessions目录:[/green] {session_manager.session_dir}")
    if not sessions:
        print("[yellow]没有找到任何会话记录。[/yellow]")
        return
    
    print("[green]已有会话:[/green]")
    for index, s in enumerate(sessions, start=1):
        title = s.title or "(无标题)"
        model = s.model or "unknown model"
        print(
            f"{index}. {s.session_id}\n"
            f"   title: {title}\n"
            f"   model: {model}\n"
            f"   updated: {s.updated_at}\n"
            f"   messages: {s.message_count}"
        )



if __name__ == "__main__":
    app()
