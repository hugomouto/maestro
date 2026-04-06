import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

SKILLS = [
    {
        "command":     "/MAESTRO-create-domain",
        "cli":         "maestro create-domain",
        "description": (
            "Cria um novo domínio com estrutura completa de subpastas "
            "(context/, data/, ops/, reports/), playbook.md pré-preenchido "
            "e registro automático no maestro.config.yaml."
        ),
    },
    {
        "command":     "/MAESTRO-build-team",
        "cli":         "maestro build-team",
        "description": (
            "Elicita o domínio do usuário e constrói automaticamente agentes "
            "especializados, tasks, workflows e squads. Cada agente tem um "
            "agent_role próprio — pesquisador, analista, produtor de conteúdo etc. "
            "Cria a estrutura de pastas do domínio (context/, data/, ops/, reports/) "
            "e gera STRUCTURE.md na raiz do projeto."
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
@click.option("--path", default=".", show_default=True)
def install(path):
    """Instala o Maestro no projeto atual (cria tudo out of the box)."""
    _print_banner()
    from maestro.installer import install as do_install
    do_install(path)


@main.command()
@click.option("--path", default=".", show_default=True)
def update(path):
    """Atualiza framework, CLAUDE.md e cria domínios novos do config."""
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


@main.command("create-domain")
@click.option("--name",        default=None, help="Nome do domínio")
@click.option("--description", default="",   help="Descrição curta do domínio")
@click.option("--path",        default=".",  show_default=True)
def create_domain(name, description, path):
    """[/MAESTRO-create-domain] Cria um novo domínio com estrutura de pastas e playbook."""
    _print_banner()
    from maestro.skills.create_domain import run
    run(name=name, description=description, path=path)


@main.command("build-team")
@click.option("--domain", default=None)
@click.option("--config", default="maestro.config.yaml", show_default=True)
@click.option("--auto",   is_flag=True, default=False)
def build_team(domain, config, auto):
    """[/MAESTRO-build-team] Elicita domínio e gera agentes especializados."""
    _print_banner()
    from maestro.skills.build_team import run
    run(domain=domain, config_path=config, auto=auto)
