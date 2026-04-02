#!/usr/bin/env bash
# =============================================================================
# fix-maestro-install-outofthebox.sh
# Atualiza o installer.py para que `maestro install` crie tudo necessário:
#   - CLAUDE.md com skills e protocolo (sempre atualizado no update)
#   - STRUCTURE.md com convenção de pastas
#   - Estrutura de domínios (context/, data/, ops/, reports/) com playbook.md
#   - maestro update também cria domínios novos adicionados ao config
# Uso: bash fix-maestro-install-outofthebox.sh (na raiz do repositório maestro/)
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()      { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}!${NC} $1"; }
section() { echo -e "\n${CYAN}── $1 ──${NC}"; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   M A E S T R O  —  Out of the Box Install  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "pyproject.toml" ] || [ ! -d "maestro" ]; then
    echo "ERRO: rode na raiz do repositório maestro/"
    exit 1
fi

# =============================================================================
# Detecta pip
# =============================================================================
section "Detectando ambiente Python"

PIP_CMD=""
EXTRA_FLAGS=""

if [ -n "$VIRTUAL_ENV" ]; then
    PIP_CMD="$VIRTUAL_ENV/bin/pip"
    ok "venv ativo: $VIRTUAL_ENV"
elif command -v pipx &>/dev/null && pipx list 2>/dev/null | grep -q maestro; then
    echo -e "  ${BLUE}→${NC} reinstalando via pipx"
    pipx install -e . --force 2>/dev/null || pipx reinstall maestro
    ok "pipx reinstalado"
    PIP_CMD="SKIP"
else
    warn "Sem venv — usando --break-system-packages"
    PIP_CMD="pip"
    EXTRA_FLAGS="--break-system-packages"
fi

# =============================================================================
# SEÇÃO 1 — installer.py completo
# =============================================================================
section "maestro/installer.py"

cat > maestro/installer.py << 'INSTALLER'
"""
Maestro Installer — Out of the Box
------------------------------------
`maestro install` cria tudo que um projeto precisa para operar imediatamente:

  1. .maestro-core/          — framework copiado do pacote
  2. maestro-workspace/      — diretórios de trabalho
  3. CLAUDE.md               — skills, protocolo, estrutura (bloco versionado)
  4. STRUCTURE.md            — referência de convenção de pastas
  5. maestro.config.yaml     — config genérica comentada
  6. {dominio}/              — estrutura de pastas + playbook.md por domínio

`maestro update` atualiza tudo exceto conteúdo criado pelo usuário:
  - Regenera bloco FRAMEWORK no CLAUDE.md
  - Cria domínios novos adicionados ao config (não toca nos existentes)
  - Sincroniza .maestro-core/
"""
import re
import shutil
import yaml
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

console = Console()

FRAMEWORK_DIR = ".maestro-core"
USER_DIR      = "maestro-workspace"
CONFIG_FILE   = "maestro.config.yaml"

BLOCK_START = "<!-- MAESTRO:framework -->"
BLOCK_END   = "<!-- /MAESTRO:framework -->"

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

