---
task: elicit-domain
executor: "@intake"
executor_type: agent
quality_gate: human
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
  - "[ ] Sugerir e confirmar agent_role por operação"
  - "[ ] Mapear decision_maker por operação"
  - "[ ] Identificar failure_modes por operação"
  - "[ ] Inferir context_files pela convenção de estrutura"
  - "[ ] Mapear sequências obrigatórias"
  - "[ ] Confirmar domain model com o usuário"

acceptance_criteria:
  - Toda operação tem agent_role definido
  - Toda operação tem context_files (pode ser vazio)
  - Nenhum context_file aponta para data/raw/
  - Usuário confirmou antes de salvar
---

# elicit-domain

## Propósito
Extrair operações do domínio e produzir domain-model.yaml com múltiplos
agentes especializados via agent_role.

## Passos

1. Perguntar nome e descrição do domínio
2. Listar 3–7 operações principais
3. Para cada operação:
   - Sugerir agent_role inferido do intent — usuário confirma ou renomeia
   - Quem aprova? (decision_maker → vira quality_gate)
   - O que pode dar errado? (failure_mode)
   - Inferir context_files pela convenção:
     - sempre: `{dominio}/context/playbook.md`
     - se gera documento: `{dominio}/ops/templates/`
     - se consome dados externos: `{dominio}/data/processed/`
4. Mapear sequências obrigatórias
5. Confirmar e salvar

## Nota
O Ralph criará automaticamente a estrutura de pastas do domínio
(context/, data/, ops/, reports/ e subpastas) durante a execução.
