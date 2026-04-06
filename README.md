# Maestro

Meta-framework auto-configurável de agentes, tasks e workflows.
Entende o domínio do usuário e gera toda a estrutura de operação a partir dele.

## Sobre                                                                                                

O Maestro é um framework de orquestração e automação de fluxos de trabalho (workflows) de Inteligência Artificial. Seu        
propósito é gerenciar o ciclo de vida completo de um projeto de IA, permitindo que o usuário defina, construa e execute       
habilidades de negócio específicas, chamadas Domínios.                                                                        

Em termos simples, o Maestro transforma um conjunto de requisitos de negócio em um plano de execução automatizado.            

1. Objetivo Principal                                                                                                         

Orquestrar a criação de Domínios de IA. Um Domínio é um módulo de conhecimento e funcionalidade que resolve um problema de    
negócio específico (ex: "Vendas", "Marketing").                                                                               

2. Fluxo de Trabalho (Como Funciona)                                                                                          

 1 Definição (Configuração): O usuário lista os Domínios desejados em maestro.config.yaml.                                    
 2 Construção (Skills): O módulo maestro/skills/build_team.py é usado para "construir" o domínio. Ele coleta informações      
   (elicitação), gera um modelo conceitual (domain_model.yaml) e um plano de execução (blueprint.yaml).                       
 3 Execução (Runtime): O módulo maestro/ralph/executor.py recebe o blueprint e executa as tarefas definidas, utilizando os    
   dados de contexto e os modelos de domínio para gerar artefatos finais.                                                     

3. Estrutura de Componentes Chave                                                                                             

                                                                                                                              
Componente,Arquivo / Módulo,Função
Ponto de Entrada,maestro/cli.py,"Interface de linha de comando (CLI) que expõe os comandos para gerenciar o framework (install, update, build-team)."
Configuração,maestro.config.yaml,Mapa central que lista e descreve todos os Domínios que o sistema deve gerenciar.
Motor de Skills,maestro/skills/build_team.py,"Contém a lógica de negócio para criar um domínio: orquestra a elicitação de requisitos, a síntese do modelo e a geração do blueprint."
Motor de Execução,maestro/ralph/executor.py,O motor de tempo de execução. Ele lê o blueprint e executa as tarefas definidas para produzir o resultado final do domínio.
Modelagem,maestro/core/templates/*.yaml,Define os esquemas de dados obrigatórios: o formato do Modelo de Domínio e o formato do Blueprint de Execução.
Tarefas,maestro/core/tasks/*.md,Documenta e estrutura as tarefas atômicas (funções) que serão chamadas durante a execução do fluxo de trabalho.                                
                                                                                                                              

Em resumo, o Maestro é um sistema que modela o conhecimento de negócio (Domínios) e automatiza o processo de execução desse   
conhecimento, transformando requisitos em fluxos de trabalho operacionais.       

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
