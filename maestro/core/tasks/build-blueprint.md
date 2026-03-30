---
task: build-blueprint
executor: "@synthesizer"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Carregue APENAS o domain-model.yaml do domínio sendo sintetizado.
# Não carregue outros domain-models ou arquivos do domínio.
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
  - "[ ] Inferir executor_type de cada operação"
  - "[ ] Agrupar em squads por decision_maker"
  - "[ ] Gerar um agente por squad"
  - "[ ] Gerar uma task por operação (com context_files herdado)"
  - "[ ] Gerar um workflow por squad"
  - "[ ] Verificar executor != quality_gate"
  - "[ ] Confirmar com o usuário"

acceptance_criteria:
  - Todo squad tem pelo menos 1 agente, 1 task e 1 workflow
  - Nenhuma task tem executor igual ao quality_gate
  - context_files de cada operação está preservado no blueprint
---

# build-blueprint

## Propósito
Converter domain-model.yaml em blueprint.yaml.
O context_files de cada operação é preservado no blueprint
e será inserido nas tasks geradas pelo Ralph.
