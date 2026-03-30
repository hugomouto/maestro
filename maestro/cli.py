import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

SKILLS = [
    {
        "command":     "/MAESTRO-build-team",
        "cli":         "maestro build-team",
        "description": (
            "Elicita o domínio do usuário e constrói automaticamente "
            "agentes, tasks, workflows e squads a partir das operações informadas. "
            "Passa pelas três camadas: Elicitação → Síntese → Execução (Ralph). "
            "Cada agente gerado segue o Context Budget Protocol."
        ),
    },
]


def _print_banner():
    console.print()
    console.print("[bold cyan]╔══════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║       M A E S T R O                  ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════╝[/bold cyan]")
    console.print()


@click.group()
def main():
    """Maestro — meta-framework auto-configurável de agentes e tasks."""
    pass


@main.command()
@click.option("--path", default=".", show_default=True,
              help="Diretório onde o Maestro será instalado.")
def install(path):
    """Instala o Maestro no projeto atual."""
    _print_banner()
    from maestro.installer import install as do_install
    do_install(path)


@main.command()
@click.option("--path", default=".", show_default=True,
              help="Diretório do projeto a ser atualizado.")
def update(path):
    """Atualiza .maestro-core/ preservando workspace e configurações."""
    _print_banner()
    from maestro.installer import update as do_update
    do_update(path)


@main.command()
def version():
    """Exibe a versão instalada do Maestro."""
    from maestro import __version__
    console.print(f"[bold]Maestro[/bold] v{__version__}")


@main.command()
def skills():
    """Lista todos os skills disponíveis no Maestro."""
    _print_banner()
    table = Table(
        title="Skills disponíveis",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold cyan",
        min_width=80,
    )
    table.add_column("Skill",       style="bold green", no_wrap=True, width=28)
    table.add_column("Comando CLI", style="dim",        no_wrap=True, width=22)
    table.add_column("Descrição",   style="white")

    for s in SKILLS:
        table.add_row(s["command"], s["cli"], s["description"])

    console.print(table)
    console.print()
    console.print(
        "[dim]Use o Skill dentro do Claude Code ou rode o Comando CLI "
        "diretamente no terminal.[/dim]"
    )
    console.print()


@main.command("build-team")
@click.option("--domain", default=None,
              help="Nome do domínio a elicitar.")
@click.option("--config", default="maestro.config.yaml", show_default=True,
              help="Caminho para o arquivo de configuração.")
@click.option("--auto", is_flag=True, default=False,
              help="Executa síntese e geração automaticamente após elicitação.")
def build_team(domain, config, auto):
    """[/MAESTRO-build-team] Elicita domínio e gera agentes, tasks e workflows."""
    _print_banner()
    from maestro.skills.build_team import run
    run(domain=domain, config_path=config, auto=auto)
