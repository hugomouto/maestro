"""Maestro Domain — criação e scaffold de domínios."""
import yaml
from pathlib import Path
from rich.console import Console
from maestro.constants import DOMAIN_STRUCTURE

console = Console()

CONFIG_FILE = "maestro.config.yaml"

PLAYBOOK_TEMPLATE = """\
# playbook.md — {domain}

> Documento principal do domínio `{domain}`.
> Lido pelo agente antes de qualquer operação.
> Preencha as seções. Mantenha abaixo de 400 linhas.

---

## Propósito

<!-- O que este domínio faz e o que NÃO faz -->

...

---

## Operações

| Operação | Responsável | Critério de conclusão |
|----------|-------------|----------------------|
| ...      | ...         | ...                  |

---

## Regras de negócio

- ...

---

## Fontes de dados

| Fonte | Localização |
|-------|-------------|
| ...   | `{domain}/data/processed/` |

---

## Interfaces com outros domínios

| Direção | Domínio | O que troca |
|---------|---------|-------------|
| Recebe de | ... | ... |
| Entrega para | ... | ... |

---

## Glossário

| Termo | Definição |
|-------|-----------|
| ...   | ...       |
"""


def create_domain(name: str, root: Path = None, description: str = "") -> dict:
    """
    Cria a estrutura de pastas de um domínio e registra no config.

    Args:
        name:        nome do domínio (ex: vendas)
        root:        raiz do projeto (default: cwd)
        description: descrição curta do domínio

    Returns:
        dict com is_new, domain_root, playbook, playbook_created
    """
    if root is None:
        root = Path(".").resolve()

    domain_root = root / name
    is_new = not domain_root.exists()

    # Estrutura de pastas + .gitkeep em pastas vazias
    for sub in DOMAIN_STRUCTURE:
        folder = domain_root / sub
        folder.mkdir(parents=True, exist_ok=True)
        gitkeep = folder / ".gitkeep"
        contents = [f for f in folder.iterdir() if f.name != ".gitkeep"]
        if not contents and not gitkeep.exists():
            gitkeep.touch()

    # Playbook
    playbook = domain_root / "context" / "playbook.md"
    playbook_created = False
    if not playbook.exists():
        content = PLAYBOOK_TEMPLATE.format(domain=name)
        if description:
            content = content.replace(
                "## Propósito\n\n<!-- O que este domínio faz e o que NÃO faz -->\n\n...",
                f"## Propósito\n\n{description}",
            )
        playbook.write_text(content, encoding="utf-8")
        playbook_created = True

    # Registro no config
    _register_in_config(root, name, description)

    # Feedback
    if is_new:
        console.print(f"  [blue]→[/blue] [cyan]{name}/[/cyan] criado")
    elif playbook_created:
        console.print(f"  [blue]→[/blue] [cyan]{name}/[/cyan] playbook.md criado")
    else:
        console.print(f"  [yellow]→[/yellow] [cyan]{name}/[/cyan] já existe — preservado")

    return {
        "is_new": is_new,
        "domain_root": domain_root,
        "playbook": playbook,
        "playbook_created": playbook_created,
    }


def _register_in_config(root: Path, name: str, description: str):
    config_path = root / CONFIG_FILE
    if not config_path.exists():
        return

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    domain_map = config.get("domain_map") or {}

    if name not in domain_map:
        domain_map[name] = {"description": description} if description else {}
        config["domain_map"] = domain_map
        config_path.write_text(
            yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        console.print(f"  [blue]→[/blue] {name} registrado em {CONFIG_FILE}")