# =============================================================================
# Bloco FRAMEWORK — regenerado em todo install/update
# Para adicionar uma skill: inclua uma linha na tabela abaixo
# =============================================================================
FRAMEWORK_BLOCK = """\
<!-- MAESTRO:framework -->
<!-- Este bloco é gerenciado pelo Maestro. Não edite manualmente. -->
<!-- Rode `maestro update` para atualizar após instalar nova versão. -->

## Skills disponíveis

| Skill | Comando CLI | O que faz |
|-------|-------------|-----------|
| /MAESTRO-build-team | `maestro build-team` | Elicita domínio, gera agentes especializados, cria estrutura de pastas |

Para listar via terminal: `maestro skills`

---

## Agentes do core

| Agente | Camada | Papel |
|--------|--------|-------|
| @intake | 1 | Elicita operações do domínio com o usuário |
| @synthesizer | 2 | Converte domain-model em blueprint de artefatos |
| @validator | pós-3 | Valida coerência dos artefatos gerados |

Agentes ficam em `.maestro-core/agents/` — leia antes de operar num domínio.

---

## Estrutura de domínio — convenção obrigatória

Todo domínio segue esta estrutura. Consulte `STRUCTURE.md` para referência completa.

```
{dominio}/
├── context/
│   └── playbook.md  ← LEIA PRIMEIRO — regras, operações, glossário do domínio
├── data/
│   ├── raw/         ← NUNCA leia diretamente em context_files
│   ├── processed/   ← leia aqui dados externos transformados
│   └── snapshots/   ← comparação histórica
├── ops/
│   ├── tasks/       ← trabalho em aberto (uma tarefa = um arquivo)
│   ├── templates/   ← modelos reutilizáveis, nunca modificar diretamente
│   └── history/     ← tarefas concluídas ou encerradas
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

Prioridade de leitura (menor → maior custo de tokens):
1. `ops/tasks/{arquivo}.md` — sempre
2. `context/playbook.md` — quase sempre
3. `ops/templates/` — ao gerar documentos
4. `data/processed/` — ao consumir dados externos
5. `data/raw/` — **NUNCA**

---

## Context Budget Protocol — OBRIGATÓRIO

Todo agente, em toda execução de task, DEVE seguir:

```
PASSO 1 — Ler APENAS o arquivo da task corrente
PASSO 2 — Raciocinar UMA VEZ: "O que mais preciso?"
PASSO 3 — Carregar apenas o necessário
PASSO 4 — Executar do início ao fim
PASSO 5 — Encerrar — NÃO recarregar durante a execução
```

Regras:
- `context_files` é o teto — nunca carregue mais do que o declarado
- `data/raw/` nunca entra em `context_files`
- Um arquivo lido não é lido novamente na mesma execução

---

## Comandos CLI

```bash
maestro install        # instala e inicializa o projeto completo
maestro update         # atualiza framework + cria domínios novos do config
maestro skills         # lista skills disponíveis
maestro build-team     # elicita domínio e gera agentes especializados
maestro version        # versão instalada
```
<!-- /MAESTRO:framework -->"""

USER_SECTION = """\
## Este projeto

<!-- Descreva aqui o projeto e seus domínios -->
<!-- Esta seção NÃO é atualizada pelo Maestro — edite livremente -->

Domínios configurados em `maestro.config.yaml`.
Estrutura de cada domínio documentada em `STRUCTURE.md`.
"""

DEFAULT_CONFIG = """\
# maestro.config.yaml
# Mapeie aqui os domínios do seu projeto.
# Após editar, rode `maestro update` para criar as pastas automaticamente.

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

# Exemplo (preenchido automaticamente pelo build-team):
# context_routing:
#   vendas:
#     always_load:
#       - ./vendas/context/playbook.md
#     load_on_demand:
#       - ./vendas/data/processed/
#       - ./vendas/ops/templates/
#     never_load:
#       - ./vendas/data/raw/
#       - ./vendas/ops/history/
"""

STRUCTURE_MD = """\
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
├── context/
│   └── playbook.md   ← documento principal do domínio — sempre leia primeiro
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
| `ops/history/` | Tarefas encerradas (resultado registrado dentro) | Trabalho em aberto |
| `reports/` | Saídas geradas por agentes | Dados brutos, WIP |

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

| Situação | Formato | Exemplo |
|----------|---------|---------|
| Playbook | `playbook.md` | `playbook.md` |
| Tarefa ativa | `{descricao}-{id}.md` | `proposta-acme.md` |
| Template | `{nome}-template.md` | `proposta-template.md` |
| Dado processado | `{fonte}-YYYY-MM.md` | `notion-2025-03.md` |
| Relatório semanal | `relatorio-YYYY-WNN.md` | `relatorio-2025-W14.md` |
| Relatório mensal | `relatorio-YYYY-MM.md` | `relatorio-2025-03.md` |

Regras: sempre minúsculas, hífens em vez de espaços, sem caracteres especiais.

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

PLAYBOOK_TEMPLATE = """\
# playbook.md — {domain}

> Documento principal do domínio `{domain}`.
> Lido pelo agente antes de qualquer operação.
> Preencha as seções abaixo. Mantenha enxuto — menos de 400 linhas.

---

## Propósito

<!-- O que este domínio faz e o que NÃO faz -->
<!-- Exemplo: "Gerencia o ciclo de conversão de leads em clientes fechados." -->
<!-- Exemplo do que não faz: "Não inclui geração de leads (isso é marketing)." -->

...

---

## Operações

