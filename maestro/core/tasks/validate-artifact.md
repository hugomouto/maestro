---
task: validate-artifact
executor: "@validator"
executor_type: agent
quality_gate: human
context_files:
  - "{artifact_path}"

checklist:
  - "[ ] Ler apenas o artefato"
  - "[ ] context_files sem data/raw/"
  - "[ ] Referências cruzadas se necessário"
  - "[ ] Score >= 7/10"
---
# validate-artifact
1. Leia o artefato
2. context_files com data/raw/ → bloqueio imediato
3. Calcule score
4. Gere relatório
