"""
Ralph Executor — loop autônomo de geração de artefatos.
Cria a estrutura física de pastas do domínio antes de gerar os artefatos.
Suporta múltiplos agentes especializados via agent_role.
"""
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
    "context",
    "data/raw",
    "data/processed",
    "data/snapshots",
    "ops/tasks",
    "ops/templates",
    "ops/history",
    "reports/weekly",
    "reports/monthly",
    "reports/adhoc",
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

    # ── Scaffold: estrutura física do domínio ─────────────────────────────────
    domain_path = Path(".") / domain
    if not domain_path.exists() or Confirm.ask(
        f"Criar/atualizar estrutura de pastas em ./{domain}/?", default=True
    ):
        _scaffold_domain(domain_path)

    # ── Scaffold: STRUCTURE.md na raiz do projeto ─────────────────────────────
    _scaffold_structure_md(Path("."))

    # ── Geração de artefatos ──────────────────────────────────────────────────
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
    """Cria a estrutura de pastas padrão de um domínio. Preserva o que existe."""
    for sub in DOMAIN_STRUCTURE:
        folder = root / sub
        folder.mkdir(parents=True, exist_ok=True)
        gitkeep = folder / ".gitkeep"
        if not list(folder.iterdir()) and not gitkeep.exists():
            gitkeep.touch()
    console.print(f"  [blue]→[/blue] Estrutura de pastas criada em [cyan]{root.name}/[/cyan]")


def _scaffold_structure_md(project_root: Path):
    """Cria STRUCTURE.md na raiz do projeto se não existir."""
    path = project_root / "STRUCTURE.md"
    if path.exists():
        return

    content = """\
# STRUCTURE.md

> Documento de referência para agentes de IA operando neste repositório.
> Gerado automaticamente pelo Maestro. Atualize se a convenção mudar.

---

## Princípio geral

Este repositório é organizado em domínios. Todos seguem a mesma estrutura interna.
Um agente nunca deve assumir onde um arquivo vive — consulte este documento primeiro.

---

## Estrutura interna de um domínio

```
{dominio}/
├── context/          ← identidade e regras permanentes do domínio
├── data/
│   ├── raw/          ← dados brutos de fontes externas (NUNCA leia diretamente)
│   ├── processed/    ← dados transformados em markdown, prontos para agentes
│   └── snapshots/    ← cópias pontuais de estado para comparação histórica
├── ops/
│   ├── tasks/        ← trabalho em aberto (uma tarefa = um arquivo)
│   ├── templates/    ← modelos reutilizáveis, nunca modificados diretamente
│   └── history/      ← tarefas concluídas ou encerradas
└── reports/
    ├── weekly/       ← relatorio-YYYY-WNN.md
    ├── monthly/      ← relatorio-YYYY-MM.md
    └── adhoc/        ← nome descritivo do assunto
```

---

## Critérios por pasta

| Pasta | O que vai | O que NÃO vai |
|-------|-----------|---------------|
| `context/` | Regras, playbook, personas, glossário | Dados variáveis, rascunhos |
| `data/raw/` | Exports de API, CSVs brutos | Qualquer coisa processada |
| `data/processed/` | Resumos em markdown de dados externos | Dados brutos |
| `data/snapshots/` | Estado do domínio em data específica | Dados atuais |
| `ops/tasks/` | Trabalho em aberto | Tarefas concluídas, templates |
| `ops/templates/` | Modelos reutilizáveis | Instâncias preenchidas |
| `ops/history/` | Tarefas encerradas (com resultado dentro) | Trabalho em aberto |
| `reports/` | Saídas geradas por agentes | Dados brutos, work-in-progress |

---

## Prioridade de leitura para agentes

```
ops/tasks/{arquivo}.md          ← sempre (é a task em si)
context/playbook.md             ← quase sempre
ops/templates/{template}.md     ← ao gerar documentos
data/processed/{arquivo}.md     ← ao consumir dados externos
reports/                        ← só com histórico explícito
data/raw/                       ← NUNCA
ops/history/                    ← só quando a task pede histórico
```

---

## Nomeação de arquivos

- Sempre minúsculas, hífens em vez de espaços
- Playbook: `playbook.md`
- Tarefa ativa: `{descricao}-{id}.md`
- Template: `{nome}-template.md`
- Dado processado: `{fonte}-YYYY-MM.md`
- Relatório: `relatorio-YYYY-MM.md` ou `relatorio-YYYY-WNN.md`

---

## Arquivos que cruzam domínios

O arquivo vive no domínio que o mantém. O consumidor referencia via context_files:

```yaml
context_files:
  - ./{dominio-origem}/ops/templates/{nome}-template.md
```

Nunca copie — sempre referencie o original.

---

*Gerado pelo Maestro. Consulte antes de criar qualquer arquivo.*
"""
    path.write_text(content, encoding="utf-8")
    console.print(f"  [blue]→[/blue] STRUCTURE.md criado na raiz do projeto")


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
    commands = "\n".join(
        f"  - name: {cmd}\n    description: Executa operação {cmd}"
        for cmd in a.get("commands", [])
    )
    deps = "\n".join(f"    - {cmd}.md" for cmd in a.get("commands", []))
    role = a.get("persona_base", a["id"])

    return f"""\
# {a['id']}

> Agente gerado pelo Maestro para o domínio `{domain}`

```yaml
agent:
  name: {a['id']}
  id: {a['id']}
  title: "{role.replace('-', ' ').title()} Agent"
  icon: 🤖
  whenToUse: "Use para operações de {role} no domínio {domain}"

persona:
  role: Especialista em {role}
  scope: Executa apenas as operações listadas em commands — nada além
  style: Preciso, orientado a resultado, não faz perguntas desnecessárias
  focus: "{role} dentro do domínio {domain}"

core_principles:
  # ── Context Budget Protocol ────────────────────────────────────────────────
  - CRITICAL: Leia o arquivo da task PRIMEIRO e apenas ele na ativação
  - CRITICAL: Decida UMA VEZ quais arquivos de context_files são necessários
  - CRITICAL: Carregue apenas o necessário — nunca por precaução
  - CRITICAL: Não recarregue arquivos já lidos durante a mesma execução
  - CRITICAL: Nunca carregue data/raw/ — use sempre data/processed/
  # ── Operação ───────────────────────────────────────────────────────────────
  - Execute apenas as operações listadas nos seus commands
  - Arquivos novos vão em ops/tasks/ — nunca em context/ ou data/
  - Tarefas concluídas movem para ops/history/ — nunca delete

startup_sequence:
  - Ler o arquivo da task corrente (única leitura no startup)
  - Avaliar context_files declarados na task
  - Carregar apenas os necessários para esta execução
  - HALT — aguardar comando

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
    failures      = "\n".join(f"  - {f}" for f in t.get("failure_modes", ["falha genérica"]))
    deps          = t.get("depends_on", [])
    deps_str      = "\n".join(f"  - {d}" for d in deps) if deps else "  []"
    context_files = t.get("context_files", [])
    agent_id      = t.get("agent", "agent")
    quality_gate  = t.get("quality_gate", "gestor")

    if context_files:
        ctx_str  = "\n".join(f"  - {f}" for f in context_files)
        ctx_note = "# Teto de contexto — carregue apenas o necessário, uma única vez."
    else:
        ctx_str  = "  []  # task auto-suficiente"
        ctx_note = "# Task auto-suficiente — não carregue arquivos adicionais."

    return f"""\
