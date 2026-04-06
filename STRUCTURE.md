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
