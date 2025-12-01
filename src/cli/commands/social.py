"""
CLI Commands for Social Content Generation
LinkedIn posts, Twitter threads, and summaries
"""
import asyncio
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
app = typer.Typer(help="Social content generation commands")


@app.command("linkedin")
def generate_linkedin(
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Content to convert"),
    content_file: Optional[Path] = typer.Option(None, "--file", "-f", help="File with content"),
    blog_id: Optional[int] = typer.Option(None, "--blog-id", "-b", help="Blog content ID"),
    research_id: Optional[int] = typer.Option(None, "--research-id", "-r", help="Research query ID"),
    audience: str = typer.Option("practitioner", "--audience", "-a", help="Target audience"),
    no_hashtags: bool = typer.Option(False, "--no-hashtags", help="Skip hashtags"),
    no_cta: bool = typer.Option(False, "--no-cta", help="Skip call-to-action"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """
    Generate a LinkedIn post from content
    
    Examples:
        ai-research social linkedin -c "My content here"
        ai-research social linkedin -f blog.md
        ai-research social linkedin -b 1
    """
    async def run():
        from src.lib.agents.shortform_agent import ShortformAgent
        
        # Get content
        source_content = None
        
        if content:
            source_content = {"content": content}
        elif content_file and content_file.exists():
            source_content = {"content": content_file.read_text()}
        elif blog_id or research_id:
            from src.common.database import get_session
            from src.lib.models.research import ContentItem, ResearchResult
            from sqlalchemy import select
            
            async with get_session() as db:
                if blog_id:
                    item = await db.get(ContentItem, blog_id)
                    if item:
                        source_content = {"title": item.title, "content": item.content}
                elif research_id:
                    result = await db.scalar(
                        select(ResearchResult).where(ResearchResult.query_id == research_id)
                    )
                    if result:
                        source_content = {
                            "topic_summary": result.topic_summary,
                            "key_concepts": result.key_concepts or {},
                        }
        
        if not source_content:
            console.print("[red]Error: Provide content via --content, --file, --blog-id, or --research-id[/red]")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating LinkedIn post...", total=None)
            
            agent = ShortformAgent()
            post = await agent.generate_linkedin_post(
                source_content=source_content,
                target_audience=audience,
                include_hashtags=not no_hashtags,
                include_cta=not no_cta,
            )
            
            progress.update(task, description="Complete!")
        
        # Display result
        console.print("\n")
        console.print(Panel(
            post.content,
            title=f"[bold]LinkedIn Post[/bold] ({post.character_count} chars)",
            subtitle=f"Audience: {audience}",
        ))
        
        if post.hashtags:
            console.print(f"\n[dim]Hashtags: {' '.join('#' + h for h in post.hashtags)}[/dim]")
        
        if post.call_to_action:
            console.print(f"[dim]CTA: {post.call_to_action}[/dim]")
        
        # Save if requested
        if output:
            output.write_text(post.content)
            console.print(f"\n[green]✓ Saved to {output}[/green]")
        elif post.file_path:
            console.print(f"\n[green]✓ Auto-saved to {post.file_path}[/green]")
    
    asyncio.run(run())


@app.command("thread")
def generate_thread(
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Content to convert"),
    content_file: Optional[Path] = typer.Option(None, "--file", "-f", help="File with content"),
    blog_id: Optional[int] = typer.Option(None, "--blog-id", "-b", help="Blog content ID"),
    max_posts: int = typer.Option(5, "--posts", "-p", help="Number of posts in thread"),
    platform: str = typer.Option("twitter", "--platform", help="twitter or threads"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """
    Generate a Twitter/X thread from content
    
    Examples:
        ai-research social thread -c "My long content" -p 5
        ai-research social thread -f blog.md --platform threads
    """
    async def run():
        from src.lib.agents.shortform_agent import ShortformAgent
        
        # Get content
        source_content = None
        
        if content:
            source_content = {"content": content}
        elif content_file and content_file.exists():
            source_content = {"content": content_file.read_text()}
        elif blog_id:
            from src.common.database import get_session
            from src.lib.models.research import ContentItem
            
            async with get_session() as db:
                item = await db.get(ContentItem, blog_id)
                if item:
                    source_content = {"title": item.title, "content": item.content}
        
        if not source_content:
            console.print("[red]Error: Provide content via --content, --file, or --blog-id[/red]")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating {platform} thread...", total=None)
            
            agent = ShortformAgent()
            thread = await agent.generate_thread(
                source_content=source_content,
                max_posts=max_posts,
                platform=platform,
            )
            
            progress.update(task, description="Complete!")
        
        # Display result
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]{thread.topic}[/bold]\n{thread.total_posts} posts",
            title=f"{platform.title()} Thread",
        ))
        
        table = Table(show_header=True)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Content")
        table.add_column("Chars", style="dim", width=5)
        
        for post in thread.posts:
            table.add_row(
                str(post.position),
                post.content[:100] + "..." if len(post.content) > 100 else post.content,
                str(post.character_count),
            )
        
        console.print(table)
        
        # Save if requested
        if output:
            thread_text = "\n\n---\n\n".join(p.content for p in thread.posts)
            output.write_text(thread_text)
            console.print(f"\n[green]✓ Saved to {output}[/green]")
    
    asyncio.run(run())


@app.command("summarize")
def summarize_content(
    content: str = typer.Argument(..., help="Content to summarize"),
    max_length: int = typer.Option(280, "--length", "-l", help="Max characters"),
):
    """
    Create a brief social media summary
    
    Example:
        ai-research social summarize "Long content here" -l 280
    """
    async def run():
        from src.lib.agents.shortform_agent import ShortformAgent
        
        agent = ShortformAgent()
        summary = await agent.summarize_for_social(
            content=content,
            max_length=max_length,
        )
        
        console.print("\n")
        console.print(Panel(
            summary,
            title=f"Summary ({len(summary)}/{max_length} chars)",
        ))
    
    asyncio.run(run())


if __name__ == "__main__":
    app()


