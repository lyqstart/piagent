import typer 
from rich import print
from app.llm import LLMClient
from app.config import get_settings
from app.agent import Agent

app = typer.Typer()

@app.command()
def run(prompt: str, model: str = ""):
    settings = get_settings(model=model or None)
    llm = LLMClient(settings = settings)
    agent = Agent(llm = llm)

    answer = agent.run(prompt)
    print(answer)

if __name__ == "__main__":
    app()
