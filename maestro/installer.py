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

## Estrutura de domínio — convenção obrigatória

Todo domínio neste projeto segue a estrutura abaixo.
Consulte `STRUCTURE.md` na raiz para a referência completa.

```
{dominio}/
├── context/         ← regras permanentes — leia context/playbook.md
├── data/
│   ├── raw/         ← NUNCA leia diretamente
│   ├── processed/   ← leia aqui dados externos
│   └── snapshots/
├── ops/
│   ├── tasks/       ← trabalho em aberto
│   ├── templates/   ← modelos reutilizáveis
│   └── history/     ← concluídos e encerrados
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

Prioridade de leitura para agentes:
1. ops/tasks/{arquivo}.md     — sempre
2. context/playbook.md        — quase sempre
3. ops/templates/             — ao gerar documentos
4. data/processed/            — ao consumir dados externos
5. data/raw/                  — NUNCA

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

context_routing: {}
  # vendas:
  #   always_load:
  #     - ./vendas/context/playbook.md
  #   load_on_demand:
  #     - ./vendas/data/processed/
  #     - ./vendas/ops/templates/
  #   never_load:
  #     - ./vendas/data/raw/
  #     - ./vendas/ops/history/
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
