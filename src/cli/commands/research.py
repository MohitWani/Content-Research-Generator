"""
Research CLI Commands
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

console = Console()
app = typer.Typer(help="Research commands")


@app.command("run")
def run_research(
    query: str = typer.Argument(..., help="Research query"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
    save: bool = typer.Option(True, "--save/--no-save"),
):
    """
    Run research on a topic
    
    Example: ai-research research run "Explain attention mechanism"
    """
    async def execute():
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Conducting research...", total=None)
            
            pipeline = ResearchPipeline()
            result = await pipeline.execute(query=query, target_audience=audience)
            
            progress.update(task, description="Complete!")
        
        # Display results
        console.print("\n")
        console.print(Panel(
            f"[bold]Research Complete[/bold]\n\n"
            f"Category: {result.topic_category.value}\n"
            f"Completeness: {result.completeness_score:.0%}\n"
            f"Sources: {result.sources_count}\n"
            f"Time: {result.execution_time_seconds:.1f}s",
            title="Results",
        ))
        
        # Show summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(result.research_output.topic_summary[:500] + "...")
        
        # Show key concepts
        if result.research_output.key_concepts:
            console.print("\n[bold]Key Concepts:[/bold]")
            for key, value in list(result.research_output.key_concepts.items())[:5]:
                console.print(f"  • [cyan]{key}[/cyan]: {value[:100]}...")
        
        if result.research_output.research_data_path:
            console.print(f"\n[green]✓ Saved to {result.research_output.research_data_path}[/green]")
    
    asyncio.run(execute())


@app.command("categorize")
def categorize_topic(
    query: str = typer.Argument(..., help="Query to categorize"),
):
    """
    Categorize a research topic
    
    Determines if topic is core AI or practical implementation
    """
    async def execute():
        from src.lib.agents.topic_agent import TopicAgent
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Categorizing...", total=None)
            
            agent = TopicAgent()
            result = await agent.categorize_query(query)
            
            progress.update(task, description="Done!")
        
        # Display result
        category_color = "blue" if result.category == "core_ai" else "green"
        console.print("\n")
        console.print(Panel(
            f"[bold {category_color}]{result.category.upper()}[/bold {category_color}]\n\n"
            f"Confidence: {result.confidence:.0%}\n\n"
            f"[dim]{result.reasoning}[/dim]",
            title="Topic Category",
        ))
    
    asyncio.run(execute())


@app.command("list")
def list_queries(
    limit: int = typer.Option(10, "--limit", "-n"),
    status: Optional[str] = typer.Option(None, "--status", "-s"),
):
    """List recent research queries"""
    console.print("[yellow]Database query listing requires active database connection[/yellow]")
    console.print("Use API endpoint: GET /api/v1/research/queries")

