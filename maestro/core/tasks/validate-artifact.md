---
task: validate-artifact
executor: "@validator"
executor_type: agent
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Carregue APENAS o artefato sendo validado.
# Se precisar verificar referência cruzada, carregue só o arquivo referenciado.
context_files:
  - "{artifact_path}"

entrada:
  - campo: artifact_path
    tipo: string
    obrigatorio: true
  - campo: artifact_type
    tipo: enum
    valores: [agent, task, workflow]
    obrigatorio: true

saida:
  - campo: validation_result
    tipo: object
    campos: [passed, score, issues, recommendations]

checklist:
  - "[ ] Ler apenas o artefato indicado"
  - "[ ] Verificar campos obrigatórios"
  - "[ ] Verificar referências (carregar só o referenciado se necessário)"
  - "[ ] Verificar executor != quality_gate (tasks)"
  - "[ ] Gerar relatório com score"

acceptance_criteria:
  - Score >= 7/10 para aprovar
  - Issues críticos bloqueiam
  - Nenhum arquivo carregado além do artefato e suas referências diretas
---

# validate-artifact

## Protocolo de validação lean

1. Leia o artefato — apenas ele
2. Identifique referências a outros arquivos
3. Para cada referência que precisa verificar: carregue só esse arquivo
4. Calcule o score
5. Gere o relatório
