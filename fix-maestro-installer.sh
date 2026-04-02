#!/usr/bin/env bash
# =============================================================================
# fix-maestro-installer.sh — versão corrigida para ambientes Debian/Ubuntu
# Detecta automaticamente o venv ativo ou usa --break-system-packages
# Corrige o installer.py para que:
#   1. CLAUDE.md use seções delimitadas — framework sempre atualiza, usuário preserva
#   2. maestro update regenera as seções do framework no CLAUDE.md existente
#   3. Skills aparecem automaticamente no Claude Code sem configuração manual
# Uso: bash fix-maestro-installer.sh (na raiz do repositório maestro/)
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
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   M A E S T R O  —  Fix Installer    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "pyproject.toml" ] || [ ! -d "maestro" ]; then
    echo "ERRO: rode na raiz do repositório maestro/"
    exit 1
fi

# =============================================================================
# Detecta qual pip usar
# =============================================================================
section "Detectando ambiente Python"

PIP_CMD=""
EXTRA_FLAGS=""

# 1. venv ativo?
if [ -n "$VIRTUAL_ENV" ]; then
    PIP_CMD="$VIRTUAL_ENV/bin/pip"
    ok "venv ativo: $VIRTUAL_ENV"

# 2. pipx?
elif command -v pipx &>/dev/null && pipx list 2>/dev/null | grep -q maestro; then
    echo -e "  ${BLUE}→${NC} Maestro instalado via pipx — reinstalando"
    pipx install -e . --force 2>/dev/null || pipx reinstall maestro
    ok "pipx reinstalado"
    PIP_CMD="SKIP"

# 3. Debian/Ubuntu: --break-system-packages
else
    warn "Sem venv ativo. Usando --break-system-packages (Debian/Ubuntu)"
    PIP_CMD="pip"
    EXTRA_FLAGS="--break-system-packages"
fi

# =============================================================================
# SEÇÃO 1 — installer.py corrigido
# =============================================================================
section "maestro/installer.py"

cat > maestro/installer.py << 'INSTALLER'
"""
Maestro Installer
-----------------
Separa o CLAUDE.md em duas camadas:

  Camada FRAMEWORK (<!-- MAESTRO:framework --> ... <!-- /MAESTRO:framework -->)
    Gerada e atualizada pelo Maestro em todo install/update.
    Contém: skills, agentes, protocolo, comandos CLI, convenção de estrutura.

  Camada USER (fora dos blocos MAESTRO)
    Escrita uma única vez no install. Nunca sobrescrita.
    Contém: configuração do projeto, domínios, notas do usuário.

Ao rodar `maestro update`, apenas o bloco FRAMEWORK é substituído.
O restante do arquivo é preservado intacto.
"""
import re
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

FRAMEWORK_DIR = ".maestro-core"
USER_DIR      = "maestro-workspace"
CONFIG_FILE   = "maestro.config.yaml"

BLOCK_START = "<!-- MAESTRO:framework -->"
BLOCK_END   = "<!-- /MAESTRO:framework -->"

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

Agentes ficam em `.maestro-core/agents/` após `maestro install`.

---

## Estrutura de domínio — convenção obrigatória

Todo domínio segue esta estrutura. Consulte `STRUCTURE.md` para referência completa.

```
{dominio}/
├── context/         ← regras permanentes — leia context/playbook.md
├── data/
│   ├── raw/         ← NUNCA leia diretamente
│   ├── processed/   ← leia aqui dados externos
│   └── snapshots/   ← comparação histórica
├── ops/
│   ├── tasks/       ← trabalho em aberto
│   ├── templates/   ← modelos reutilizáveis
│   └── history/     ← concluídos e encerrados
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
maestro install        # instala no projeto atual
maestro update         # atualiza framework (preserva workspace e config)
maestro skills         # lista skills disponíveis
maestro build-team     # inicia elicitação de domínio
maestro version        # versão instalada
```
<!-- /MAESTRO:framework -->"""

USER_SECTION = """\
## Este projeto

<!-- Descreva aqui o projeto, domínios e configurações específicas -->
<!-- Esta seção NÃO é atualizada pelo Maestro — edite livremente -->

| Item | Caminho |
|------|---------|
| Config | maestro.config.yaml |
| Framework | .maestro-core/ |
| Workspace | maestro-workspace/ |
| Referência de estrutura | STRUCTURE.md |
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
    _install_claude_md(root)
    console.print("\n[green]✓ Maestro instalado.[/green]")
    console.print("  Edite [bold]maestro.config.yaml[/bold] com seus domínios.")
    console.print()


def update(target_path: str = "."):
    root = Path(target_path).resolve()
    console.print(f"\n[bold]Atualizando Maestro em:[/bold] {root}\n")
    _copy_framework(root)
    _update_claude_md(root)
    console.print("\n[green]✓ .maestro-core/ atualizado.[/green]")
    console.print("  Workspace e config preservados.")
    console.print()


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
        console.print(f"  [blue]→[/blue] CLAUDE.md atualizado (bloco framework regenerado)")
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
# SEÇÃO 2 — reinstala usando o pip correto
# =============================================================================
section "Reinstalando pacote"

if [ "$PIP_CMD" = "SKIP" ]; then
    ok "pipx já reinstalou — pulando pip"
elif [ -n "$PIP_CMD" ]; then
    if $PIP_CMD install -e . -q $EXTRA_FLAGS; then
        ok "pacote reinstalado com sucesso"
    else
        warn "Falhou. Tente manualmente uma das opções:"
        echo "  # Se tiver venv:"
        echo "  source .venv/bin/activate && pip install -e ."
        echo "  # Sem venv (Debian):"
        echo "  pip install -e . --break-system-packages"
        exit 1
    fi
fi

# =============================================================================
# SEÇÃO 3 — propaga para projetos instalados no diretório pai
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
    echo -e "  Nenhum projeto com Maestro instalado encontrado no diretório pai."
    echo -e "  Rode ${GREEN}maestro update${NC} dentro de cada projeto para propagar."
fi

# =============================================================================
# RESUMO
# =============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Installer corrigido!                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} CLAUDE.md com bloco <!-- MAESTRO:framework --> versionado"
echo -e "  ${GREEN}✓${NC} maestro update regenera skills automaticamente"
echo -e "  ${GREEN}✓${NC} Seção do usuário preservada em todo update"
echo ""
echo -e "  Para propagar ao ERP agora:"
echo -e "    ${GREEN}cd ../seu-erp && maestro update${NC}"
echo ""
