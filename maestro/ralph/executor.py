"""
Ralph Executor — loop autônomo de geração de artefatos.
Respeita o Context Budget ao gerar tasks: inclui context_files como teto.
"""
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

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

    # ── Scaffold: cria estrutura de pastas do domínio ─────────────────────────
    domain_path = Path(".") / domain
    if domain_path.exists() or Confirm.ask(
        f"\nCriar estrutura de pastas em ./{domain}/?", default=True
    ):
        _scaffold_domain(str(domain_path))

    # ── Scaffold: cria STRUCTURE.md na raiz do projeto ────────────────────────
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


def _scaffold_domain(domain_path: str):
    """
    Cria a estrutura de pastas padrão de um domínio.
    Chamada pelo Ralph antes de gerar os artefatos.
    Preserva arquivos existentes — só cria o que falta.
    """
    root = Path(domain_path)
    structure = [
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
    created = []
    for sub in structure:
        folder = root / sub
        folder.mkdir(parents=True, exist_ok=True)
        gitkeep = folder / ".gitkeep"
        if not any(folder.iterdir()) and not gitkeep.exists():
            gitkeep.touch()
            created.append(str(folder))

    if created:
        console.print(f"  [blue]→[/blue] Estrutura criada em {root.name}/")
    return root


def _scaffold_structure_md(project_root: Path):
    """
    Cria STRUCTURE.md na raiz do projeto se não existir.
    Descreve a convenção de pastas para agentes de IA.
    """
    path = project_root / "STRUCTURE.md"
    if path.exists():
        return

    content = """\
# STRUCTURE.md

> Documento de referência para agentes de IA operando neste repositório.
> Descreve onde criar, ler e mover arquivos — independente do domínio de negócio.
> Gerado automaticamente pelo Maestro. Atualize se a convenção mudar.

---

## Princípio geral

Este repositório é organizado em domínios. Cada domínio representa uma área
de responsabilidade do sistema. Todos os domínios seguem a mesma estrutura
interna de subpastas.

Um agente de IA nunca deve assumir onde um arquivo vive — deve consultar
este documento antes de criar ou ler qualquer arquivo.

---

## Estrutura interna de um domínio

```
{dominio}/
├── context/          ← identidade e regras permanentes do domínio
├── data/
│   ├── raw/          ← dados brutos recebidos de fontes externas
│   ├── processed/    ← dados transformados, prontos para leitura por agentes
│   └── snapshots/    ← cópias pontuais de estado
├── ops/
│   ├── tasks/        ← trabalho em aberto (uma tarefa = um arquivo)
│   ├── templates/    ← modelos reutilizáveis, nunca modificados diretamente
│   └── history/      ← tarefas concluídas ou encerradas
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

---

## Critérios por pasta

### context/
Arquivos que definem como o domínio funciona: regras, processos, personas,
glossário, critérios de decisão. Muda raramente (semanas ou meses).
O arquivo principal é sempre `context/playbook.md`.

Não vai aqui: dados variáveis, arquivos gerados por ferramentas externas,
rascunhos ou versões intermediárias.

### data/raw/
Dados brutos recebidos de fontes externas sem transformação: exports de APIs,
CSVs baixados, dumps. Atualizado por scripts, nunca manualmente.

NUNCA leia arquivos de data/raw/ diretamente em um agente. Use data/processed/.

### data/processed/
Dados de raw/ transformados em markdown legível por agentes. É aqui que
um agente lê dados externos. Declare o arquivo específico em context_files
da task — não carregue a pasta inteira.

### data/snapshots/
Cópias pontuais de estado do domínio em uma data específica. Consulte
apenas quando a task pede explicitamente comparação histórica.

### ops/tasks/
Trabalho em aberto — uma tarefa ativa por arquivo. Quando uma tarefa for
concluída ou encerrada, mova o arquivo para ops/history/. Nunca delete.

Formato de nome: {descricao-curta}-{identificador}.md

### ops/templates/
Modelos reutilizáveis. Nunca modifique um template diretamente — leia-o,
gere uma instância preenchida e salve em ops/tasks/.

Formato de nome: {nome}-template.md

### ops/history/
Tarefas encerradas, independente do resultado. O resultado (ganhou, perdeu,
cancelado, motivo) fica registrado dentro do arquivo, não no nome da pasta.

Consulte apenas quando a task pedir explicitamente histórico.

### reports/
Saídas geradas por agentes ou scripts. Nunca sobrescreva um relatório
existente — crie um novo com data atualizada.

- weekly/  → relatorio-YYYY-WNN.md
- monthly/ → relatorio-YYYY-MM.md
- adhoc/   → nome descritivo do assunto

---

## Regras de nomeação

| Situação | Formato | Exemplo |
|----------|---------|---------|
| Playbook | `playbook.md` | `playbook.md` |
| Tarefa ativa | `{descricao}-{id}.md` | `proposta-acme.md` |
| Template | `{nome}-template.md` | `proposta-template.md` |
| Dado processado | `{fonte}-YYYY-MM.md` | `notion-2025-03.md` |
| Relatório semanal | `relatorio-YYYY-WNN.md` | `relatorio-2025-W14.md` |
| Relatório mensal | `relatorio-YYYY-MM.md` | `relatorio-2025-03.md` |
| Snapshot | `snapshot-YYYY-MM-DD.md` | `snapshot-2025-03-01.md` |

Regras gerais: sempre minúsculas, hífens em vez de espaços, sem caracteres especiais.

---

## Context Budget — regra de ouro para agentes

Um agente nunca deve carregar arquivos por precaução. Para cada task:

1. Leia apenas o arquivo da task
2. Decida uma única vez quais arquivos adicionais são necessários
3. Carregue apenas esses — sempre os menores e mais específicos
4. Execute do início ao fim sem recarregar nada

Prioridade de carregamento (do menor para o maior custo):

```
ops/tasks/{arquivo}.md          ← sempre (é a task em si)
context/playbook.md             ← quase sempre
ops/templates/{template}.md     ← quando a task gera um documento
data/processed/{arquivo}.md     ← quando a task precisa de dados
reports/                        ← raramente, só com histórico explícito
data/raw/                       ← NUNCA diretamente
ops/history/                    ← só quando a task pede histórico
```

---

## Quando um arquivo cruza domínios

O arquivo vive no domínio que o mantém, não no que o consome.
O domínio consumidor declara o caminho completo em context_files:

```yaml
context_files:
  - ./{dominio-origem}/ops/templates/proposta-template.md
```

Nunca copie o arquivo para outro domínio. Referencie sempre o original.

---

*Gerado pelo Maestro v{version}. Consulte STRUCTURE.md antes de criar qualquer arquivo.*
"""
    path.write_text(content.replace("{version}", "0.1.0"), encoding="utf-8")
    console.print(f"  [blue]→[/blue] STRUCTURE.md criado na raiz do projeto")
