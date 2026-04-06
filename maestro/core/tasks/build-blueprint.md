---
task: build-blueprint
executor: "@synthesizer"
executor_type: agent
quality_gate: human
context_files:
  - maestro-workspace/domain-models/{domain}.yaml

checklist:
  - "[ ] Ler domain-model.yaml (única leitura)"
  - "[ ] Agrupar por agent_role"
  - "[ ] Um agente por role distinto"
  - "[ ] context_files preservados de cada operação"
  - "[ ] Nenhum context_file aponta para data/raw/"
  - "[ ] Confirmar com usuário"
---
# build-blueprint
Converter domain-model.yaml em blueprint.yaml.
agent_role → quem executa. decision_maker → quality_gate.
