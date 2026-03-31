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
  - "[ ] Identificar nome e descrição do domínio"
  - "[ ] Identificar 3-7 operações principais"
  - "[ ] Mapear decision_maker por operação"
  - "[ ] Identificar failure_modes por operação"
  - "[ ] Inferir context_files usando convenção de pastas"
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

1. Pergunte o nome do domínio e uma descrição de 1 linha do que ele faz
2. Liste as 3–7 operações principais do domínio
3. Para cada operação:
   - Quem decide que está concluída? (decision_maker)
   - O que pode dar errado? (failure_mode)
   - Infira context_files usando a convenção:
     - Se a operação usa regras/processo → `{dominio}/context/playbook.md`
     - Se a operação gera um documento → `{dominio}/ops/templates/{nome}-template.md`
     - Se a operação consome dados externos → `{dominio}/data/processed/{fonte}.md`
     - Se a operação cruza domínios → inclua o caminho do domínio de origem
4. Mapeie sequências obrigatórias
5. Confirme o domain-model.yaml com o usuário antes de salvar

## Nota sobre estrutura física

O Maestro criará automaticamente a estrutura de pastas
(context/, data/, ops/, reports/ e subpastas) para cada domínio
durante a execução do Ralph. O intake não precisa perguntar sobre isso.
