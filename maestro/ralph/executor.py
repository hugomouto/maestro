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
