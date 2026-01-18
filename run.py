#!/usr/bin/env python3
"""
CLI Runner for YAML Multi-Agent Orchestration Engine

"""
import argparse
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import print as rprint

from app.core.yaml_parser import load_and_parse, validate_yaml
from app.core.exceptions import YAMLParseError, ValidationError
from app.engine.orchestrator import Orchestrator


console = Console()


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║     YAML Multi-Agent Orchestration Engine                     ║
║     Declarative AI Agent Workflows                            ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_workflow_diagram(config):
    """Print ASCII diagram of the workflow"""
    workflow_type = config.workflow.type

    console.print("\n[bold]Workflow Diagram:[/bold]")

    if workflow_type == "sequential":
        agents = [step.agent for step in config.workflow.steps]
        diagram = " → ".join([f"[{a}]" for a in agents])
        console.print(f"  {diagram}", style="green")

    elif workflow_type == "parallel":
        branches = config.workflow.branches
        console.print("       ┌" + "─" * 20)
        for i, branch in enumerate(branches):
            prefix = "  ├──" if i < len(branches) - 1 else "  └──"
            console.print(f"  {prefix}→ [{branch}]", style="blue")

        if config.workflow.then:
            console.print("       │")
            console.print(f"       └──→ [{config.workflow.then.agent}] (aggregator)", style="yellow")


def print_agents_table(config):
    """Print table of agents"""
    table = Table(title="Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Tools", style="magenta")

    for agent in config.agents:
        tools = ", ".join(agent.tools) if agent.tools else "-"
        table.add_row(agent.id, agent.role, agent.model, tools)

    console.print(table)


def print_execution_result(result):
    """Print execution result"""
    if result.success:
        console.print("\n[bold green]✓ Execution Successful[/bold green]")
    else:
        console.print("\n[bold red]✗ Execution Failed[/bold red]")
        if result.error:
            console.print(f"[red]Error: {result.error}[/red]")

    # Print agent outputs
    console.print("\n[bold]Agent Outputs:[/bold]")
    for agent_id, output in result.agent_outputs.items():
        console.print(Panel(
            Markdown(output),
            title=f"[cyan]{agent_id}[/cyan]",
            border_style="blue"
        ))

    # Print final output
    console.print("\n[bold]Final Output:[/bold]")
    console.print(Panel(
        Markdown(result.final_output),
        title="[green]Result[/green]",
        border_style="green"
    ))

    # Print stats
    console.print(f"\n[dim]Workflow ID: {result.workflow_id}[/dim]")
    if result.execution_time:
        console.print(f"[dim]Execution Time: {result.execution_time:.2f}s[/dim]")


def print_execution_log(result, verbose=False):
    """Print execution log"""
    if not verbose:
        return

    console.print("\n[bold]Execution Log:[/bold]")
    table = Table()
    table.add_column("Time", style="dim")
    table.add_column("Event", style="cyan")
    table.add_column("Agent", style="green")
    table.add_column("Details", style="yellow")

    for log in result.execution_log:
        time = log.get("timestamp", "")[:19]  # Trim to datetime
        event = log.get("event", "")
        agent = log.get("agent_id", "-")
        details = ""

        if "error" in log:
            details = f"[red]{log['error']}[/red]"
        elif "output_length" in log:
            details = f"{log['output_length']} chars"

        table.add_row(time, event, agent, details)

    console.print(table)


async def run_workflow(yaml_path: str, query: str, verbose: bool = False):
    """Run a workflow from YAML file"""
    try:
        # Load and parse YAML
        console.print(f"\n[bold]Loading:[/bold] {yaml_path}")
        config = load_and_parse(yaml_path)

        # Print workflow info
        print_agents_table(config)
        print_workflow_diagram(config)

        # Create orchestrator
        console.print(f"\n[bold]Workflow Type:[/bold] {config.workflow.type}")
        console.print(f"[bold]Query:[/bold] {query}")

        orchestrator = Orchestrator(config)
        console.print(f"[bold]Workflow ID:[/bold] {orchestrator.workflow_id}")

        # Execute
        console.print("\n[bold yellow]Executing workflow...[/bold yellow]\n")

        with console.status("[bold green]Running agents...") as status:
            result = await orchestrator.execute(query)

        # Print results
        print_execution_result(result)
        print_execution_log(result, verbose)

        return result.success

    except YAMLParseError as e:
        console.print(f"[red]YAML Parse Error: {e}[/red]")
        return False
    except ValidationError as e:
        console.print(f"[red]Validation Error: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return False


def validate_workflow(yaml_path: str):
    """Validate a YAML workflow file"""
    try:
        with open(yaml_path, 'r') as f:
            content = f.read()

        is_valid, errors = validate_yaml(content)

        if is_valid:
            console.print("[bold green]✓ YAML is valid[/bold green]")

            # Also show the parsed config
            config = load_and_parse(yaml_path)
            print_agents_table(config)
            print_workflow_diagram(config)
            return True
        else:
            console.print("[bold red]✗ YAML validation failed[/bold red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def start_server():
    """Start the FastAPI server"""
    import uvicorn
    console.print("[bold green]Starting API server...[/bold green]")
    console.print("API docs available at: http://localhost:8000/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="YAML Multi-Agent Orchestration Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py examples/sequential.yaml --query "Tell me about AI"
  python run.py examples/parallel.yaml --query "Design a web app" --verbose
  python run.py --validate examples/sequential.yaml
  python run.py --server
        """
    )

    parser.add_argument("yaml_file", nargs="?", help="Path to YAML workflow file")
    parser.add_argument("--query", "-q", help="Query to send to the workflow")
    parser.add_argument("--validate", "-v", action="store_true", help="Validate YAML only")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--server", "-s", action="store_true", help="Start API server")

    args = parser.parse_args()

    print_banner()

    # Start server mode
    if args.server:
        start_server()
        return

    # Validate mode
    if args.validate:
        if not args.yaml_file:
            console.print("[red]Error: YAML file required for validation[/red]")
            sys.exit(1)
        success = validate_workflow(args.yaml_file)
        sys.exit(0 if success else 1)

    # Execute mode
    if not args.yaml_file:
        parser.print_help()
        sys.exit(1)

    if not args.query:
        console.print("[red]Error: --query is required for execution[/red]")
        sys.exit(1)

    # Run the workflow
    success = asyncio.run(run_workflow(args.yaml_file, args.query, args.verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
