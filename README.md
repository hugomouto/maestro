# Maestro

Meta-framework auto-configurável de agentes, tasks e workflows.
Entende o domínio do usuário e gera toda a estrutura de operação a partir dele.

## Dependências

- Python 3.10+
- [Claude Code](https://claude.ai/code) instalado e autenticado (`claude` disponível no terminal)
- `pip` (gerenciador de pacotes Python)
- Git

## Instalação

### Em qualquer máquina (instalação global)

Instala o CLI `maestro` globalmente, disponível em qualquer projeto:

```bash
pip install git+https://github.com/hugomouto/maestro.git
```

### Num projeto específico

Após a instalação global, entre na pasta do projeto e rode:

```bash
cd meu-projeto
maestro install
```

Isso cria a estrutura `.maestro-core/`, `maestro-workspace/`, `maestro.config.yaml` e `CLAUDE.md` no projeto atual.

## Atualização

Para atualizar para a versão mais recente do repositório:

```bash
pip install --upgrade git+https://github.com/hugomouto/maestro.git
```

Após atualizar o pacote, rode novamente `maestro install` dentro de projetos existentes caso queira atualizar os arquivos de core gerados localmente.

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
