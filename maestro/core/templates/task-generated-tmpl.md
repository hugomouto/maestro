---
task: {{TASK_ID}}
domain: {{DOMAIN}}
agent: {{AGENT_ID}}
executor_type: {{EXECUTOR_TYPE}}
quality_gate: {{QUALITY_GATE}}

# ── Context Budget ────────────────────────────────────────────────────────────
# Teto de contexto — carregue apenas o necessário, uma única vez.
# NUNCA carregue data/raw/ diretamente.
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
  - "[ ] Ler task (feito)"
  - "[ ] Avaliar context_files — carregar só o necessário (UMA VEZ)"
  - "[ ] Executar operação principal"
  - "[ ] Registrar saída"

acceptance_criteria:
  - Resultado documentado
  - Nenhum arquivo carregado além de context_files
---

# {{TASK_ID}}

## Propósito
{{INTENT}}

## Execução

1. Avalie `context_files` — carregue apenas o necessário
2. Execute conforme `{{DOMAIN}}/context/playbook.md`
3. Registre e encerre
