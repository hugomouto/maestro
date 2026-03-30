---
task: elicit-domain
executor: "@intake"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Task auto-suficiente. Não carregue arquivos adicionais.
# Todo o protocolo de elicitação está descrito aqui.
context_files: []

entrada:
  - campo: domain_name
    tipo: string
    obrigatorio: true

saida:
  - campo: domain_model
    tipo: yaml
    destino: maestro-workspace/domain-models/{domain_name}.yaml

checklist:
  - "[ ] Identificar 3-7 operações principais"
  - "[ ] Mapear decision_maker por operação"
  - "[ ] Identificar failure_modes por operação"
  - "[ ] Coletar context_files por operação (teto de contexto)"
  - "[ ] Mapear sequências obrigatórias"
  - "[ ] Confirmar domain model com o usuário"

acceptance_criteria:
  - Toda operação tem id, intent e executor_type definidos
  - Toda operação tem context_files declarado (pode ser vazio)
  - Nenhuma operação foi inventada
  - Usuário confirmou antes de salvar
---

# elicit-domain

## Propósito
Extrair operações do domínio e produzir domain-model.yaml.
Inclui coleta de context_files — o teto de contexto de cada operação.

## Passos

1. Pergunte as 3-7 operações principais
2. Para cada: decision_maker, failure_mode, e arquivos que o agente
   PODE precisar consultar (context_files)
3. Mapeie sequências obrigatórias
4. Confirme e salve
