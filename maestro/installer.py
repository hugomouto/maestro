"""
Maestro Installer — Out of the Box
"""
import re
import shutil
import yaml
from pathlib import Path
from rich.console import Console
console = Console()

FRAMEWORK_DIR = ".maestro-core"
USER_DIR      = "maestro-workspace"
CONFIG_FILE   = "maestro.config.yaml"
BLOCK_START   = "<!-- MAESTRO:framework -->"
BLOCK_END     = "<!-- /MAESTRO:framework -->"

# =============================================================================
# FRAMEWORK_BLOCK — regenerado em todo install/update
# Para adicionar uma skill: inclua uma linha na tabela abaixo
# =============================================================================
FRAMEWORK_BLOCK = """\
<!-- MAESTRO:framework -->
<!-- Bloco gerenciado pelo Maestro. Regenerado em todo install/update. -->

## Skills disponíveis

| Skill | Comando CLI | O que faz |
|-------|-------------|-----------|
| /MAESTRO-build-team | `maestro build-team` | Elicita domínio, gera agentes especializados por role, cria estrutura de pastas |
| /MAESTRO-create-domain | `maestro create-domain` | Cria um novo domínio com estrutura de pastas e playbook.md |

---

## Agentes do core

| Agente | Camada | Papel |
|--------|--------|-------|
| @intake | 1 | Elicita operações e sugere agent_role |
| @synthesizer | 2 | Converte domain-model em blueprint (agrupa por agent_role) |
| @validator | pós-3 | Valida artefatos gerados pelo Ralph |

---

## Estrutura de domínio

```
{dominio}/
├── context/playbook.md  ← LEIA PRIMEIRO — regras e operações do domínio
├── data/
│   ├── raw/             ← NUNCA carregue diretamente
│   ├── processed/       ← dados externos prontos para leitura
│   └── snapshots/
├── ops/
│   ├── tasks/           ← trabalho em aberto
│   ├── templates/       ← modelos reutilizáveis
│   └── history/         ← concluídos
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

---

## Context Budget Protocol

```
1. Ler APENAS o arquivo da task
2. Decidir UMA VEZ quais context_files carregar
3. Carregar apenas o necessário
4. Executar
5. Encerrar — não recarregar
```

`data/raw/` nunca entra em `context_files`.

---

## Comandos CLI

```bash
maestro install          # instala e inicializa o projeto completo
maestro update           # atualiza framework + cria domínios novos do config
maestro create-domain    # cria um novo domínio interativamente
maestro build-team       # elicita domínio e gera agentes
maestro skills           # lista skills
maestro version          # versão instalada
```
<!-- /MAESTRO:framework -->"""

USER_SECTION = """\
## Este projeto

<!-- Descreva aqui o projeto. Esta seção nunca é sobrescrita pelo Maestro. -->

| Item | Caminho |
|------|---------|
| Config | maestro.config.yaml |
| Framework | .maestro-core/ |
| Workspace | maestro-workspace/ |
| Estrutura | STRUCTURE.md |
"""

DEFAULT_CONFIG = """\
# maestro.config.yaml
# Adicione seus domínios e rode `maestro update` para criar as pastas.

domain_map: {}

# Exemplo:
# domain_map:
#   vendas:
#     description: "Pipeline, propostas, contratos, fechamento"
#   marketing:
#     description: "Marca, conteúdo, campanhas, redes sociais"
#   operacao:
#     description: "Fornecedores, estoque, processos, SLAs"
#   produto:
#     description: "Roadmap, specs, lançamentos"
#   gestao:
#     description: "Financeiro, OKRs, decisões estratégicas"

context_routing: {}
"""

