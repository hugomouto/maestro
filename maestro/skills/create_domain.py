"""Skill create-domain — cria um domínio interativamente."""
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def run(name: str = None, description: str = "", path: str = "."):
    root = Path(path).resolve()

    if not name:
        name = Prompt.ask("[bold]Nome do domínio[/bold] (ex: vendas, marketing)")
        name = name.strip().lower().replace(" ", "-")

    if not description:
        description = Prompt.ask(
            "[bold]Descrição curta[/bold] (opcional, Enter para pular)",
            default="",
        )

    console.print()
    from maestro.domain import create_domain
    create_domain(name=name, root=root, description=description)
    console.print()
    console.print(f"[green]✓ Domínio [bold]{name}[/bold] pronto.[/green]")
    console.print(f"  Preencha [bold]{name}/context/playbook.md[/bold] e rode [bold]maestro build-team[/bold]")
    console.print()
