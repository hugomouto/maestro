# context-budget.md
> Protocolo obrigatório para todos os agentes do Maestro

## Protocolo
```
PASSO 1  Ler o arquivo da task — e apenas ele
PASSO 2  Raciocinar UMA VEZ sobre quais context_files são necessários
PASSO 3  Carregar apenas os identificados no Passo 2
PASSO 4  Executar do início ao fim
PASSO 5  Encerrar — não recarregar nada
```

## Regras
- context_files é o teto — nunca carregue mais do que o declarado
- data/raw/ NUNCA entra em context_files
- Um arquivo lido não é lido novamente na mesma execução
- Sem cross-domain sem necessidade explícita na task

## Convenção de estrutura
```
{dominio}/
├── context/playbook.md  ← sempre o primeiro context_file
├── data/raw/            ← NUNCA carregar
├── data/processed/      ← carregar quando precisar de dados externos
├── ops/tasks/           ← a task em si
├── ops/templates/       ← carregar ao gerar documentos
├── ops/history/         ← carregar só com histórico explícito
└── reports/             ← onde os agentes escrevem saídas
```
