"""
Skill: /MAESTRO-build-team
Elicitação → Síntese → Execução (Ralph)
Gera múltiplos agentes especializados por agent_role.
"""
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax
import yaml

console = Console()


def run(domain=None, config_path="maestro.config.yaml", auto=False):
    console.print(Panel.fit(
        "[bold cyan]/MAESTRO-build-team[/bold cyan]\n"
        "[dim]Elicitação → Síntese → Execução[/dim]",
        border_style="cyan"
    ))

    config  = _load_config(config_path)
    domains = list(config.get("domain_map", {}).keys())

    console.print("\n[bold]Camada 1 — Elicitação[/bold]\n")
    domain              = _choose_domain(domain, domains, config)
    operations          = _elicit_operations(domain)
    if not operations:
        console.print("[yellow]Nenhuma operação informada. Encerrando.[/yellow]")
        return
    operations_enriched = _enrich_operations(operations, domain)
    sequences           = _elicit_sequences(operations_enriched)
    context_hints       = _infer_context_files(operations_enriched, domain)
    domain_model        = _build_domain_model(domain, operations_enriched, sequences, context_hints)
    model_path          = _save_domain_model(domain, domain_model)
    console.print(f"\n[green]✓ domain-model.yaml → {model_path}[/green]")
    _show_yaml(domain_model, "Domain Model")

    if not Confirm.ask("\nContinuar para Síntese?", default=True):
        console.print("[dim]Pausado.[/dim]")
        return

    console.print("\n[bold]Camada 2 — Síntese[/bold]\n")
    blueprint = _synthesize(domain_model)
    bp_path   = _save_blueprint(domain, blueprint)
    console.print(f"[green]✓ blueprint.yaml → {bp_path}[/green]")
    _show_yaml(blueprint, "Blueprint")

    if not auto:
        if not Confirm.ask("\nContinuar para Execução (Ralph)?", default=True):
            return

    console.print("\n[bold]Camada 3 — Execução[/bold]\n")
    from maestro.ralph.executor import run as ralph_run
    ralph_run(str(bp_path))
    console.print(f"\n[green]✓ Artefatos → maestro-workspace/output/{domain}/[/green]\n")


def _choose_domain(domain, domains, config):
    if domain:
        return domain
    if domains:
        console.print("[bold]Domínios mapeados:[/bold]")
        for i, d in enumerate(domains, 1):
            desc = config["domain_map"][d].get("description", "")
            console.print(f"  [green]{i}.[/green] {d}  [dim]{desc}[/dim]")
        console.print()
        choice = Prompt.ask("Qual domínio? (número, nome ou 'novo')", default="novo")
        if choice.isdigit() and 1 <= int(choice) <= len(domains):
            return domains[int(choice) - 1]
        if choice in domains:
            return choice
    return Prompt.ask("Nome do domínio (ex: vendas, operacao)")


def _elicit_operations(domain):
    console.print(f"[bold]Domínio:[/bold] [cyan]{domain}[/cyan]\n")
    console.print("Liste as operações principais. Mínimo 3, máximo 7.\n")
    operations = []
    i = 1
    while len(operations) < 7:
        suffix = " (mínimo)" if i <= 3 else " (ou Enter para terminar)"
        op = Prompt.ask(f"  Operação {i}{suffix}", default="")
        if not op:
            if len(operations) < 3:
                console.print(f"  [yellow]Informe mais {3 - len(operations)} operação(ões).[/yellow]")
                continue
            break
        operations.append(op)
        i += 1
    return operations


def _infer_agent_role(intent: str, domain: str) -> str:
    intent_lower = intent.lower()
    ROLE_RULES = [
        (["pesquis", "mercado", "concorrên", "benchm", "research"],   "researcher"),
        (["estratég", "planejam", "campanha", "calendár", "strategy"], "strategist"),
        (["dado", "métric", "analís", "relatór", "performance",
          "orgânic", "pago", "tráfego"],                               "data-analyst"),
        (["conteúd", "post", "copy", "texto", "redaç"],                "content-producer"),
        (["instagram", "reels", "stories", "feed"],                    "instagram-agent"),
        (["linkedin", "artigo", "newsletter"],                         "linkedin-agent"),
        (["vend", "proposta", "lead", "prospect", "crm"],              "sales-agent"),
        (["financ", "orçam", "custo", "budget", "dre"],                "finance-agent"),
        (["operas", "process", "fornec", "estoque", "logíst"],         "ops-agent"),
        (["produto", "roadmap", "feature", "sprint", "backlog"],       "product-agent"),
        (["aprova", "autoriz", "valid", "revis", "qualid"],            "reviewer"),
        (["export", "import", "integr", "sincron"],                    "data-worker"),
    ]
    for keywords, role in ROLE_RULES:
        if any(kw in intent_lower for kw in keywords):
            return role
    first_word = intent_lower.strip().split()[0] if intent_lower.strip() else domain
    return f"{first_word[:20].replace(' ', '-')}-agent"


