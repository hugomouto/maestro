"""
Skill: /MAESTRO-build-team
Camada 1 → Camada 2 → Camada 3 (Ralph)
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

    # ── CAMADA 1 ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Camada 1 — Elicitação[/bold]\n")

    domain              = _choose_domain(domain, domains, config)
    operations          = _elicit_operations(domain)

    if not operations:
        console.print("[yellow]Nenhuma operação informada. Encerrando.[/yellow]")
        return

    operations_enriched = _enrich_operations(operations)
    sequences           = _elicit_sequences(operations_enriched)
    context_hints       = _elicit_context_hints(operations_enriched)
    domain_model        = _build_domain_model(domain, operations_enriched, sequences, context_hints)
    model_path          = _save_domain_model(domain, domain_model)

    console.print(f"\n[green]✓ domain-model.yaml → {model_path}[/green]")
    _show_yaml(domain_model, "Domain Model")

    if not Confirm.ask("\nContinuar para Síntese?", default=True):
        console.print("[dim]Pausado. Rode novamente para continuar.[/dim]")
        return

    # ── CAMADA 2 ──────────────────────────────────────────────────────────────
    console.print("\n[bold]Camada 2 — Síntese[/bold]\n")

    blueprint = _synthesize(domain_model)
    bp_path   = _save_blueprint(domain, blueprint)

    console.print(f"[green]✓ blueprint.yaml → {bp_path}[/green]")
    _show_yaml(blueprint, "Blueprint")

    if not auto:
        if not Confirm.ask("\nContinuar para Execução (Ralph)?", default=True):
            console.print("[dim]Rode 'maestro build-team --auto' para executar.[/dim]")
            return

    # ── CAMADA 3 ──────────────────────────────────────────────────────────────
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


def _enrich_operations(operations):
    console.print("\n[bold]Refinamento:[/bold]\n")
    enriched = []
    for op in operations:
        console.print(f"  [cyan]{op}[/cyan]")
        decision_maker = Prompt.ask("    Quem decide que está concluída?", default="gestor")
        failure        = Prompt.ask("    O que pode dar errado?",          default="dado inválido")
        console.print()
        enriched.append({
            "id":             op.lower().strip().replace(" ", "-"),
            "intent":         op,
            "decision_maker": decision_maker,
            "failure_modes":  [failure],
        })
    return enriched


def _elicit_sequences(operations):
    ids = [op["id"] for op in operations]
    console.print("[bold]Sequências obrigatórias:[/bold]")
    for i, op_id in enumerate(ids, 1):
        console.print(f"  {i}. {op_id}")

    if not Confirm.ask("\nExiste dependência de ordem?", default=False):
        return []

    console.print("[dim]Formato: 'op-a → op-b' (b depende de a). Enter para terminar.[/dim]\n")
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


def _elicit_context_hints(operations):
    """
    Pergunta ao usuário quais arquivos de contexto cada operação pode precisar.
    Esses hints viram context_files nas tasks geradas — limitando o que
    o agente pode carregar durante a execução.
    """
    console.print("\n[bold]Context Budget — arquivos de contexto por operação:[/bold]")
    console.print(
        "[dim]Para cada operação, informe caminhos de arquivos que o agente\n"
        "PODE precisar consultar. Deixe vazio se a task é auto-suficiente.\n"
        "Esses arquivos serão o TETO de contexto — o agente carrega só o necessário.[/dim]\n"
    )

    hints = {}
    for op in operations:
        console.print(f"  [cyan]{op['id']}[/cyan]")
        files = []
        while True:
            f = Prompt.ask(
                "    Arquivo de contexto (caminho relativo, ou Enter para terminar)",
                default=""
            )
            if not f:
                break
            files.append(f)
        hints[op["id"]] = files
        if files:
            console.print(f"    [dim]→ {len(files)} arquivo(s) registrado(s)[/dim]")
        console.print()

    return hints


def _build_domain_model(domain, operations, sequences, context_hints):
    EXECUTOR_RULES = {
        "aprovar":   "human",
        "autorizar": "human",
        "calcular":  "worker",
        "exportar":  "worker",
        "processar": "worker",
        "analisar":  "agent",
        "revisar":   "clone",
        "validar":   "agent",
        "gerar":     "agent",
    }

    for op in operations:
        op["executor_type"] = next(
            (v for k, v in EXECUTOR_RULES.items() if k in op["intent"].lower()),
            "agent"
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

    squads_map = {}
    for op in operations:
        dm = op.get("decision_maker", "geral")
        squads_map.setdefault(dm, []).append(op)

    squads = []
    for dm, ops in squads_map.items():
        squad_id = f"{domain}-{dm.lower().replace(' ', '-')}"
        agent_id = f"{dm.lower().replace(' ', '-')}-agent"

        squads.append({
            "id": squad_id,
            "agents": [{
                "id":           agent_id,
                "persona_base": dm,
                "commands":     [op["id"] for op in ops],
            }],
            "tasks": [{
                "id":            op["id"],
                "intent":        op["intent"],
                "executor":      op["executor_type"],
                "quality_gate":  agent_id,
                "failure_modes": op.get("failure_modes", []),
                "depends_on":    op.get("depends_on", []),
                "context_files": op.get("context_files", []),  # ← Context Budget
            } for op in ops],
            "workflows": [{
                "id":    f"fluxo-{squad_id}",
                "steps": [op["id"] for op in ops],
            }],
        })

    return {"domain": domain, "version": "0.1.0", "squads": squads}


def _save_domain_model(domain, model):
    out = Path("maestro-workspace/domain-models")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(
        yaml.dump(model, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8"
    )
    return path


def _save_blueprint(domain, blueprint):
    out = Path("maestro-workspace/blueprints")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{domain}.yaml"
    path.write_text(
        yaml.dump(blueprint, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8"
    )
    return path


def _load_config(config_path):
    p = Path(config_path)
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {}


def _show_yaml(data, title=""):
    content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(Panel(Syntax(content, "yaml", theme="monokai"), title=title, border_style="dim"))
