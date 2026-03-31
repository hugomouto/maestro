# context-budget.md

> Protocolo obrigatório para todos os agentes do Maestro

## O problema que este protocolo resolve

Sem controle, um agente tende a carregar contexto "por precaução":
carrega a pasta inteira do domínio, relê arquivos já lidos, mantém
contexto entre tasks. Isso multiplica o consumo de tokens por 5-10x
sem aumentar a qualidade do resultado.

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

## O que context_files significa

`context_files` em uma task é o **teto de permissão** — não uma obrigação.
O agente avalia quais desses arquivos são relevantes para a execução
específica e carrega apenas esses.

```yaml
# Exemplo de task com context_files
context_files:
  - ./vendas/context/playbook.md      # carregue se a operação envolve processo de venda
  - ./vendas/context/pricing.md       # carregue se a operação envolve preço
  - ./vendas/pipeline/template.md     # carregue se precisa criar um registro no pipeline
```

Se a operação não usa preço, `pricing.md` não é carregado — mesmo estando na lista.

## Task auto-suficiente

Se `context_files: []`, a task foi projetada para ser executada
apenas com as informações já contidas nela. Não carregue nada adicional.

## Convenção de estrutura de domínio

Todo domínio gerenciado pelo Maestro segue esta estrutura de pastas:

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

### Onde cada tipo de arquivo vive

| Tipo de arquivo | Pasta correta |
|-----------------|---------------|
| Regras, processos, personas | `context/` |
| Playbook do domínio | `context/playbook.md` |
| Export de API, CSV bruto | `data/raw/` |
| Resumo em markdown de dados externos | `data/processed/` |
| Tarefa em andamento | `ops/tasks/` |
| Modelo reutilizável | `ops/templates/` |
| Tarefa concluída | `ops/history/` |
| Relatório gerado | `reports/{weekly,monthly,adhoc}/` |

### Regra de nomeação

- Sempre minúsculas, hífens em vez de espaços
- Playbook: sempre `playbook.md`
- Tarefa ativa: `{descricao}-{identificador}.md`
- Template: `{nome}-template.md`
- Relatório: `relatorio-YYYY-MM.md` ou `relatorio-YYYY-WNN.md`
- Dado processado: `{fonte}-YYYY-MM.md`

### context_files padrão por tipo de task

Tasks que lêem regras do domínio:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
```

Tasks que geram documentos:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
  - ./{dominio}/ops/templates/{nome}-template.md
```

Tasks que analisam dados externos:
```yaml
context_files:
  - ./{dominio}/context/playbook.md
  - ./{dominio}/data/processed/{fonte}-{periodo}.md
```

Tasks cross-domínio (um domínio usa template de outro):
```yaml
context_files:
  - ./{dominio-executor}/context/playbook.md
  - ./{dominio-origem}/ops/templates/{nome}-template.md
```

## Impacto esperado

| Cenário | Tokens por execução |
|---------|-------------------|
| Sem protocolo (carrega tudo) | ~50-100k |
| Com Context Budget | ~5-15k |
| Redução | ~85% |
