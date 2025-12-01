"""
Content CLI Commands
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
app = typer.Typer(help="Content generation commands")


@app.command("blog")
def generate_blog(
    topic: str = typer.Argument(..., help="Topic or research summary"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
    tone: str = typer.Option("professional", "--tone", "-t"),
    output: Optional[str] = typer.Option(None, "--output", "-o"),
):
    """
    Generate a blog post from topic
    
    Example: ai-research content blog "Transformers explained"
    """
    async def execute():
        from src.lib.agents.blog_writer_agent import BlogWriterAgent
        from src.lib.agents.branding_agent import BrandingAgent
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating blog...", total=None)
            
            # Create minimal research data
            research_data = {
                "topic_summary": topic,
                "key_concepts": {},
                "sources": [],
            }
            
            writer = BlogWriterAgent()
            blog = await writer.generate_blog(
                research_data=research_data,
                target_audience=audience,
                tone=tone,
            )
            
            # Apply branding
            progress.update(task, description="Applying branding...")
            branding = BrandingAgent()
            branded = await branding.apply_branding(
                content=blog.content,
                target_audience=audience,
            )
            blog.content = branded.branded_content
            
            progress.update(task, description="Complete!")
        
        # Display result
        console.print("\n")
        console.print(Panel(
            f"[bold]{blog.title}[/bold]\n\n"
            f"[dim]Audience: {audience} | Tone: {tone}[/dim]",
            title="Generated Blog",
        ))
        
        console.print(f"\n{blog.content[:800]}...")
        
        if output:
            with open(output, "w") as f:
                f.write(f"# {blog.title}\n\n{blog.content}")
            console.print(f"\n[green]✓ Saved to {output}[/green]")
        elif blog.file_path:
            console.print(f"\n[green]✓ Saved to {blog.file_path}[/green]")
    
    asyncio.run(execute())


@app.command("linkedin")
def generate_linkedin(
    topic: str = typer.Argument(..., help="Topic for LinkedIn post"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
):
    """
    Generate a LinkedIn post
    
    Example: ai-research content linkedin "New transformer paper"
    """
    async def execute():
        from src.lib.agents.shortform_agent import ShortformAgent
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating post...", total=None)
            
            agent = ShortformAgent()
            post = await agent.generate_linkedin_post(
                source_content={"topic_summary": topic, "title": topic},
                target_audience=audience,
            )
            
            progress.update(task, description="Complete!")
        
        # Display result
        console.print("\n")
        console.print(Panel(
            post.content,
            title=f"LinkedIn Post ({post.character_count} chars)",
        ))
        
        if post.hashtags:
            console.print(f"\n[blue]{' '.join('#' + h for h in post.hashtags)}[/blue]")
        
        if post.file_path:
            console.print(f"\n[green]✓ Saved to {post.file_path}[/green]")
    
    asyncio.run(execute())


@app.command("adapt")
def adapt_content(
    file: str = typer.Argument(..., help="Path to content file"),
    from_audience: str = typer.Option("practitioner", "--from", "-f"),
    to_audience: str = typer.Option("beginner", "--to", "-t"),
):
    """
    Adapt content for different audience
    
    Example: ai-research content adapt blog.md --from expert --to beginner
    """
    async def execute():
        from src.lib.agents.blog_writer_agent import BlogWriterAgent
        from pathlib import Path
        
        # Read file
        content = Path(file).read_text()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Adapting content...", total=None)
            
            writer = BlogWriterAgent()
            adapted = await writer.adapt_tone(
                content=content,
                original_audience=from_audience,
                new_audience=to_audience,
            )
            
            progress.update(task, description="Complete!")
        
        console.print("\n[bold]Adapted Content:[/bold]\n")
        console.print(adapted[:1000] + "...")
        
        # Save adapted version
        output_path = file.replace(".md", f"_{to_audience}.md")
        Path(output_path).write_text(adapted)
        console.print(f"\n[green]✓ Saved to {output_path}[/green]")
    
    asyncio.run(execute())

