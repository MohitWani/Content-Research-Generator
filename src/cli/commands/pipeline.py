"""
Pipeline CLI Commands
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
app = typer.Typer(help="Pipeline execution commands")


@app.command("full")
def run_full_pipeline(
    query: str = typer.Argument(..., help="Research query"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
    tone: str = typer.Option("professional", "--tone", "-t"),
    social: bool = typer.Option(True, "--social/--no-social"),
):
    """
    Run full pipeline: Research → Blog → Social
    
    Example: ai-research pipeline full "Explain transformers" --audience beginner
    """
    async def execute():
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
        
        total_time = 0.0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Research phase
            task = progress.add_task("[1/3] Researching...", total=None)
            
            research_pipeline = ResearchPipeline()
            research_result = await research_pipeline.execute(
                query=query,
                target_audience=audience,
            )
            total_time += research_result.execution_time_seconds
            
            progress.update(task, description="[1/3] Research complete ✓")
            
            # Blog phase
            progress.update(task, description="[2/3] Generating blog...")
            
            blog_pipeline = BlogGenerationPipeline()
            blog_result = await blog_pipeline.execute_from_research(
                research_output={
                    "topic_summary": research_result.research_output.topic_summary,
                    "key_concepts": research_result.research_output.key_concepts,
                    "mathematical_foundations": research_result.research_output.mathematical_foundations,
                    "historical_context": research_result.research_output.historical_context,
                    "implementation_examples": research_result.research_output.implementation_examples,
                    "sources": research_result.research_output.sources,
                },
                target_audience=audience,
                tone=tone,
            )
            total_time += blog_result.execution_time_seconds
            
            progress.update(task, description="[3/3] Complete!")
        
        # Display results
        console.print("\n")
        
        # Summary table
        table = Table(title="Pipeline Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Topic Category", research_result.topic_category.value)
        table.add_row("Completeness", f"{research_result.completeness_score:.0%}")
        table.add_row("Sources Found", str(research_result.sources_count))
        table.add_row("Total Time", f"{total_time:.1f}s")
        
        console.print(table)
        
        # Blog preview
        console.print("\n")
        console.print(Panel(
            f"[bold]{blog_result.blog_output.title}[/bold]\n\n"
            f"{blog_result.blog_output.content[:400]}...",
            title="Blog Preview",
        ))
        
        # LinkedIn preview
        if social and blog_result.linkedin_post:
            console.print("\n")
            console.print(Panel(
                blog_result.linkedin_post.content[:200] + "...",
                title="LinkedIn Post",
            ))
        
        # File locations
        console.print("\n[bold]Output Files:[/bold]")
        if research_result.research_output.research_data_path:
            console.print(f"  Research: {research_result.research_output.research_data_path}")
        if blog_result.blog_output.file_path:
            console.print(f"  Blog: {blog_result.blog_output.file_path}")
        if blog_result.linkedin_post and blog_result.linkedin_post.file_path:
            console.print(f"  LinkedIn: {blog_result.linkedin_post.file_path}")
    
    asyncio.run(execute())


@app.command("research")
def run_research_pipeline(
    query: str = typer.Argument(..., help="Research query"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
):
    """
    Run research pipeline only
    
    Example: ai-research pipeline research "Latest in LLMs"
    """
    async def execute():
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running research pipeline...", total=None)
            
            pipeline = ResearchPipeline()
            result = await pipeline.execute(query=query, target_audience=audience)
            
            progress.update(task, description="Complete!")
        
        console.print("\n")
        console.print(Panel(
            f"Category: {result.topic_category.value}\n"
            f"Completeness: {result.completeness_score:.0%}\n"
            f"Sources: {result.sources_count}\n"
            f"Time: {result.execution_time_seconds:.1f}s",
            title="Research Pipeline Complete",
        ))
        
        if result.research_output.research_data_path:
            console.print(f"\n[green]✓ Output: {result.research_output.research_data_path}[/green]")
    
    asyncio.run(execute())


@app.command("status")
def pipeline_status():
    """Show recent pipeline executions"""
    console.print("[yellow]Pipeline status requires database connection[/yellow]")
    console.print("Use API endpoint: GET /api/v1/pipelines/executions")

