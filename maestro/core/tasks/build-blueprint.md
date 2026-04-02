---
task: build-blueprint
executor: "@synthesizer"
executor_type: agent
quality_gate: human
context_files:
  - maestro-workspace/domain-models/{domain}.yaml

entrada:
  - campo: domain_model_path
    tipo: string
    obrigatorio: true

saida:
  - campo: blueprint
    tipo: yaml
    destino: maestro-workspace/blueprints/{domain}.yaml

checklist:
  - "[ ] Ler domain-model.yaml (única leitura)"
  - "[ ] Agrupar operações por agent_role"
  - "[ ] Gerar um agente por agent_role distinto"
  - "[ ] Gerar uma task por operação (com context_files herdado)"
  - "[ ] Verificar que nenhum context_file aponta para data/raw/"
  - "[ ] Verificar context/playbook.md é o primeiro context_file"
  - "[ ] Gerar um workflow por agente"
  - "[ ] Confirmar com o usuário"

acceptance_criteria:
  - Todo agente tem agent_role distinto
  - Nenhuma task tem agent igual ao quality_gate
  - context_files de cada operação está preservado
---

# build-blueprint

## Propósito
Converter domain-model.yaml em blueprint.yaml com múltiplos agentes
especializados. Agrupamento por agent_role — não por decision_maker.

## Regra central
agent_role → quem executa → determina o agente gerado
decision_maker → quem aprova → vira quality_gate da task
