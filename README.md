# Maestro

Meta-framework auto-configurável de agentes, tasks e workflows.
Entende o domínio do usuário e gera toda a estrutura de operação a partir dele.

## Instalação

```bash
pip install git+https://github.com/SEU-USUARIO/maestro.git
```

## Uso rápido

```bash
maestro install        # instala no projeto atual
maestro skills         # lista skills disponíveis
maestro build-team     # inicia elicitação de domínio (/MAESTRO-build-team)
maestro version        # versão instalada
```

## Context Budget Protocol

Cada agente segue um protocolo de carregamento único por task:

```
1. Ler o arquivo da task
2. Raciocinar UMA VEZ sobre o que é necessário
3. Carregar apenas o necessário
4. Executar
5. Descartar — não recarregar durante a execução
```

## Arquitetura interna

```
Camada 1 — Elicitação   @intake      → domain-model.yaml
Camada 2 — Síntese      @synthesizer → blueprint.yaml
Camada 3 — Execução     Ralph loop   → agentes, tasks, workflows em arquivos
```

## Estrutura após `maestro install`

```
seu-projeto/
├── .maestro-core/
│   ├── agents/             ← intake, synthesizer, validator
│   ├── tasks/              ← elicit-domain, build-blueprint, etc.
│   ├── templates/          ← templates de geração
│   └── protocols/          ← context-budget.md
├── maestro-workspace/
│   ├── domain-models/
│   ├── blueprints/
│   └── output/
├── maestro.config.yaml
└── CLAUDE.md
```
