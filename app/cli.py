import typer 
from rich import print
from app.messages import Message
from app.llm import LLMClient
from app.config import get_settings

app = typer.Typer()

@app.command()
def run(prompt: str, model: str = ""):
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)

    messages = [
        Message(role="user", content=prompt)
    ]

    answer = llm.complete(messages)
    print(answer)

if __name__ == "__main__":
    app()
