---
task: infer-executor
executor: "@synthesizer"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Task auto-suficiente. As regras de inferência estão aqui.
context_files: []

entrada:
  - campo: operation
    tipo: object
    obrigatorio: true

saida:
  - campo: executor_type
    tipo: enum
    valores: [agent, worker, clone, human]

checklist:
  - "[ ] Verificar palavras-chave do intent"
  - "[ ] Verificar decision_maker"
  - "[ ] Aplicar fallback (agent) se inconclusivo"
  - "[ ] Registrar justificativa"

acceptance_criteria:
  - executor_type é um dos 4 valores válidos
  - Justificativa registrada
---

# infer-executor

## Regras (aplicar em ordem)

1. decision_maker humano + critério subjetivo → `human`
2. Intent: calcular, exportar, transformar, processar → `worker`
3. Requer metodologia específica de domínio → `clone`
4. Default → `agent`
