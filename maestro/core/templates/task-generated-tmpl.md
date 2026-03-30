---
task: {{TASK_ID}}
domain: {{DOMAIN}}
executor_type: {{EXECUTOR_TYPE}}
quality_gate: human

# ── Context Budget ────────────────────────────────────────────────────────────
# Teto de contexto: carregue apenas o necessário entre esses arquivos.
# Se a lista estiver vazia, a task é auto-suficiente.
context_files:
  {{CONTEXT_FILES}}

entrada:
  - campo: contexto
    tipo: string
    obrigatorio: true

saida:
  - campo: resultado
    tipo: object

failure_modes:
  {{FAILURE_MODES}}

depends_on:
  {{DEPENDS_ON}}

checklist:
  - "[ ] Ler task (já feito)"
  - "[ ] Avaliar context_files — carregar só o necessário (UMA VEZ)"
  - "[ ] Executar operação principal"
  - "[ ] Confirmar resultado"
  - "[ ] Registrar saída"

acceptance_criteria:
  - Resultado documentado
  - Nenhum arquivo carregado além de context_files
---

# {{TASK_ID}}

## Propósito
{{INTENT}}

## Execução

1. Avalie `context_files` — carregue apenas o necessário para esta execução
2. Execute
3. Registre e encerre
