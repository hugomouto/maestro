# CLAUDE.md — Maestro (repositório do framework)

<!-- MAESTRO:framework -->
<!-- Bloco gerenciado pelo Maestro. Regenerado em todo install/update. -->

## Skills disponíveis

| Skill | Comando CLI | O que faz |
|-------|-------------|-----------|
| /MAESTRO-build-team | `maestro build-team` | Elicita domínio, gera agentes especializados por role, cria estrutura de pastas |

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
maestro install       # instala e inicializa o projeto completo
maestro update        # atualiza framework + cria domínios novos do config
maestro build-team    # elicita domínio e gera agentes
maestro skills        # lista skills
maestro version       # versão instalada
```
<!-- /MAESTRO:framework -->

---

## Este repositório (desenvolvimento do framework)

Este é o **repositório do framework Maestro** — não um projeto que o usa.

### Estrutura do pacote

```
maestro/
├── __init__.py          ← versão
├── cli.py               ← comandos CLI
├── installer.py         ← install/update + geração de CLAUDE.md nos projetos
├── skills/
│   └── build_team.py    ← skill /MAESTRO-build-team
├── ralph/
│   └── executor.py      ← geração de artefatos + scaffold de domínio
└── core/                ← copiado para .maestro-core/ nos projetos
    ├── agents/
    ├── tasks/
    ├── templates/
    └── protocols/
```

### Como adicionar uma nova skill

1. Crie `maestro/skills/{nome}.py` com função `run()`
2. Adicione entrada em `SKILLS` no `cli.py`
3. Adicione linha na tabela de `FRAMEWORK_BLOCK` no `installer.py`
4. Rode `bash setup-maestro-v2.sh` para reinstalar
5. Nos projetos: `maestro update` propaga automaticamente

### Publicar nova versão

```bash
git add . && git commit -m "feat: descrição"
git push origin main
# nos projetos:
pip install --upgrade git+https://github.com/hugomouto/maestro.git
maestro update
```
