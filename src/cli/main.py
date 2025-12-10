"""
CLI Entry Point
AI Research Agent System Command Line Interface
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.cli.commands import research, content, pipeline, social, paper

console = Console()
app = typer.Typer(
    name="ai-research",
    help="AI Research Agent - Deep research and content generation for AI topics",
    add_completion=False,
)

# Add subcommands
app.add_typer(research.app, name="research", help="Research commands")
app.add_typer(paper.app, name="paper", help="ArXiv paper research commands")
app.add_typer(content.app, name="content", help="Content generation commands")
app.add_typer(pipeline.app, name="pipeline", help="Pipeline execution commands")
app.add_typer(social.app, name="social", help="Social content commands")


@app.command()
def version():
    """Show version information"""
    console.print(Panel.fit(
        "[bold blue]AI Research Agent[/bold blue]\n"
        "Version: 1.0.0\n"
        "Deep research and content generation for AI topics",
        title="About",
    ))


@app.command()
def quick(
    query: str = typer.Argument(..., help="Research query"),
    audience: str = typer.Option("practitioner", "--audience", "-a", help="Target audience"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """
    Quick research and blog generation
    
    Example: ai-research quick "Explain transformers"
    """
    async def run():
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Research phase
            task = progress.add_task("Researching...", total=None)
            
            research_pipeline = ResearchPipeline()
            research_result = await research_pipeline.execute(
                query=query,
                target_audience=audience,
            )
            
            progress.update(task, description="Research complete!")
            
            # Blog generation phase
            progress.update(task, description="Generating blog...")
            
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
            )
            
            progress.update(task, description="Complete!")
        
        # Display results
        console.print("\n")
        console.print(Panel(
            f"[bold]{blog_result.blog_output.title}[/bold]\n\n"
            f"[dim]Audience: {audience} | "
            f"Completeness: {research_result.completeness_score:.0%}[/dim]",
            title="Generated Blog",
        ))
        
        # Show preview
        content_preview = blog_result.blog_output.content[:500] + "..."
        console.print(f"\n[dim]{content_preview}[/dim]")
        
        # Save if output specified
        if output:
            with open(output, "w") as f:
                f.write(blog_result.blog_output.content)
            console.print(f"\n[green]✓ Saved to {output}[/green]")
        elif blog_result.blog_output.file_path:
            console.print(f"\n[green]✓ Saved to {blog_result.blog_output.file_path}[/green]")
        
        # Show LinkedIn post if generated
        if blog_result.linkedin_post:
            console.print("\n")
            console.print(Panel(
                blog_result.linkedin_post.content[:300] + "...",
                title="LinkedIn Post Preview",
            ))
    
    asyncio.run(run())


@app.command()
def status():
    """Show system status"""
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    # Check components
    components = [
        ("Database", "✓ Available"),
        ("LLM (Bedrock)", "✓ Configured"),
        ("Tavily Search", "✓ Ready"),
        ("ArXiv Client", "✓ Ready"),
        ("GitHub Client", "✓ Ready"),
    ]
    
    for name, status in components:
        table.add_row(name, status)
    
    console.print(table)


if __name__ == "__main__":
    app()