STRUCTURE_MD = """\
# STRUCTURE.md
> Referência de convenção de pastas. Gerado pelo Maestro.

## Estrutura de um domínio

```
{dominio}/
├── context/          ← regras permanentes
│   └── playbook.md   ← documento principal — sempre leia primeiro
├── data/
│   ├── raw/          ← dados brutos (NUNCA em context_files)
│   ├── processed/    ← dados prontos para agentes
│   └── snapshots/    ← histórico pontual
├── ops/
│   ├── tasks/        ← trabalho em aberto
│   ├── templates/    ← modelos reutilizáveis
│   └── history/      ← concluídos
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

## Prioridade de leitura

```
ops/tasks/{arquivo}.md      ← sempre
context/playbook.md         ← quase sempre
ops/templates/              ← ao gerar documentos
data/processed/             ← ao consumir dados externos
data/raw/                   ← NUNCA
ops/history/                ← só com histórico explícito
```

## Nomeação

- Sempre minúsculas com hífens
- Playbook: `playbook.md`
- Tarefa: `{descricao}-{id}.md`
- Template: `{nome}-template.md`
- Dado processado: `{fonte}-YYYY-MM.md`
- Relatório: `relatorio-YYYY-MM.md`
"""


def install(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Instalando Maestro em:[/bold] {root}\n")
    _copy_framework(root)
    _create_workspace(root)
    _write_if_missing(root / CONFIG_FILE, DEFAULT_CONFIG)
    _write_always(root / "STRUCTURE.md", STRUCTURE_MD)
    _sync_claude_md(root)
    _scaffold_domains(root)
    _scaffold_slash_commands(root)
    console.print("\n[green]✓ Maestro instalado.[/green]")
    console.print()
    console.print("  Próximos passos:")
    console.print("  1. Edite [bold]maestro.config.yaml[/bold] — adicione seus domínios")
    console.print("  2. Rode [bold]maestro update[/bold] — cria pastas e playbooks")
    console.print("  3. Preencha cada [bold]{dominio}/context/playbook.md[/bold]")
    console.print("  4. Rode [bold]maestro build-team[/bold] — gera os agentes")
    console.print()


def update(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Atualizando Maestro em:[/bold] {root}\n")
    _copy_framework(root)
    _write_always(root / "STRUCTURE.md", STRUCTURE_MD)
    _sync_claude_md(root)
    _scaffold_domains(root)
    _scaffold_slash_commands(root)
    console.print("\n[green]✓ Maestro atualizado.[/green]")
    console.print()


def _sync_claude_md(root: Path):
    """
    Cria ou atualiza o CLAUDE.md.
    - Se não existe: cria com bloco framework + seção user
    - Se existe com bloco: substitui só o bloco framework
    - Se existe sem bloco (versão antiga): insere o bloco no topo
    """
    path = root / "CLAUDE.md"

    if not path.exists():
        content = (
            "# CLAUDE.md — Maestro\n\n"
            + FRAMEWORK_BLOCK
            + "\n\n---\n\n"
            + USER_SECTION
        )
        path.write_text(content, encoding="utf-8")
        console.print(f"  [blue]→[/blue] CLAUDE.md criado")
        return

    content = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}",
        re.DOTALL
    )

    if pattern.search(content):
        updated = pattern.sub(FRAMEWORK_BLOCK, content)
        path.write_text(updated, encoding="utf-8")
        console.print(f"  [blue]→[/blue] CLAUDE.md atualizado")
    else:
        lines = content.split("\n")
        insert_at = next(
            (i + 1 for i, l in enumerate(lines) if l.startswith("# ")), 1
        )
        lines.insert(insert_at, f"\n{FRAMEWORK_BLOCK}\n")
        path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"  [blue]→[/blue] CLAUDE.md migrado")


def _scaffold_domains(root: Path):
    config_path = root / CONFIG_FILE
    if not config_path.exists():
        return
    config  = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    domains = config.get("domain_map", {})
    if not domains:
        console.print(f"  [dim]Sem domínios no config — edite {CONFIG_FILE} e rode update[/dim]")
        return
    from maestro.domain import create_domain
    for name, cfg in domains.items():
        create_domain(name=name, root=root, description=(cfg or {}).get("description", ""))


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




