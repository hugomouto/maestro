# context-budget.md

> Protocolo obrigatório para todos os agentes do Maestro

## O problema que este protocolo resolve

Sem controle, um agente tende a carregar contexto "por precaução":
carrega a pasta inteira do domínio, relê arquivos já lidos, acessa
dados brutos diretamente. Isso multiplica o consumo de tokens por 5-10x.

## O protocolo

```
PASSO 1  Ler o arquivo da task — e apenas ele
PASSO 2  Raciocinar UMA VEZ: "quais arquivos em context_files
         são realmente necessários para ESTA execução?"
PASSO 3  Carregar apenas os arquivos identificados no Passo 2
PASSO 4  Executar a task do início ao fim
PASSO 5  Encerrar — não recarregar nada
```

## Regras

| Regra | Descrição |
|-------|-----------|
| Task-first | A task é lida primeiro, sempre |
| Decisão única | O raciocínio sobre contexto acontece uma única vez |
| Teto declarado | O agente nunca carrega mais do que `context_files` da task |
| Sem recarregamento | Um arquivo lido não é lido novamente na mesma execução |
| Sem cross-domain | Arquivos de outros domínios só com necessidade explícita na task |

## Convenção de estrutura de domínio

Todo domínio gerenciado pelo Maestro segue esta estrutura:

```
{dominio}/
├── context/          ← identidade e regras permanentes
├── data/
│   ├── raw/          ← dados brutos (NUNCA carregar diretamente)
│   ├── processed/    ← dados prontos para leitura por agentes
│   └── snapshots/    ← cópias pontuais de estado
├── ops/
│   ├── tasks/        ← trabalho em aberto
│   ├── templates/    ← modelos reutilizáveis
│   └── history/      ← tarefas concluídas
└── reports/
    ├── weekly/
    ├── monthly/
    └── adhoc/
```

### Prioridade de carregamento (do menor para o maior custo)

```
ops/tasks/{arquivo}.md          ← sempre (é a task em si)
context/playbook.md             ← quase sempre
ops/templates/{template}.md     ← quando a task gera um documento
data/processed/{arquivo}.md     ← quando a task precisa de dados externos
reports/                        ← raramente, só com histórico explícito
data/raw/                       ← NUNCA diretamente
ops/history/                    ← só quando a task pede histórico explícito
```

### context_files padrão por tipo de task

Task que usa regras do domínio:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
```

Task que gera documento:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
  - ./{dominio}/ops/templates/{nome}-template.md
```

Task que analisa dados externos:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
  - ./{dominio}/data/processed/{fonte}-{periodo}.md
```

## Impacto esperado

| Cenário | Tokens por execução |
|---------|-------------------|
| Sem protocolo (carrega tudo) | ~50-100k |
| Com Context Budget | ~5-15k |
| Redução | ~85% |
