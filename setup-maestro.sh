#!/usr/bin/env bash
# =============================================================================
# setup-maestro.sh
# Roda na raiz da pasta maestro/ e cria toda a estrutura do pacote.
# Inclui Context Budget Protocol — agente decide contexto uma vez por task.
# Uso: bash setup-maestro.sh
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()     { echo -e "${BLUE}→${NC} $1"; }
ok()      { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}!${NC} $1"; }
section() { echo -e "\n${CYAN}── $1 ──${NC}"; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       M A E S T R O  —  Setup        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

# =============================================================================
# SEÇÃO 1 — ESTRUTURA DE DIRETÓRIOS
# =============================================================================
section "Estrutura de diretórios"

mkdir -p maestro/core/agents
mkdir -p maestro/core/tasks
mkdir -p maestro/core/templates
mkdir -p maestro/core/protocols       # ← novo: Context Budget Protocol
mkdir -p maestro/ralph
mkdir -p maestro/skills
mkdir -p tests

ok "Diretórios criados"

# =============================================================================
# SEÇÃO 2 — CONFIGURAÇÃO DO PACOTE
# =============================================================================
section "Configuração do pacote"

cat > pyproject.toml << 'PYPROJECT'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "maestro"
version = "0.1.0"
description = "Meta-framework auto-configurável de agentes, tasks e workflows"
requires-python = ">=3.10"
dependencies = [
    "anthropic",
    "pyyaml",
    "click",
    "rich",
]

[project.scripts]
maestro = "maestro.cli:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["maestro*"]

[tool.setuptools.package-data]
maestro = ["core/**/*", "ralph/*", "skills/*"]
PYPROJECT
ok "pyproject.toml"

cat > .gitignore << 'GITIGNORE'
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.env
.venv/
venv/
*.DS_Store
maestro-workspace/
.maestro-core/
GITIGNORE
ok ".gitignore"

cat > README.md << 'README'
# Maestro

Meta-framework auto-configurável de agentes, tasks e workflows.
Entende o domínio do usuário e gera toda a estrutura de operação a partir dele.

## Instalação

```bash
pip install git+https://github.com/SEU-USUARIO/maestro.git
```

## Uso rápido

```bash
maestro install        # instala no projeto atual
maestro skills         # lista skills disponíveis
maestro build-team     # inicia elicitação de domínio (/MAESTRO-build-team)
maestro version        # versão instalada
```

## Context Budget Protocol

Cada agente segue um protocolo de carregamento único por task:

```
1. Ler o arquivo da task
2. Raciocinar UMA VEZ sobre o que é necessário
3. Carregar apenas o necessário
4. Executar
5. Descartar — não recarregar durante a execução
```

## Arquitetura interna

```
Camada 1 — Elicitação   @intake      → domain-model.yaml
Camada 2 — Síntese      @synthesizer → blueprint.yaml
Camada 3 — Execução     Ralph loop   → agentes, tasks, workflows em arquivos
```

## Estrutura após `maestro install`

```
seu-projeto/
├── .maestro-core/
│   ├── agents/             ← intake, synthesizer, validator
│   ├── tasks/              ← elicit-domain, build-blueprint, etc.
│   ├── templates/          ← templates de geração
│   └── protocols/          ← context-budget.md
├── maestro-workspace/
│   ├── domain-models/
│   ├── blueprints/
│   └── output/
├── maestro.config.yaml
└── CLAUDE.md
```
README
ok "README.md"

# =============================================================================
# SEÇÃO 3 — PACOTE PYTHON
# =============================================================================
section "Pacote Python"

cat > maestro/__init__.py << 'INIT'
__version__ = "0.1.0"
INIT
ok "maestro/__init__.py"

# ── maestro/cli.py ────────────────────────────────────────────────────────────
cat > maestro/cli.py << 'CLI'
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
CLI
ok "maestro/cli.py"

# ── maestro/installer.py ──────────────────────────────────────────────────────
cat > maestro/installer.py << 'INSTALLER'
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

FRAMEWORK_DIR = ".maestro-core"
USER_DIR      = "maestro-workspace"
CONFIG_FILE   = "maestro.config.yaml"

# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE.md — lido automaticamente pelo Claude Code em toda sessão.
# Contém os princípios globais de Context Budget.
# ─────────────────────────────────────────────────────────────────────────────
CLAUDE_MD = """\
# CLAUDE.md — Maestro

## Meta-framework instalado

| Item      | Caminho                |
|-----------|------------------------|
| Config    | maestro.config.yaml    |
| Framework | .maestro-core/         |
| Workspace | maestro-workspace/     |

---

## Context Budget Protocol — OBRIGATÓRIO

Este é o princípio mais importante do Maestro em termos de custo operacional.
Todo agente, em toda execução de task, DEVE seguir este protocolo:

```
PASSO 1 — Ler o arquivo da task corrente (e SOMENTE ele)
PASSO 2 — Raciocinar UMA ÚNICA VEZ: "O que mais preciso para executar isso?"
PASSO 3 — Carregar apenas os arquivos identificados no Passo 2
PASSO 4 — Executar a task do início ao fim
PASSO 5 — Encerrar — NÃO recarregar arquivos durante a execução
```

### Regras de ouro

- **A task é suficiente** — ela contém todo o contexto necessário por design
- **Nunca carregue por precaução** — só carregue o que é comprovadamente necessário
- **Uma leitura por arquivo** — se já leu, não leia de novo
- **Sem carregamento de domínio completo** — nunca carregue toda uma pasta
- **context_files é o teto** — nunca carregue mais do que o declarado na task

### O que NÃO fazer

```
❌ Carregar todos os arquivos do domínio "para ter contexto"
❌ Reler um arquivo já carregado para confirmar algo
❌ Carregar o maestro.config.yaml em toda execução
❌ Carregar arquivos de outros domínios sem necessidade explícita
❌ Manter contexto carregado entre tasks diferentes
```

---

## Agentes disponíveis

| Agente       | Camada | Papel                                           |
|--------------|--------|-------------------------------------------------|
| @intake      | 1      | Elicita operações do domínio com o usuário      |
| @synthesizer | 2      | Converte domain-model em blueprint de artefatos |
| @validator   | pós-3  | Valida coerência dos artefatos gerados          |

## Skills

| Skill               | Comando CLI        | O que faz                   |
|---------------------|--------------------|-----------------------------|
| /MAESTRO-build-team | maestro build-team | Elicita domínio e gera tudo |

## Comandos CLI

```bash
maestro skills         # lista skills
maestro build-team     # inicia elicitação
maestro update         # atualiza framework
maestro version        # versão instalada
```
"""

DEFAULT_CONFIG = """\
# maestro.config.yaml
# Mapeie aqui os domínios do seu sistema.

domain_map: {}
  # vendas:
  #   path: ./vendas
  #   description: "Pipeline, propostas, contratos, fechamento"
  #   primary_tasks: []

context_routing: {}
  # vendas:
  #   always_load:
  #     - ./vendas/context/playbook.md
  #   load_on_demand:
  #     - ./vendas/pipeline/
"""


def install(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Instalando Maestro em:[/bold] {root}\n")
    _copy_framework(root)
    _create_workspace(root)
    _write_if_missing(root / CONFIG_FILE, DEFAULT_CONFIG)
    _write_if_missing(root / "CLAUDE.md", CLAUDE_MD)
    console.print("\n[green]✓ Maestro instalado.[/green]")
    console.print("  Edite [bold]maestro.config.yaml[/bold] com seus domínios.")
    console.print()


def update(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Atualizando Maestro em:[/bold] {root}\n")
    _copy_framework(root)
    console.print("\n[green]✓ .maestro-core/ atualizado.[/green]")
    console.print("  Workspace, config e CLAUDE.md foram preservados.")
    console.print()


def _copy_framework(root: Path):
    import maestro
    pkg_core = Path(maestro.__file__).parent / "core"
    dst = root / FRAMEWORK_DIR
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(pkg_core, dst)
    console.print(f"  [blue]→[/blue] .maestro-core/ sincronizado")


def _create_workspace(root: Path):
    for sub in ["domain-models", "blueprints", "output"]:
        (root / USER_DIR / sub).mkdir(parents=True, exist_ok=True)
    console.print(f"  [blue]→[/blue] maestro-workspace/ pronto")


def _write_if_missing(path: Path, content: str):
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        console.print(f"  [blue]→[/blue] {path.name} criado")
    else:
        console.print(f"  [yellow]→[/yellow] {path.name} já existe, mantido")
INSTALLER
ok "maestro/installer.py"

# ── maestro/skills/ ───────────────────────────────────────────────────────────
touch maestro/skills/__init__.py

cat > maestro/skills/build_team.py << 'BUILD_TEAM'
"""
Skill: /MAESTRO-build-team
Camada 1 → Camada 2 → Camada 3 (Ralph)
"""
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax
import yaml

console = Console()


def run(domain=None, config_path="maestro.config.yaml", auto=False):
    console.print(Panel.fit(
        "[bold cyan]/MAESTRO-build-team[/bold cyan]\n"
        "[dim]Elicitação → Síntese → Execução[/dim]",
        border_style="cyan"
    ))

    config  = _load_config(config_path)
    domains = list(config.get("domain_map", {}).keys())

    # ── CAMADA 1 ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Camada 1 — Elicitação[/bold]\n")

    domain              = _choose_domain(domain, domains, config)
    operations          = _elicit_operations(domain)

    if not operations:
        console.print("[yellow]Nenhuma operação informada. Encerrando.[/yellow]")
        return

    operations_enriched = _enrich_operations(operations)
    sequences           = _elicit_sequences(operations_enriched)
    context_hints       = _elicit_context_hints(operations_enriched)
    domain_model        = _build_domain_model(domain, operations_enriched, sequences, context_hints)
    model_path          = _save_domain_model(domain, domain_model)

    console.print(f"\n[green]✓ domain-model.yaml → {model_path}[/green]")
    _show_yaml(domain_model, "Domain Model")

    if not Confirm.ask("\nContinuar para Síntese?", default=True):
        console.print("[dim]Pausado. Rode novamente para continuar.[/dim]")
        return

    # ── CAMADA 2 ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Camada 2 — Síntese[/bold]\n")

    blueprint = _synthesize(domain_model)
    bp_path   = _save_blueprint(domain, blueprint)

    console.print(f"[green]✓ blueprint.yaml → {bp_path}[/green]")
    _show_yaml(blueprint, "Blueprint")

    if not auto:
        if not Confirm.ask("\nContinuar para Execução (Ralph)?", default=True):
            console.print("[dim]Rode 'maestro build-team --auto' para executar.[/dim]")
            return

    # ── CAMADA 3 ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Camada 3 — Execução[/bold]\n")

    from maestro.ralph.executor import run as ralph_run
    ralph_run(str(bp_path))

    console.print(f"\n[green]✓ Artefatos → maestro-workspace/output/{domain}/[/green]\n")


def _choose_domain(domain, domains, config):
    if domain:
        return domain
    if domains:
        console.print("[bold]Domínios mapeados:[/bold]")
        for i, d in enumerate(domains, 1):
            desc = config["domain_map"][d].get("description", "")
            console.print(f"  [green]{i}.[/green] {d}  [dim]{desc}[/dim]")
        console.print()
        choice = Prompt.ask("Qual domínio? (número, nome ou 'novo')", default="novo")
        if choice.isdigit() and 1 <= int(choice) <= len(domains):
            return domains[int(choice) - 1]
        if choice in domains:
            return choice
    return Prompt.ask("Nome do domínio (ex: vendas, operacao)")


def _elicit_operations(domain):
    console.print(f"[bold]Domínio:[/bold] [cyan]{domain}[/cyan]\n")
    console.print("Liste as operações principais. Mínimo 3, máximo 7.\n")

    operations = []
    i = 1
    while len(operations) < 7:
        suffix = " (mínimo)" if i <= 3 else " (ou Enter para terminar)"
        op = Prompt.ask(f"  Operação {i}{suffix}", default="")
        if not op:
            if len(operations) < 3:
                console.print(f"  [yellow]Informe mais {3 - len(operations)} operação(ões).[/yellow]")
                continue
            break
        operations.append(op)
        i += 1
    return operations


def _enrich_operations(operations):
    console.print("\n[bold]Refinamento:[/bold]\n")
    enriched = []
    for op in operations:
        console.print(f"  [cyan]{op}[/cyan]")
        decision_maker = Prompt.ask("    Quem decide que está concluída?", default="gestor")
        failure        = Prompt.ask("    O que pode dar errado?",          default="dado inválido")
        console.print()
        enriched.append({
            "id":             op.lower().strip().replace(" ", "-"),
            "intent":         op,
            "decision_maker": decision_maker,
            "failure_modes":  [failure],
        })
    return enriched


def _elicit_sequences(operations):
    ids = [op["id"] for op in operations]
    console.print("[bold]Sequências obrigatórias:[/bold]")
    for i, op_id in enumerate(ids, 1):
        console.print(f"  {i}. {op_id}")

    if not Confirm.ask("\nExiste dependência de ordem?", default=False):
        return []

    console.print("[dim]Formato: 'op-a → op-b' (b depende de a). Enter para terminar.[/dim]\n")
    sequences = []
    while True:
        pair = Prompt.ask("  Dependência", default="")
        if not pair:
            break
        if "→" in pair:
            parts = [p.strip() for p in pair.split("→")]
            if len(parts) == 2:
                sequences.append(parts)
    return sequences


def _elicit_context_hints(operations):
    """
    Pergunta ao usuário quais arquivos de contexto cada operação pode precisar.
    Esses hints viram context_files nas tasks geradas — limitando o que
    o agente pode carregar durante a execução.
    """
    console.print("\n[bold]Context Budget — arquivos de contexto por operação:[/bold]")
    console.print(
        "[dim]Para cada operação, informe caminhos de arquivos que o agente\n"
        "PODE precisar consultar. Deixe vazio se a task é auto-suficiente.\n"
        "Esses arquivos serão o TETO de contexto — o agente carrega só o necessário.[/dim]\n"
    )

    hints = {}
    for op in operations:
        console.print(f"  [cyan]{op['id']}[/cyan]")
        files = []
        while True:
            f = Prompt.ask(
                "    Arquivo de contexto (caminho relativo, ou Enter para terminar)",
                default=""
            )
            if not f:
                break
            files.append(f)
        hints[op["id"]] = files
        if files:
            console.print(f"    [dim]→ {len(files)} arquivo(s) registrado(s)[/dim]")
        console.print()

    return hints


def _build_domain_model(domain, operations, sequences, context_hints):
    EXECUTOR_RULES = {
        "aprovar":   "human",
        "autorizar": "human",
        "calcular":  "worker",
        "exportar":  "worker",
        "processar": "worker",
        "analisar":  "agent",
        "revisar":   "clone",
        "validar":   "agent",
        "gerar":     "agent",
    }

    for op in operations:
        op["executor_type"] = next(
            (v for k, v in EXECUTOR_RULES.items() if k in op["intent"].lower()),
            "agent"
        )
        op["depends_on"]    = []
        op["context_files"] = context_hints.get(op["id"], [])

    for pair in sequences:
        for op in operations:
            if op["id"] == pair[1]:
                op["depends_on"].append(pair[0])

    return {"domain": domain, "operations": operations, "sequences": sequences}


def _synthesize(domain_model):
    domain     = domain_model["domain"]
    operations = domain_model["operations"]

    squads_map = {}
    for op in operations:
        dm = op.get("decision_maker", "geral")
        squads_map.setdefault(dm, []).append(op)

    squads = []
    for dm, ops in squads_map.items():
        squad_id = f"{domain}-{dm.lower().replace(' ', '-')}"
        agent_id = f"{dm.lower().replace(' ', '-')}-agent"

        squads.append({
            "id": squad_id,
            "agents": [{
                "id":           agent_id,
                "persona_base": dm,
                "commands":     [op["id"] for op in ops],
            }],
            "tasks": [{
                "id":            op["id"],
                "intent":        op["intent"],
                "executor":      op["executor_type"],
                "quality_gate":  agent_id,
                "failure_modes": op.get("failure_modes", []),
                "depends_on":    op.get("depends_on", []),
                "context_files": op.get("context_files", []),  # ← Context Budget
            } for op in ops],
            "workflows": [{
                "id":    f"fluxo-{squad_id}",
                "steps": [op["id"] for op in ops],
            }],
        })

    return {"domain": domain, "version": "0.1.0", "squads": squads}


def _save_domain_model(domain, model):
    out = Path("maestro-workspace/domain-models")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(
        yaml.dump(model, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8"
    )
    return path


def _save_blueprint(domain, blueprint):
    out = Path("maestro-workspace/blueprints")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(
        yaml.dump(blueprint, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8"
    )
    return path


def _load_config(config_path):
    p = Path(config_path)
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {}


def _show_yaml(data, title=""):
    content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(Panel(Syntax(content, "yaml", theme="monokai"), title=title, border_style="dim"))
BUILD_TEAM
ok "maestro/skills/build_team.py"

# ── maestro/ralph/executor.py ─────────────────────────────────────────────────
touch maestro/ralph/__init__.py

cat > maestro/ralph/executor.py << 'RALPH'
"""
Ralph Executor — loop autônomo de geração de artefatos.
Respeita o Context Budget ao gerar tasks: inclui context_files como teto.
"""
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console  = Console()
OUTPUT   = "maestro-workspace/output"
PROGRESS = "maestro-workspace/ralph-progress.json"


def run(blueprint_path: str):
    blueprint = yaml.safe_load(Path(blueprint_path).read_text(encoding="utf-8"))
    domain    = blueprint.get("domain", "domain")
    progress  = _load_progress(blueprint_path)
    pending   = _get_pending(blueprint, progress)

    if not pending:
        console.print("[green]✓ Todos os artefatos já foram gerados.[/green]")
        return

    console.print(f"[bold]Ralph:[/bold] {len(pending)} artefato(s) para gerar\n")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as bar:
        job = bar.add_task("Gerando...", total=len(pending))
        for artifact in pending:
            bar.update(job, description=f"[cyan]{artifact['type']}[/cyan]: {artifact['id']}")
            content  = _generate(artifact, domain)
            out_path = _artifact_path(domain, artifact)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")
            progress["generated"].append(artifact["id"])
            _save_progress(blueprint_path, progress)
            bar.advance(job)

    _print_summary(domain, blueprint)


def _get_pending(blueprint, progress):
    done    = set(progress.get("generated", []))
    pending = []
    for squad in blueprint.get("squads", []):
        for a in squad.get("agents",    []):
            if a["id"] not in done:
                pending.append({"type": "agent",    **a,  "squad": squad["id"]})
        for t in squad.get("tasks",     []):
            if t["id"] not in done:
                pending.append({"type": "task",     **t,  "squad": squad["id"]})
        for w in squad.get("workflows", []):
            if w["id"] not in done:
                pending.append({"type": "workflow", **w,  "squad": squad["id"]})
    return pending


def _generate(artifact, domain):
    t = artifact["type"]
    if t == "agent":    return _tmpl_agent(artifact, domain)
    if t == "task":     return _tmpl_task(artifact, domain)
    if t == "workflow": return _tmpl_workflow(artifact, domain)
    return f"# {artifact['id']}\n\nTipo desconhecido: {t}\n"


def _artifact_path(domain, artifact):
    ext = ".yaml" if artifact["type"] == "workflow" else ".md"
    return Path(OUTPUT) / domain / f"{artifact['type']}s" / f"{artifact['id']}{ext}"


def _tmpl_agent(a, domain):
    """
    Agentes gerados incluem o Context Budget Protocol nos core_principles.
    """
    commands = "\n".join(
        f"  - name: {cmd}\n    description: Executa operação {cmd}"
        for cmd in a.get("commands", [])
    )
    deps = "\n".join(f"    - {cmd}.md" for cmd in a.get("commands", []))
    return f"""\
# {a['id']}

> Agente gerado pelo Maestro para o domínio `{domain}`

```yaml
agent:
  name: {a['id']}
  id: {a['id']}
  title: "{a.get('persona_base', a['id']).title()} Agent"
  icon: 🤖
  whenToUse: "Use para operações de {domain} sob responsabilidade de {a.get('persona_base', 'gestor')}"

persona:
  role: Especialista em {a.get('persona_base', domain)}
  style: Preciso, orientado a resultados
  focus: Executar operações de {domain} com qualidade e rastreabilidade

core_principles:
  # ── Context Budget Protocol (obrigatório) ──────────────────────────────────
  - CRITICAL: Leia o arquivo da task PRIMEIRO e apenas ele na ativação
  - CRITICAL: Decida UMA ÚNICA VEZ quais arquivos adicionais são necessários
  - CRITICAL: Carregue apenas o que está listado em context_files da task
  - CRITICAL: Nunca recarregue um arquivo já lido durante a mesma execução
  - CRITICAL: Nunca carregue arquivos de outros domínios sem necessidade explícita
  # ── Operação ───────────────────────────────────────────────────────────────
  - Execute apenas as operações listadas nos seus comandos
  - Sempre registre o resultado de cada operação
  - Confirme com o usuário antes de operações irreversíveis

startup_sequence:
  - Ler o arquivo da task corrente
  - Avaliar context_files declarados na task
  - Carregar apenas os necessários para esta execução específica
  - HALT até receber comando do usuário

commands:
{commands}
  - name: help
    description: Lista comandos disponíveis
  - name: exit
    description: Sai do agente

dependencies:
  tasks:
{deps}
  protocols:
    - context-budget.md
```
"""


def _tmpl_task(t, domain):
    """
    Tasks geradas incluem context_files como teto de carregamento.
    O agente pode carregar MENOS que isso, mas nunca mais.
    """
    failures      = "\n".join(f"  - {f}" for f in t.get("failure_modes", ["falha genérica"]))
    deps          = t.get("depends_on", [])
    deps_str      = "\n".join(f"  - {d}" for d in deps) if deps else "  []"
    context_files = t.get("context_files", [])

    if context_files:
        ctx_str = "\n".join(f"  - {f}" for f in context_files)
        ctx_note = (
            "# Teto de contexto: o agente decide o que é relevante entre esses arquivos.\n"
            "# Carrega apenas o necessário, uma única vez, antes de executar.\n"
        )
    else:
        ctx_str  = "  []  # task auto-suficiente — não carregue arquivos adicionais"
        ctx_note = "# Task auto-suficiente: não requer arquivos externos.\n"

    return f"""\
---
task: {t['id']}
domain: {domain}
executor_type: {t.get('executor', 'agent')}
quality_gate: human

# ── Context Budget ───────────────────────────────────────────────────────────
# {ctx_note}
# REGRA: Leia este arquivo primeiro. Avalie context_files. Carregue só o
# necessário. Execute. Não recarregue nada durante a execução.
context_files:
{ctx_str}

# ── Definição da task ─────────────────────────────────────────────────────────
entrada:
  - campo: contexto
    tipo: string
    obrigatorio: true

saida:
  - campo: resultado
    tipo: object
    destino: maestro-workspace/output/{domain}/results/{t['id']}.json

failure_modes:
{failures}

depends_on:
{deps_str}

checklist:
  - "[ ] Validar entrada"
  - "[ ] Carregar context_files necessários (UMA VEZ)"
  - "[ ] Executar operação principal"
  - "[ ] Confirmar resultado"
  - "[ ] Registrar saída"

acceptance_criteria:
  - Resultado documentado e rastreável
  - Failure modes verificados
  - Nenhum arquivo carregado além dos declarados em context_files
---

# {t['id']}

## Propósito
{t.get('intent', 'Executar operação do domínio ' + domain)}

## Protocolo de execução

### 1. Preparação de contexto (fazer UMA única vez)
Antes de executar, avalie quais arquivos de `context_files` são realmente
necessários para esta execução específica. Carregue apenas esses.
Não carregue todos por precaução.

### 2. Execução
Execute a operação conforme as regras do domínio `{domain}`.

### 3. Saída
Registre o resultado. Encerre sem recarregar nada.
"""


def _tmpl_workflow(w, domain):
    steps = "\n".join(
        f"  - step: {i+1}\n    task: {s}\n    on_failure: halt"
        for i, s in enumerate(w.get("steps", []))
    )
    return f"""\
# {w['id']}

domain: {domain}
version: "0.1.0"

steps:
{steps}

on_complete:
  action: notify
  message: "Workflow {w['id']} concluído"
"""


def _load_progress(blueprint_path):
    p = Path(PROGRESS)
    if p.exists():
        data = json.loads(p.read_text())
        if data.get("blueprint") == blueprint_path:
            return data
    return {"blueprint": blueprint_path, "generated": []}


def _save_progress(blueprint_path, data):
    data["blueprint"] = blueprint_path
    Path(PROGRESS).parent.mkdir(parents=True, exist_ok=True)
    Path(PROGRESS).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _print_summary(domain, blueprint):
    console.print(f"\n[bold]Artefatos gerados em {OUTPUT}/{domain}/:[/bold]")
    for squad in blueprint.get("squads", []):
        console.print(f"\n  Squad: [cyan]{squad['id']}[/cyan]")
        for a in squad.get("agents",    []): console.print(f"    [green]agents/[/green]{a['id']}.md")
        for t in squad.get("tasks",     []): console.print(f"    [green]tasks/[/green]{t['id']}.md")
        for w in squad.get("workflows", []): console.print(f"    [green]workflows/[/green]{w['id']}.yaml")
    console.print()
RALPH
ok "maestro/ralph/executor.py"

# =============================================================================
# SEÇÃO 4 — PROTOCOLO (novo)
# =============================================================================
section "Context Budget Protocol"

cat > maestro/core/protocols/context-budget.md << 'CBP'
# context-budget.md

> Protocolo obrigatório para todos os agentes do Maestro

## O problema que este protocolo resolve

Sem controle, um agente tende a carregar contexto "por precaução":
carrega a pasta inteira do domínio, relê arquivos já lidos, mantém
contexto entre tasks. Isso multiplica o consumo de tokens por 5-10x
sem aumentar a qualidade do resultado.

## O protocolo

```
PASSO 1  Ler o arquivo da task — e apenas ele
PASSO 2  Raciocinar UMA VEZ: "quais arquivos em context_files
         são realmente necessários para ESTA execução?"
PASSO 3  Carregar apenas os arquivos identificados no Passo 2
PASSO 4  Executar a task do início ao fim
PASSO 5  Encerrar — não recarregar nada
```

## Regras

| Regra | Descrição |
|-------|-----------|
| Task-first | A task é lida primeiro, sempre |
| Decisão única | O raciocínio sobre contexto acontece uma única vez |
| Teto declarado | O agente nunca carrega mais do que `context_files` da task |
| Sem recarregamento | Um arquivo lido não é lido novamente na mesma execução |
| Sem cross-domain | Arquivos de outros domínios só com necessidade explícita na task |

## O que context_files significa

`context_files` em uma task é o **teto de permissão** — não uma obrigação.
O agente avalia quais desses arquivos são relevantes para a execução
específica e carrega apenas esses.

```yaml
# Exemplo de task com context_files
context_files:
  - ./vendas/context/playbook.md      # carregue se a operação envolve processo de venda
  - ./vendas/context/pricing.md       # carregue se a operação envolve preço
  - ./vendas/pipeline/template.md     # carregue se precisa criar um registro no pipeline
```

Se a operação não usa preço, `pricing.md` não é carregado — mesmo estando na lista.

## Task auto-suficiente

Se `context_files: []`, a task foi projetada para ser executada
apenas com as informações já contidas nela. Não carregue nada adicional.

## Impacto esperado

| Cenário | Tokens por execução |
|---------|-------------------|
| Sem protocolo (carrega tudo) | ~50-100k |
| Com Context Budget | ~5-15k |
| Redução | ~85% |
CBP
ok "protocols/context-budget.md"

# =============================================================================
# SEÇÃO 5 — AGENTES DO CORE
# =============================================================================
section "Agentes do core (3 agentes)"

cat > maestro/core/agents/intake.md << 'INTAKE'
# intake

> Agente de Elicitação — Camada 1 do Maestro

```yaml
agent:
  name: Intake
  id: intake
  title: Domain Intake Agent
  icon: 🎯
  whenToUse: "Use para iniciar a elicitação de um novo domínio"

persona:
  role: Especialista em descoberta de domínio e modelagem de intenção
  style: Curioso, direto, perguntas concretas
  identity: >
    Transforma intenção do usuário em domain-model.yaml preciso.
    Nunca inventa operações.
  focus: Elicitação mínima e precisa

core_principles:
  # ── Context Budget ─────────────────────────────────────────────────────────
  - CRITICAL: Na ativação, leia APENAS o arquivo da task corrente
  - CRITICAL: Decida UMA VEZ o que mais precisa — carregue só isso
  - CRITICAL: Não recarregue arquivos já lidos nesta sessão
  # ── Elicitação ─────────────────────────────────────────────────────────────
  - CRITICAL: Nunca invente operações — extraia apenas do que o usuário diz
  - CRITICAL: Confirme o domain model antes de salvar
  - Máximo 3 perguntas por rodada
  - Prefira exemplos concretos

startup_sequence:
  - Ler elicit-domain.md (única leitura de arquivo no startup)
  - HALT — aguardar comando do usuário

commands:
  - name: elicit
    description: Inicia elicitação de um domínio
  - name: confirm
    description: Confirma e salva o domain model
  - name: help
    description: Mostra os comandos disponíveis
  - name: exit
    description: Sai do agente

dependencies:
  tasks:
    - elicit-domain.md
  templates:
    - domain-model-tmpl.yaml
  protocols:
    - context-budget.md
```

## Protocolo

1. Identificar 3–7 operações principais
2. Para cada: decision_maker + failure_mode + context_files relevantes
3. Mapear sequências obrigatórias
4. Confirmar e salvar domain-model.yaml
INTAKE
ok "agents/intake.md"

cat > maestro/core/agents/synthesizer.md << 'SYNTH'
# synthesizer

> Agente de Síntese — Camada 2 do Maestro

```yaml
agent:
  name: Synthesizer
  id: synthesizer
  title: Domain Synthesizer Agent
  icon: ⚗️
  whenToUse: "Use para converter domain-model.yaml em blueprint.yaml"

persona:
  role: Arquiteto de sistemas de agentes
  style: Analítico, sistemático
  identity: >
    Lê domain-model.yaml, aplica regras de inferência e produz
    blueprint.yaml com executor_type, squads, agentes e workflows.
  focus: Transformar intenção em estrutura

core_principles:
  # ── Context Budget ─────────────────────────────────────────────────────────
  - CRITICAL: Leia APENAS o domain-model.yaml do domínio sendo sintetizado
  - CRITICAL: Não carregue outros domain-models para comparação
  - CRITICAL: Uma leitura do domain-model — não releia durante a síntese
  # ── Síntese ────────────────────────────────────────────────────────────────
  - CRITICAL: executor != quality_gate em todas as tasks
  - Agrupe por decision_maker para squads coesos
  - Sinalizar ambiguidades antes de assumir executor_type

startup_sequence:
  - Ler build-blueprint.md (única leitura no startup)
  - HALT — aguardar o domain-model.yaml do domínio a sintetizar

commands:
  - name: synthesize
    description: Converte domain-model.yaml em blueprint.yaml
  - name: preview
    description: Mostra o blueprint sem salvar
  - name: help
    description: Mostra os comandos
  - name: exit
    description: Sai do agente

dependencies:
  tasks:
    - build-blueprint.md
    - infer-executor.md
  templates:
    - blueprint-tmpl.yaml
  protocols:
    - context-budget.md
```

## Regras de inferência

| Padrão no intent       | executor_type  |
|------------------------|----------------|
| aprovar, autorizar     | human          |
| calcular, exportar     | worker         |
| metodologia específica | clone          |
| demais                 | agent (default)|
SYNTH
ok "agents/synthesizer.md"

cat > maestro/core/agents/validator.md << 'VALIDATOR'
# validator

> Agente de Validação — pós Camada 3 do Maestro

```yaml
agent:
  name: Validator
  id: validator
  title: Artifact Validator Agent
  icon: 🔍
  whenToUse: "Use para validar artefatos gerados pelo Ralph"

persona:
  role: Especialista em qualidade de sistemas de agentes
  style: Criterioso, foca em correção estrutural
  identity: >
    Verifica se agentes, tasks e workflows estão completos,
    coerentes e prontos para uso operacional.
  focus: Garantir que os artefatos formem um sistema funcional

core_principles:
  # ── Context Budget ─────────────────────────────────────────────────────────
  - CRITICAL: Para validar um artefato, leia APENAS esse artefato
  - CRITICAL: Não carregue o domínio inteiro para validar um único arquivo
  - CRITICAL: Se precisar verificar referência cruzada, leia só o arquivo referenciado
  # ── Validação ──────────────────────────────────────────────────────────────
  - CRITICAL: Artefato só passa com score >= 7/10
  - CRITICAL: Sinalizar dependências quebradas imediatamente
  - Gerar relatório mesmo quando aprovado

startup_sequence:
  - Ler validate-artifact.md (única leitura no startup)
  - HALT — aguardar o artefato a validar

commands:
  - name: validate
    description: Valida todos os artefatos do domínio
  - name: validate-artifact
    description: Valida um artefato específico
  - name: report
    description: Exibe o último relatório
  - name: help
    description: Mostra os comandos
  - name: exit
    description: Sai do agente

dependencies:
  tasks:
    - validate-artifact.md
  protocols:
    - context-budget.md
```

## Score de validação (/10)

### Agente: id+name+icon (+2) | comandos (+2) | dependencies existem (+2) | principles (+2) | persona (+2)
### Task: executor_type (+2) | executor!=quality_gate (+2) | acceptance_criteria (+2) | checklist (+2) | depends_on (+2)
### Workflow: steps existem (+3) | sem ciclos (+3) | sequência coerente (+4)
VALIDATOR
ok "agents/validator.md"

# =============================================================================
# SEÇÃO 6 — TASKS DO CORE
# =============================================================================
section "Tasks do core (4 tasks)"

cat > maestro/core/tasks/elicit-domain.md << 'ELICIT'
---
task: elicit-domain
executor: "@intake"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Task auto-suficiente. Não carregue arquivos adicionais.
# Todo o protocolo de elicitação está descrito aqui.
context_files: []

entrada:
  - campo: domain_name
    tipo: string
    obrigatorio: true

saida:
  - campo: domain_model
    tipo: yaml
    destino: maestro-workspace/domain-models/{domain_name}.yaml

checklist:
  - "[ ] Identificar 3-7 operações principais"
  - "[ ] Mapear decision_maker por operação"
  - "[ ] Identificar failure_modes por operação"
  - "[ ] Coletar context_files por operação (teto de contexto)"
  - "[ ] Mapear sequências obrigatórias"
  - "[ ] Confirmar domain model com o usuário"

acceptance_criteria:
  - Toda operação tem id, intent e executor_type definidos
  - Toda operação tem context_files declarado (pode ser vazio)
  - Nenhuma operação foi inventada
  - Usuário confirmou antes de salvar
---

# elicit-domain

## Propósito
Extrair operações do domínio e produzir domain-model.yaml.
Inclui coleta de context_files — o teto de contexto de cada operação.

## Passos

1. Pergunte as 3-7 operações principais
2. Para cada: decision_maker, failure_mode, e arquivos que o agente
   PODE precisar consultar (context_files)
3. Mapeie sequências obrigatórias
4. Confirme e salve
ELICIT
ok "tasks/elicit-domain.md"

cat > maestro/core/tasks/infer-executor.md << 'INFER'
---
task: infer-executor
executor: "@synthesizer"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Task auto-suficiente. As regras de inferência estão aqui.
context_files: []

entrada:
  - campo: operation
    tipo: object
    obrigatorio: true

saida:
  - campo: executor_type
    tipo: enum
    valores: [agent, worker, clone, human]

checklist:
  - "[ ] Verificar palavras-chave do intent"
  - "[ ] Verificar decision_maker"
  - "[ ] Aplicar fallback (agent) se inconclusivo"
  - "[ ] Registrar justificativa"

acceptance_criteria:
  - executor_type é um dos 4 valores válidos
  - Justificativa registrada
---

# infer-executor

## Regras (aplicar em ordem)

1. decision_maker humano + critério subjetivo → `human`
2. Intent: calcular, exportar, transformar, processar → `worker`
3. Requer metodologia específica de domínio → `clone`
4. Default → `agent`
INFER
ok "tasks/infer-executor.md"

cat > maestro/core/tasks/build-blueprint.md << 'BLUEPRINT'
---
task: build-blueprint
executor: "@synthesizer"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Carregue APENAS o domain-model.yaml do domínio sendo sintetizado.
# Não carregue outros domain-models ou arquivos do domínio.
context_files:
  - maestro-workspace/domain-models/{domain}.yaml

entrada:
  - campo: domain_model_path
    tipo: string
    obrigatorio: true

saida:
  - campo: blueprint
    tipo: yaml
    destino: maestro-workspace/blueprints/{domain}.yaml

checklist:
  - "[ ] Ler domain-model.yaml (única leitura)"
  - "[ ] Inferir executor_type de cada operação"
  - "[ ] Agrupar em squads por decision_maker"
  - "[ ] Gerar um agente por squad"
  - "[ ] Gerar uma task por operação (com context_files herdado)"
  - "[ ] Gerar um workflow por squad"
  - "[ ] Verificar executor != quality_gate"
  - "[ ] Confirmar com o usuário"

acceptance_criteria:
  - Todo squad tem pelo menos 1 agente, 1 task e 1 workflow
  - Nenhuma task tem executor igual ao quality_gate
  - context_files de cada operação está preservado no blueprint
---

# build-blueprint

## Propósito
Converter domain-model.yaml em blueprint.yaml.
O context_files de cada operação é preservado no blueprint
e será inserido nas tasks geradas pelo Ralph.
BLUEPRINT
ok "tasks/build-blueprint.md"

cat > maestro/core/tasks/validate-artifact.md << 'VALIDATE'
---
task: validate-artifact
executor: "@validator"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Carregue APENAS o artefato sendo validado.
# Se precisar verificar referência cruzada, carregue só o arquivo referenciado.
context_files:
  - "{artifact_path}"

entrada:
  - campo: artifact_path
    tipo: string
    obrigatorio: true
  - campo: artifact_type
    tipo: enum
    valores: [agent, task, workflow]
    obrigatorio: true

saida:
  - campo: validation_result
    tipo: object
    campos: [passed, score, issues, recommendations]

checklist:
  - "[ ] Ler apenas o artefato indicado"
  - "[ ] Verificar campos obrigatórios"
  - "[ ] Verificar referências (carregar só o referenciado se necessário)"
  - "[ ] Verificar executor != quality_gate (tasks)"
  - "[ ] Gerar relatório com score"

acceptance_criteria:
  - Score >= 7/10 para aprovar
  - Issues críticos bloqueiam
  - Nenhum arquivo carregado além do artefato e suas referências diretas
---

# validate-artifact

## Protocolo de validação lean

1. Leia o artefato — apenas ele
2. Identifique referências a outros arquivos
3. Para cada referência que precisa verificar: carregue só esse arquivo
4. Calcule o score
5. Gere o relatório
VALIDATE
ok "tasks/validate-artifact.md"

# =============================================================================
# SEÇÃO 7 — TEMPLATES DO CORE
# =============================================================================
section "Templates do core (4 templates)"

cat > maestro/core/templates/domain-model-tmpl.yaml << 'DMTMPL'
domain: "{{DOMAIN_NAME}}"

operations:
  - id: "{{OPERATION_ID}}"
    intent: "{{OPERATION_INTENT}}"
    decision_maker: "{{DECISION_MAKER}}"
    failure_modes:
      - "{{FAILURE_MODE_1}}"
    executor_type: agent
    depends_on: []
    context_files: []    # teto de contexto — arquivos que o agente PODE carregar

sequences: []
DMTMPL
ok "templates/domain-model-tmpl.yaml"

cat > maestro/core/templates/blueprint-tmpl.yaml << 'BPTMPL'
domain: "{{DOMAIN_NAME}}"
version: "0.1.0"

squads:
  - id: "{{SQUAD_ID}}"
    agents:
      - id: "{{AGENT_ID}}"
        persona_base: "{{DECISION_MAKER}}"
        commands:
          - "{{OPERATION_ID}}"
    tasks:
      - id: "{{OPERATION_ID}}"
        intent: "{{OPERATION_INTENT}}"
        executor: agent
        quality_gate: "{{AGENT_ID}}"
        failure_modes:
          - "{{FAILURE_MODE}}"
        depends_on: []
        context_files: []    # herdado do domain-model — teto de contexto
    workflows:
      - id: "fluxo-{{SQUAD_ID}}"
        steps:
          - "{{OPERATION_ID}}"
BPTMPL
ok "templates/blueprint-tmpl.yaml"

cat > maestro/core/templates/agent-generated-tmpl.md << 'AGTTMPL'
# {{AGENT_ID}}

> Agente gerado pelo Maestro para o domínio `{{DOMAIN}}`

```yaml
agent:
  name: {{AGENT_ID}}
  id: {{AGENT_ID}}
  title: "{{PERSONA_BASE}} Agent"
  icon: 🤖
  whenToUse: "Use para operações de {{DOMAIN}}"

persona:
  role: Especialista em {{PERSONA_BASE}}
  style: Preciso, orientado a resultados
  focus: Executar operações de {{DOMAIN}}

core_principles:
  - CRITICAL: Leia o arquivo da task PRIMEIRO e apenas ele na ativação
  - CRITICAL: Decida UMA VEZ quais arquivos de context_files são necessários
  - CRITICAL: Carregue apenas o necessário — nunca por precaução
  - CRITICAL: Não recarregue arquivos já lidos durante a mesma execução
  - Execute apenas as operações listadas nos seus comandos

startup_sequence:
  - Ler o arquivo da task corrente (única leitura no startup)
  - HALT — aguardar comando

commands:
  {{COMMANDS}}
  - name: help
    description: Lista comandos disponíveis
  - name: exit
    description: Sai do agente

dependencies:
  tasks:
    {{TASK_DEPENDENCIES}}
  protocols:
    - context-budget.md
```
AGTTMPL
ok "templates/agent-generated-tmpl.md"

cat > maestro/core/templates/task-generated-tmpl.md << 'TGTTMPL'
---
task: {{TASK_ID}}
domain: {{DOMAIN}}
executor_type: {{EXECUTOR_TYPE}}
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Teto de contexto: carregue apenas o necessário entre esses arquivos.
# Se a lista estiver vazia, a task é auto-suficiente.
context_files:
  {{CONTEXT_FILES}}

entrada:
  - campo: contexto
    tipo: string
    obrigatorio: true

saida:
  - campo: resultado
    tipo: object

failure_modes:
  {{FAILURE_MODES}}

depends_on:
  {{DEPENDS_ON}}

checklist:
  - "[ ] Ler task (já feito)"
  - "[ ] Avaliar context_files — carregar só o necessário (UMA VEZ)"
  - "[ ] Executar operação principal"
  - "[ ] Confirmar resultado"
  - "[ ] Registrar saída"

acceptance_criteria:
  - Resultado documentado
  - Nenhum arquivo carregado além de context_files
---

# {{TASK_ID}}

## Propósito
{{INTENT}}

## Execução

1. Avalie `context_files` — carregue apenas o necessário para esta execução
2. Execute
3. Registre e encerre
TGTTMPL
ok "templates/task-generated-tmpl.md"

# =============================================================================
# SEÇÃO 8 — TESTES
# =============================================================================
section "Testes"

touch tests/__init__.py

cat > tests/test_cli.py << 'TESTS'
from click.testing import CliRunner
from maestro.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["version"])
    assert result.exit_code == 0
    assert "Maestro" in result.output


def test_skills_lists_build_team():
    runner = CliRunner()
    result = runner.invoke(main, ["skills"])
    assert result.exit_code == 0
    assert "MAESTRO-build-team" in result.output


def test_skills_shows_description():
    runner = CliRunner()
    result = runner.invoke(main, ["skills"])
    assert "Elicita" in result.output
TESTS
ok "tests/test_cli.py"

# =============================================================================
# SEÇÃO 9 — INSTALA O PACOTE
# =============================================================================
section "Instalando pacote em modo editable"

if pip install -e . -q; then
    ok "pip install -e . concluído — comando 'maestro' disponível"
else
    warn "pip install falhou. Rode manualmente: pip install -e ."
fi

# =============================================================================
# RESUMO FINAL
# =============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Maestro criado com sucesso!                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Estrutura gerada:"
echo ""
echo -e "  maestro/core/"
echo -e "  ├── protocols/"
echo -e "  │   └── context-budget.md      ← protocolo de consumo de contexto"
echo -e "  ├── agents/"
echo -e "  │   ├── intake.md              ← Camada 1: Elicitação"
echo -e "  │   ├── synthesizer.md         ← Camada 2: Síntese"
echo -e "  │   └── validator.md           ← Validação pós-geração"
echo -e "  ├── tasks/"
echo -e "  │   ├── elicit-domain.md       ← context_files: []"
echo -e "  │   ├── infer-executor.md      ← context_files: []"
echo -e "  │   ├── build-blueprint.md     ← context_files: [domain-model.yaml]"
echo -e "  │   └── validate-artifact.md  ← context_files: [artefato]"
echo -e "  └── templates/"
echo -e "      ├── domain-model-tmpl.yaml"
echo -e "      ├── blueprint-tmpl.yaml"
echo -e "      ├── agent-generated-tmpl.md  ← inclui Context Budget"
echo -e "      └── task-generated-tmpl.md   ← inclui context_files"
echo ""
echo -e "  Context Budget aplicado em:"
echo -e "    ${GREEN}✓${NC} CLAUDE.md         ← princípio global"
echo -e "    ${GREEN}✓${NC} Todos os agentes  ← startup_sequence + core_principles"
echo -e "    ${GREEN}✓${NC} Todas as tasks    ← campo context_files como teto"
echo -e "    ${GREEN}✓${NC} Ralph executor    ← propaga context_files para artefatos gerados"
echo -e "    ${GREEN}✓${NC} protocols/        ← documento de referência"
echo ""
echo -e "  ${BLUE}Teste agora:${NC}"
echo -e "    ${GREEN}maestro version${NC}"
echo -e "    ${GREEN}maestro skills${NC}"
echo -e "    ${GREEN}maestro build-team${NC}"
echo ""
echo -e "  ${BLUE}Suba para o GitHub:${NC}"
echo -e "    ${GREEN}git init && git add . && git commit -m 'feat: Maestro com Context Budget'${NC}"
echo -e "    ${GREEN}git remote add origin https://github.com/SEU-USUARIO/maestro.git${NC}"
echo -e "    ${GREEN}git push -u origin main${NC}"
echo ""