def _enrich_operations(operations, domain):
    console.print("\n[bold]Refinamento:[/bold]\n")
    enriched = []
    for op in operations:
        console.print(f"  [cyan]{op}[/cyan]")
        suggested_role = _infer_agent_role(op, domain)
        console.print(f"    [dim]Agente sugerido: {suggested_role}[/dim]")
        agent_role = Prompt.ask(
            "    Agente que executa (confirme ou renomeie)",
            default=suggested_role
        )
        decision_maker = Prompt.ask(
            "    Quem aprova/decide que está concluída?",
            default="gestor"
        )
        failure = Prompt.ask("    O que pode dar errado?", default="dado inválido")
        console.print()
        enriched.append({
            "id":             op.lower().strip().replace(" ", "-"),
            "intent":         op,
            "agent_role":     agent_role.lower().strip().replace(" ", "-"),
            "decision_maker": decision_maker,
            "failure_modes":  [failure],
        })
    return enriched


def _infer_context_files(operations, domain):
    hints = {}
    for op in operations:
        intent_lower = op["intent"].lower()
        files = [f"./{domain}/context/playbook.md"]
        if any(kw in intent_lower for kw in ["criar", "gerar", "redigir", "produzir", "escrever", "montar"]):
            files.append(f"./{domain}/ops/templates/")
        if any(kw in intent_lower for kw in ["analís", "métric", "dado", "relatór", "performance", "resultado"]):
            files.append(f"./{domain}/data/processed/")
        if any(kw in intent_lower for kw in ["históric", "anterior", "comparar", "evolução"]):
            files.append(f"./{domain}/data/snapshots/")
        hints[op["id"]] = files
    return hints


def _elicit_sequences(operations):
    ids = [op["id"] for op in operations]
    console.print("[bold]Sequências obrigatórias:[/bold]")
    for i, op_id in enumerate(ids, 1):
        console.print(f"  {i}. {op_id}")
    if not Confirm.ask("\nExiste dependência de ordem?", default=False):
        return []
    console.print("[dim]Formato: 'op-a → op-b'. Enter para terminar.[/dim]\n")
    sequences = []
    while True:
        pair = Prompt.ask("  Dependência", default="")
        if not pair:
            break
        if "→" in pair:
            parts = [p.strip() for p in pair.split("→")]
            if len(parts) == 2:
                sequences.append(parts)
    return sequences


def _build_domain_model(domain, operations, sequences, context_hints):
    EXECUTOR_RULES = {
        "aprovar": "human", "autorizar": "human",
        "calcular": "worker", "exportar": "worker",
        "processar": "worker", "sincroniz": "worker",
        "analisar": "agent", "revisar": "clone",
        "validar": "agent", "gerar": "agent",
    }
    for op in operations:
        op["executor_type"] = next(
            (v for k, v in EXECUTOR_RULES.items() if k in op["intent"].lower()), "agent"
        )
        op["depends_on"]    = []
        op["context_files"] = context_hints.get(op["id"], [])
    for pair in sequences:
        for op in operations:
            if op["id"] == pair[1]:
                op["depends_on"].append(pair[0])
    return {"domain": domain, "operations": operations, "sequences": sequences}


def _synthesize(domain_model):
    domain     = domain_model["domain"]
    operations = domain_model["operations"]
    agents_map = {}
    for op in operations:
        role = op.get("agent_role") or op.get("decision_maker", "geral")
        agents_map.setdefault(role, []).append(op)

    squad_id  = f"{domain}-squad"
    agents, tasks, workflows = [], [], []

    for role, ops in agents_map.items():
        agent_id = role if role.endswith("-agent") else f"{role}-agent"
        agents.append({"id": agent_id, "persona_base": role, "commands": [op["id"] for op in ops]})
        for op in ops:
            tasks.append({
                "id": op["id"], "intent": op["intent"],
                "executor": op["executor_type"], "agent": agent_id,
                "quality_gate": op.get("decision_maker", "gestor"),
                "failure_modes": op.get("failure_modes", ["falha genérica"]),
                "depends_on": op.get("depends_on", []),
                "context_files": op.get("context_files", []),
            })
        workflows.append({"id": f"fluxo-{agent_id}", "agent": agent_id, "steps": [op["id"] for op in ops]})

    return {"domain": domain, "version": "0.2.0", "squads": [{"id": squad_id, "agents": agents, "tasks": tasks, "workflows": workflows}]}


def _save_domain_model(domain, model):
    out = Path("maestro-workspace/domain-models")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(yaml.dump(model, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return path


def _save_blueprint(domain, blueprint):
    out = Path("maestro-workspace/blueprints")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(yaml.dump(blueprint, allow_unicode=True, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return path


def _load_config(config_path):
    p = Path(config_path)
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {} if p.exists() else {}


def _show_yaml(data, title=""):
    content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(Panel(Syntax(content, "yaml", theme="monokai"), title=title, border_style="dim"))
