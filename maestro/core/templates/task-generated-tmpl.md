---
task: {{TASK_ID}}
domain: {{DOMAIN}}
agent: {{AGENT_ID}}
executor_type: {{EXECUTOR_TYPE}}
quality_gate: {{QUALITY_GATE}}
context_files:
  {{CONTEXT_FILES}}
failure_modes:
  {{FAILURE_MODES}}
depends_on:
  {{DEPENDS_ON}}
checklist:
  - "[ ] Avaliar context_files (UMA VEZ)"
  - "[ ] Executar"
  - "[ ] Registrar saída"
---
# {{TASK_ID}}
## Propósito
{{INTENT}}
