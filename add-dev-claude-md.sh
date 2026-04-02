#!/usr/bin/env bash
# =============================================================================
# add-dev-claude-md.sh
# Cria o CLAUDE.md de desenvolvimento na raiz do repositório maestro/.
# Este arquivo é para quem desenvolve o Maestro — não para projetos que o usam.
# Uso: bash add-dev-claude-md.sh (na raiz do repositório maestro/)
# =============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()      { echo -e "${GREEN}✓${NC} $1"; }
section() { echo -e "\n${CYAN}── $1 ──${NC}"; }

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   M A E S T R O  —  Dev CLAUDE.md    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "pyproject.toml" ] || [ ! -d "maestro" ]; then
    echo "ERRO: rode na raiz do repositório maestro/"
    exit 1
fi

section "Criando CLAUDE.md de desenvolvimento"

cat > CLAUDE.md << 'CLAUDEMD'
# CLAUDE.md — Maestro (repositório de desenvolvimento)

Este é o repositório do **framework Maestro** — não um projeto que usa o Maestro.
Aqui você desenvolve, testa e publica o pacote.

---

## O que é este repositório

Maestro é um meta-framework Python auto-configurável que:
1. Elicita domínios de negócio via CLI interativo
2. Gera automaticamente agentes especializados, tasks e workflows
3. Cria a estrutura de pastas de cada domínio (`context/`, `data/`, `ops/`, `reports/`)
4. Instala um `CLAUDE.md` versionado nos projetos que o usam

---

## Estrutura do pacote

```
maestro/
├── __init__.py              ← versão do pacote
├── cli.py                   ← comandos CLI (maestro install, update, skills, build-team)
├── installer.py             ← lógica de install/update + geração do CLAUDE.md nos projetos
├── skills/
│   └── build_team.py        ← skill /MAESTRO-build-team (elicitação → síntese → Ralph)
├── ralph/
│   └── executor.py          ← loop de geração de artefatos + scaffold de domínio
└── core/                    ← copiado para .maestro-core/ nos projetos instalados
    ├── agents/              ← intake.md, synthesizer.md, validator.md
    ├── tasks/               ← elicit-domain.md, build-blueprint.md, etc.
    ├── templates/           ← domain-model-tmpl.yaml, blueprint-tmpl.yaml, etc.
    └── protocols/           ← context-budget.md
```

---

## Como desenvolver

### Instalar em modo editable (primeira vez)

```bash
pip install -e . --break-system-packages
# ou com venv:
python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

### Testar localmente

```bash
maestro version
maestro skills
maestro build-team
```

### Rodar os testes

```bash
python -m pytest tests/ -v
```

### Scripts de manutenção disponíveis

| Script | O que faz |
|--------|-----------|
| `bash update-maestro.sh` | Aplica todas as atualizações do framework (skills, ralph, core) |
| `bash fix-maestro-installer.sh` | Corrige o installer.py e propaga CLAUDE.md para projetos |
| `bash add-dev-claude-md.sh` | Recria este arquivo |

---

## Arquivos que NÃO devem ser editados manualmente

- `maestro/core/**` — edite via script ou prompt, nunca direto
- `maestro-workspace/` — gerado em runtime, ignorado pelo git

---

## Como adicionar uma nova skill

1. Crie `maestro/skills/{nome_skill}.py` com uma função `run()`
2. Registre no `SKILLS` list em `maestro/cli.py`
3. Adicione a linha na tabela de `FRAMEWORK_BLOCK` em `maestro/installer.py`
4. Rode `bash update-maestro.sh` para reinstalar
5. Nos projetos instalados: `maestro update` propaga automaticamente

---

## Como publicar uma nova versão

```bash
# 1. Atualizar versão em maestro/__init__.py e pyproject.toml
# 2. Commitar tudo
git add . && git commit -m "feat: descrição da mudança"
git push origin main

# 3. Nos projetos que usam o Maestro:
pip install --upgrade git+https://github.com/hugomouto/maestro.git
maestro update
```

---

## Fluxo interno do /MAESTRO-build-team

```
Usuário descreve operações
        ↓
build_team.py — _elicit_operations()
        ↓  pergunta agent_role (sugerido), decision_maker, failure_mode
build_team.py — _infer_context_files()
        ↓  infere context_files pela convenção de estrutura
build_team.py — _build_domain_model()
        ↓  salva domain-model.yaml
build_team.py — _synthesize()
        ↓  agrupa por agent_role → um agente por especialidade
        ↓  salva blueprint.yaml
ralph/executor.py — run()
        ↓  _scaffold_domain() → cria context/, data/, ops/, reports/
        ↓  _scaffold_structure_md() → cria STRUCTURE.md na raiz
        ↓  gera agents/*.md, tasks/*.md, workflows/*.yaml
```

---

## Convenção de estrutura de domínio (o que o Maestro gera nos projetos)

```
{dominio}/
├── context/         ← regras permanentes — sempre context/playbook.md
├── data/
│   ├── raw/         ← dados brutos — NUNCA leia em context_files
│   ├── processed/   ← dados transformados — leia aqui
│   └── snapshots/   ← comparação histórica
├── ops/
│   ├── tasks/       ← trabalho em aberto
│   ├── templates/   ← modelos reutilizáveis
│   └── history/     ← concluídos
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

---

## Context Budget Protocol

Todo agente gerado pelo Maestro segue:

```
1. Ler APENAS o arquivo da task
2. Decidir UMA VEZ quais context_files carregar
3. Carregar apenas o necessário
4. Executar
5. Encerrar — não recarregar
```

`data/raw/` nunca entra em `context_files`. O validator bloqueia se entrar.
CLAUDEMD

ok "CLAUDE.md criado"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              CLAUDE.md de desenvolvimento criado!        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Agora ao abrir o Claude Code neste repositório,"
echo -e "  ele vai entender que está no framework Maestro"
echo -e "  e terá contexto para ajudar no desenvolvimento."
echo ""