<!-- Liste as operações principais e quem decide que cada uma está concluída -->

| Operação | Responsável | Critério de conclusão |
|----------|-------------|----------------------|
| ...      | ...         | ...                  |

---

## Regras de negócio

<!-- Critérios, limites e condições obrigatórias que o agente deve respeitar -->

- ...

---

## Fontes de dados

<!-- De onde vêm os dados e onde ficam na estrutura de pastas -->

| Fonte | Localização |
|-------|-------------|
| ...   | `{domain}/data/processed/` |

---

## Interfaces com outros domínios

<!-- Com quais domínios este conversa, o que recebe e o que entrega -->

| Direção | Domínio | O que troca |
|---------|---------|-------------|
| Recebe de | ... | ... |
| Entrega para | ... | ... |

---

## Glossário

<!-- Termos específicos deste domínio que o agente precisa conhecer -->

| Termo | Definição |
|-------|-----------|
| ...   | ...       |
"""


def install(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Instalando Maestro em:[/bold] {root}\n")

    _copy_framework(root)
    _create_workspace(root)
    _write_if_missing(root / CONFIG_FILE, DEFAULT_CONFIG)
    _write_structure_md(root)
    _install_claude_md(root)
    _scaffold_domains(root)

    console.print("\n[green]✓ Maestro instalado.[/green]")
    console.print()
    console.print("  Próximos passos:")
    console.print("  1. Edite [bold]maestro.config.yaml[/bold] — adicione seus domínios")
    console.print("  2. Rode [bold]maestro update[/bold] — cria as pastas e playbooks")
    console.print("  3. Preencha [bold]{{dominio}}/context/playbook.md[/bold] em cada domínio")
    console.print("  4. Rode [bold]maestro build-team[/bold] — gera os agentes")
    console.print()


def update(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Atualizando Maestro em:[/bold] {root}\n")

    _copy_framework(root)
    _update_claude_md(root)
    _write_structure_md(root)
    _scaffold_domains(root)

    console.print("\n[green]✓ Maestro atualizado.[/green]")
    console.print("  Workspace e config preservados.")
    console.print()


def _scaffold_domains(root: Path):
    """
    Lê os domínios do maestro.config.yaml e cria a estrutura de pastas
    + playbook.md para cada um que ainda não existe.
    Nunca sobrescreve arquivos existentes.
    """
    config_path = root / CONFIG_FILE
    if not config_path.exists():
        return

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    domains = config.get("domain_map", {})

    if not domains:
        console.print(
            f"  [dim]Nenhum domínio em {CONFIG_FILE} — "
            f"adicione domínios e rode 'maestro update'[/dim]"
        )
        return

    for domain_name, domain_config in domains.items():
        domain_root = root / domain_name
        _create_domain_structure(domain_root, domain_name, domain_config or {})


def _create_domain_structure(domain_root: Path, domain_name: str, domain_config: dict):
    """Cria estrutura de pastas e playbook.md para um domínio."""
    is_new = not domain_root.exists()

    # Cria todas as subpastas
    for sub in DOMAIN_STRUCTURE:
        folder = domain_root / sub
        folder.mkdir(parents=True, exist_ok=True)
        gitkeep = folder / ".gitkeep"
        if not any(f for f in folder.iterdir() if f.name != ".gitkeep"):
            gitkeep.touch()

    # Cria playbook.md se não existir
    playbook_path = domain_root / "context" / "playbook.md"
    if not playbook_path.exists():
        description = domain_config.get("description", "")
        content = PLAYBOOK_TEMPLATE.format(domain=domain_name)
        if description:
            content = content.replace(
                "## Propósito",
                f"## Propósito\n\n{description}"
            )
        playbook_path.write_text(content, encoding="utf-8")

        if is_new:
            console.print(
                f"  [blue]→[/blue] [cyan]{domain_name}/[/cyan] criado  "
                f"[dim]context/, data/, ops/, reports/, playbook.md[/dim]"
            )
        else:
            console.print(
                f"  [blue]→[/blue] [cyan]{domain_name}/context/playbook.md[/cyan] criado"
            )
    else:
        console.print(
            f"  [yellow]→[/yellow] [cyan]{domain_name}/[/cyan] já existe — preservado"
        )


def _write_structure_md(root: Path):
    """Sempre escreve/atualiza o STRUCTURE.md — é documentação do framework."""
    path = root / "STRUCTURE.md"
    path.write_text(STRUCTURE_MD, encoding="utf-8")
    if not path.exists():
        console.print(f"  [blue]→[/blue] STRUCTURE.md criado")
    else:
        console.print(f"  [blue]→[/blue] STRUCTURE.md atualizado")


def _install_claude_md(root: Path):
    path = root / "CLAUDE.md"
    if path.exists():
        _update_claude_md(root)
        return
    content = f"# CLAUDE.md — Maestro\n\n{FRAMEWORK_BLOCK}\n\n---\n\n{USER_SECTION}"
    path.write_text(content, encoding="utf-8")
    console.print(f"  [blue]→[/blue] CLAUDE.md criado")


def _update_claude_md(root: Path):
    path = root / "CLAUDE.md"
    if not path.exists():
        _install_claude_md(root)
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
        # CLAUDE.md antigo sem bloco — insere após o título
        lines = content.split("\n")
        insert_at = 1
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_at = i + 1
                break
        lines.insert(insert_at, f"\n{FRAMEWORK_BLOCK}\n")
        path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"  [blue]→[/blue] CLAUDE.md migrado — bloco framework inserido")


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

# =============================================================================
# SEÇÃO 2 — reinstala
# =============================================================================
section "Reinstalando pacote"

if [ "$PIP_CMD" = "SKIP" ]; then
    ok "pipx já reinstalou"
elif [ -n "$PIP_CMD" ]; then
    if $PIP_CMD install -e . -q $EXTRA_FLAGS; then
        ok "pacote reinstalado"
    else
        warn "Falhou. Tente manualmente:"
        echo "  pip install -e . --break-system-packages"
        exit 1
    fi
fi

# =============================================================================
# SEÇÃO 3 — propaga para projetos instalados
# =============================================================================
section "Propagando para projetos instalados"

PROPAGATED=0
for dir in ../*/; do
    if [ -f "${dir}CLAUDE.md" ] && [ -d "${dir}.maestro-core" ]; then
        echo -e "  ${BLUE}→${NC} Atualizando ${dir}"
        maestro update --path "$dir"
        PROPAGATED=$((PROPAGATED + 1))
    fi
done

if [ $PROPAGATED -eq 0 ]; then
    echo -e "  Nenhum projeto encontrado. Rode ${GREEN}maestro update${NC} em cada projeto."
fi

# =============================================================================
# RESUMO
# =============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         maestro install agora é out of the box!          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  O que o ${GREEN}maestro install${NC} agora cria:"
echo ""
echo -e "  ${GREEN}✓${NC} .maestro-core/          — framework"
echo -e "  ${GREEN}✓${NC} maestro-workspace/      — diretórios de trabalho"
echo -e "  ${GREEN}✓${NC} CLAUDE.md               — skills + protocolo (versionado)"
echo -e "  ${GREEN}✓${NC} STRUCTURE.md            — convenção de pastas"
echo -e "  ${GREEN}✓${NC} maestro.config.yaml     — config comentada"
echo -e "  ${GREEN}✓${NC} {dominio}/              — estrutura completa por domínio"
echo -e "  ${GREEN}✓${NC} {dominio}/context/playbook.md — template pré-preenchido"
echo ""
echo -e "  O ${GREEN}maestro update${NC} agora também:"
echo -e "  ${GREEN}✓${NC} Cria domínios novos adicionados ao config"
echo -e "  ${GREEN}✓${NC} Regenera CLAUDE.md e STRUCTURE.md"
echo -e "  ${GREEN}✓${NC} Nunca sobrescreve playbooks ou dados existentes"
echo ""
echo -e "  Fluxo recomendado num projeto novo:"
echo -e "    ${BLUE}1.${NC} ${GREEN}maestro install${NC}"
echo -e "    ${BLUE}2.${NC} Edite ${GREEN}maestro.config.yaml${NC} com seus domínios"
echo -e "    ${BLUE}3.${NC} ${GREEN}maestro update${NC}  ← cria as pastas e playbooks"
echo -e "    ${BLUE}4.${NC} Preencha cada ${GREEN}{dominio}/context/playbook.md${NC}"
echo -e "    ${BLUE}5.${NC} ${GREEN}maestro build-team${NC}  ← gera os agentes"
echo ""
