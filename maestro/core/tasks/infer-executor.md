---
task: infer-executor
executor: "@synthesizer"
executor_type: agent
quality_gate: human
context_files: []
---
# infer-executor
## Regras
1. decision_maker humano + critério subjetivo → `human`
2. calcular, exportar, processar, sincronizar → `worker`
3. Metodologia específica → `clone`
4. Default → `agent`