---
task: {t['id']}
domain: {domain}
agent: {agent_id}
executor_type: {t.get('executor', 'agent')}
quality_gate: {quality_gate}

# ── Context Budget ────────────────────────────────────────────────────────────
{ctx_note}
# REGRA: Leia esta task. Avalie context_files. Carregue só o necessário. Execute.
context_files:
{ctx_str}

# ── Definição ─────────────────────────────────────────────────────────────────
entrada:
  - campo: contexto
    tipo: string
    obrigatorio: true

saida:
  - campo: resultado
    tipo: object
    destino: {domain}/reports/adhoc/{t['id']}.md

failure_modes:
{failures}

depends_on:
{deps_str}

checklist:
  - "[ ] Ler task (feito)"
  - "[ ] Avaliar context_files — carregar só o necessário (UMA VEZ)"
  - "[ ] Executar operação principal"
  - "[ ] Confirmar resultado"
  - "[ ] Registrar saída em reports/ ou ops/history/"

acceptance_criteria:
  - Resultado documentado e rastreável
  - Nenhum arquivo carregado além de context_files
---

# {t['id']}

## Propósito
{t.get('intent', 'Executar operação do domínio ' + domain)}

## Execução

1. Avalie `context_files` — carregue apenas o necessário
2. Execute conforme as regras em `{domain}/context/playbook.md`
3. Registre o resultado e encerre
"""


def _tmpl_workflow(w, domain):
    steps = "\n".join(
        f"  - step: {i+1}\n    task: {s}\n    on_failure: halt"
        for i, s in enumerate(w.get("steps", []))
    )
    agent = w.get("agent", "agent")
    return f"""\
# {w['id']}

domain: {domain}
agent: {agent}
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
        n_agents    = len(squad.get("agents",    []))
        n_tasks     = len(squad.get("tasks",     []))
        n_workflows = len(squad.get("workflows", []))
        console.print(
            f"\n  Squad: [cyan]{squad['id']}[/cyan]  "
            f"[dim]{n_agents} agente(s) · {n_tasks} task(s) · {n_workflows} workflow(s)[/dim]\n"
        )
        for a in squad.get("agents", []):
            cmds = ", ".join(a.get("commands", []))
            console.print(f"    [green]agents/[/green]{a['id']}.md  [dim]→ {cmds}[/dim]")
        console.print()
        for t in squad.get("tasks", []):
            console.print(
                f"    [green]tasks/[/green]{t['id']}.md  "
                f"[dim]executor: {t.get('agent', '?')}[/dim]"
            )
        console.print()
        for w in squad.get("workflows", []):
            console.print(
                f"    [green]workflows/[/green]{w['id']}.yaml  "
                f"[dim]agente: {w.get('agent', '?')}[/dim]"
            )
    console.print()
