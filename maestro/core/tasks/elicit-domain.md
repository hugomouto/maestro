---
task: elicit-domain
executor: "@intake"
executor_type: agent
quality_gate: human
context_files: []

checklist:
  - "[ ] Nome e descrição do domínio"
  - "[ ] 3-7 operações principais"
  - "[ ] agent_role sugerido e confirmado por operação"
  - "[ ] decision_maker por operação"
  - "[ ] failure_modes por operação"
  - "[ ] context_files inferidos pela convenção"
  - "[ ] Sequências obrigatórias"
  - "[ ] Confirmação do usuário"

acceptance_criteria:
  - Toda operação tem agent_role
  - Nenhum context_file aponta para data/raw/
  - Usuário confirmou antes de salvar
---
# elicit-domain
Extrair operações e produzir domain-model.yaml com múltiplos agentes especializados.