def _scaffold_slash_commands(root: Path):
    """
    Cria .claude/commands/*.md para cada skill registrada.
    Esses arquivos são lidos pelo Claude Code como slash commands.
    """
    commands_dir = root / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    command_file = commands_dir / "MAESTRO-build-team.md"
    content = """Você é o Maestro operando no modo /MAESTRO-build-team.

Execute o fluxo completo de elicitação de domínio:

**Camada 1 — Elicitação**
Pergunte ao usuário:
1. Nome do domínio (ex: vendas, marketing, operacao)
2. As 3–7 operações principais desse domínio
3. Para cada operação:
   - Sugira um `agent_role` com base no intent (ex: researcher, data-analyst, content-producer, instagram-agent) e peça confirmação
   - Quem aprova/decide que está concluída? (decision_maker)
   - O que pode dar errado? (failure_mode)

**Camada 2 — Síntese**
Com base nas respostas, gere o `domain-model.yaml` agrupando por `agent_role`.
Cada `agent_role` distinto = um agente especializado distinto.
O `decision_maker` vira o `quality_gate` da task — não determina o agente.

Regras obrigatórias:
- `context_files` sempre começa com `./{dominio}/context/playbook.md`
- Operações que geram documentos incluem `./{dominio}/ops/templates/`
- Operações que consomem dados incluem `./{dominio}/data/processed/`
- NUNCA inclua `data/raw/` em `context_files`

**Camada 3 — Scaffold**
Informe ao usuário que deve rodar `maestro build-team` no terminal para gerar os artefatos físicos.

Mostre um resumo do que será gerado:
- Quantos agentes e quais roles
- Quantas tasks
- Estrutura de pastas que será criada

Consulte `.maestro-core/agents/intake.md` e `.maestro-core/protocols/context-budget.md` para referência.
"""
    command_file.write_text(content, encoding="utf-8")
    console.print(f"  [blue]→[/blue] .claude/commands/MAESTRO-build-team.md criado")

    create_domain_file = commands_dir / "MAESTRO-create-domain.md"
    create_domain_content = """Você é o Maestro operando no modo /MAESTRO-create-domain.

Crie um novo domínio no projeto atual.

**Passo 1 — Elicitação**
Pergunte ao usuário:
1. Nome do domínio (minúsculas, hífens, sem espaços — ex: vendas, marketing, operacao)
2. Descrição curta do domínio (uma frase — o que ele faz e o que NÃO faz)

**Passo 2 — Confirmação**
Mostre o resumo do que será criado:
- Pasta `{nome}/` com subpastas: context/, data/raw/, data/processed/, data/snapshots/, ops/tasks/, ops/templates/, ops/history/, reports/weekly/, reports/monthly/, reports/adhoc/
- Arquivo `{nome}/context/playbook.md` pré-preenchido
- Registro em `maestro.config.yaml`

Peça confirmação antes de prosseguir.

**Passo 3 — Criação**
Informe ao usuário que deve rodar no terminal:
```
maestro create-domain
```
Ou, se já souber o nome:
```
maestro create-domain --name {nome}
```

Após criado, oriente:
1. Preencha `{nome}/context/playbook.md` com as regras do domínio
2. Rode `maestro build-team` para gerar os agentes
"""
    create_domain_file.write_text(create_domain_content, encoding="utf-8")
    console.print(f"  [blue]→[/blue] .claude/commands/MAESTRO-create-domain.md criado")

def _write_if_missing(path: Path, content: str):
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        console.print(f"  [blue]→[/blue] {path.name} criado")
    else:
        console.print(f"  [yellow]→[/yellow] {path.name} já existe, mantido")


def _write_always(path: Path, content: str):
    path.write_text(content, encoding="utf-8")
    console.print(f"  [blue]→[/blue] {path.name} atualizado")
