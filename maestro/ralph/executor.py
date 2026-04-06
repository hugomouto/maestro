"""Ralph Executor — geração de artefatos + scaffold de domínio."""
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

console  = Console()
OUTPUT   = "maestro-workspace/output"
PROGRESS = "maestro-workspace/ralph-progress.json"

DOMAIN_STRUCTURE = [
    "context", "data/raw", "data/processed", "data/snapshots",
    "ops/tasks", "ops/templates", "ops/history",
    "reports/weekly", "reports/monthly", "reports/adhoc",
]


def run(blueprint_path: str):
    blueprint = yaml.safe_load(Path(blueprint_path).read_text(encoding="utf-8"))
    domain    = blueprint.get("domain", "domain")
    progress  = _load_progress(blueprint_path)
    pending   = _get_pending(blueprint, progress)

    if not pending:
        console.print("[green]✓ Todos os artefatos já foram gerados.[/green]")
        return

    console.print(f"[bold]Ralph:[/bold] {len(pending)} artefato(s) para gerar\n")

    domain_path = Path(".") / domain
    if not domain_path.exists() or Confirm.ask(f"Criar/atualizar estrutura em ./{domain}/?", default=True):
        _scaffold_domain(domain_path)

    _scaffold_structure_md(Path("."))

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


def _scaffold_domain(root: Path):
    for sub in DOMAIN_STRUCTURE:
        folder = root / sub
        folder.mkdir(parents=True, exist_ok=True)
        gitkeep = folder / ".gitkeep"
        if not [f for f in folder.iterdir() if f.name != ".gitkeep"] and not gitkeep.exists():
            gitkeep.touch()
    console.print(f"  [blue]→[/blue] Estrutura criada em [cyan]{root.name}/[/cyan]")


def _scaffold_structure_md(project_root: Path):
    path = project_root / "STRUCTURE.md"
    if path.exists():
        return
    path.write_text("# STRUCTURE.md\n\nConsulte CLAUDE.md para a convenção de pastas.\n", encoding="utf-8")


def _get_pending(blueprint, progress):
    done, pending = set(progress.get("generated", [])), []
    for squad in blueprint.get("squads", []):
        for a in squad.get("agents",    []):
            if a["id"] not in done: pending.append({"type": "agent",    **a,  "squad": squad["id"]})
        for t in squad.get("tasks",     []):
            if t["id"] not in done: pending.append({"type": "task",     **t,  "squad": squad["id"]})
        for w in squad.get("workflows", []):
            if w["id"] not in done: pending.append({"type": "workflow", **w,  "squad": squad["id"]})
    return pending


def _generate(artifact, domain):
    t = artifact["type"]
    if t == "agent":    return _tmpl_agent(artifact, domain)
    if t == "task":     return _tmpl_task(artifact, domain)
    if t == "workflow": return _tmpl_workflow(artifact, domain)
    return f"# {artifact['id']}\n"


def _artifact_path(domain, artifact):
    ext = ".yaml" if artifact["type"] == "workflow" else ".md"
    return Path(OUTPUT) / domain / f"{artifact['type']}s" / f"{artifact['id']}{ext}"


def _tmpl_agent(a, domain):
    role     = a.get("persona_base", a["id"])
    commands = "\n".join(f"  - name: {cmd}\n    description: Executa {cmd}" for cmd in a.get("commands", []))
    deps     = "\n".join(f"    - {cmd}.md" for cmd in a.get("commands", []))
    return f"""\
# {a['id']}
> Agente gerado pelo Maestro para o domínio `{domain}`

```yaml
agent:
  id: {a['id']}
  title: "{role.replace('-', ' ').title()} Agent"
  whenToUse: "Use para operações de {role} no domínio {domain}"

persona:
  role: Especialista em {role}
  scope: Executa apenas as operações listadas em commands
  focus: "{role} dentro do domínio {domain}"

core_principles:
  - CRITICAL: Leia o arquivo da task PRIMEIRO e apenas ele na ativação
  - CRITICAL: Decida UMA VEZ quais context_files são necessários
  - CRITICAL: Nunca carregue data/raw/ — use data/processed/
  - CRITICAL: Não recarregue arquivos já lidos na mesma execução
  - Execute apenas as operações listadas nos seus commands

startup_sequence:
  - Ler o arquivo da task corrente
  - HALT — aguardar comando

commands:
{commands}
  - name: help
    description: Lista comandos
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
    failures     = "\n".join(f"  - {f}" for f in t.get("failure_modes", ["falha genérica"]))
    deps         = t.get("depends_on", [])
    deps_str     = "\n".join(f"  - {d}" for d in deps) if deps else "  []"
    ctx          = t.get("context_files", [])
    ctx_str      = "\n".join(f"  - {f}" for f in ctx) if ctx else "  []"
    return f"""\
---
task: {t['id']}
domain: {domain}
agent: {t.get('agent', 'agent')}
executor_type: {t.get('executor', 'agent')}
quality_gate: {t.get('quality_gate', 'gestor')}

context_files:
{ctx_str}

failure_modes:
{failures}

depends_on:
{deps_str}

checklist:
  - "[ ] Avaliar context_files — carregar só o necessário"
  - "[ ] Executar operação"
  - "[ ] Registrar resultado"
---

# {t['id']}

## Propósito
{t.get('intent', 'Executar operação do domínio ' + domain)}

## Execução
1. Avalie context_files — carregue só o necessário
2. Execute conforme `{domain}/context/playbook.md`
3. Registre e encerre
"""


def _tmpl_workflow(w, domain):
    steps = "\n".join(f"  - step: {i+1}\n    task: {s}\n    on_failure: halt" for i, s in enumerate(w.get("steps", [])))
    return f"""\
# {w['id']}
domain: {domain}
agent: {w.get('agent', 'agent')}
version: "0.2.0"

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
        n_a = len(squad.get("agents", []))
        n_t = len(squad.get("tasks", []))
        n_w = len(squad.get("workflows", []))
        console.print(f"\n  Squad: [cyan]{squad['id']}[/cyan]  [dim]{n_a} agente(s) · {n_t} task(s) · {n_w} workflow(s)[/dim]\n")
        for a in squad.get("agents", []):
            console.print(f"    [green]agents/[/green]{a['id']}.md  [dim]→ {', '.join(a.get('commands', []))}[/dim]")
        for t in squad.get("tasks", []):
            console.print(f"    [green]tasks/[/green]{t['id']}.md  [dim]executor: {t.get('agent', '?')}[/dim]")
        for w in squad.get("workflows", []):
            console.print(f"    [green]workflows/[/green]{w['id']}.yaml")
    console.print()
