---
task: validate-artifact
executor: "@validator"
executor_type: agent
quality_gate: human
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
  - "[ ] Verificar que context_files não aponta para data/raw/"
  - "[ ] Verificar referências (carregar só o referenciado se necessário)"
  - "[ ] Verificar agent != quality_gate (tasks)"
  - "[ ] Gerar relatório com score"

acceptance_criteria:
  - Score >= 7/10 para aprovar
  - context_files apontando para data/raw/ bloqueia imediatamente
  - Nenhum arquivo carregado além do artefato e suas referências diretas
---

# validate-artifact

## Protocolo

1. Leia o artefato — apenas ele
2. Verifique se context_files tem data/raw/ → bloqueia se sim
3. Identifique referências a outros arquivos
4. Para cada referência que precisa verificar: carregue só esse arquivo
5. Calcule o score
6. Gere o relatório
