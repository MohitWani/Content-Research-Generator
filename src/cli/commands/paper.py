"""
Paper Research CLI Commands
CLI interface for ArXiv paper research and blog generation
Maps to: spec.md → Stories 1-8, FR1-FR10 | plan.md → Section 8 (CLI Interface Design)
"""
import asyncio
import json
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()
app = typer.Typer(
    name="paper",
    help="ArXiv paper research and blog generation commands",
    add_completion=False,
)


@app.command()
def research(
    arxiv_id: Optional[str] = typer.Option(
        None, "--arxiv-id", "-a", help="ArXiv paper ID (e.g., 2508.07407)"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Paper title to search for"
    ),
    audience: str = typer.Option(
        "practitioner", "--audience", "-au", help="Target audience: beginner, practitioner, expert"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path for research JSON"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed output"
    ),
):
    """
    Research an ArXiv paper
    
    Examples:
        paper research --arxiv-id 2508.07407
        paper research --title "Attention Is All You Need"
        paper research -a 1706.03762 -au beginner
    """
    if not arxiv_id and not title:
        console.print("[red]Error:[/red] Either --arxiv-id or --title must be provided")
        raise typer.Exit(code=1)
    
    async def run():
        from src.lib.agents.arxiv_paper_research_agent import ArXivPaperResearchAgent
        
        agent = ArXivPaperResearchAgent()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Researching paper...", total=None)
            
            try:
                if arxiv_id:
                    result = await agent.research_paper_by_id(
                        arxiv_id=arxiv_id,
                        target_audience=audience,
                    )
                else:
                    result = await agent.research_paper_by_title(
                        title=title,
                        target_audience=audience,
                    )
                
                progress.update(task, description="[green]Research complete![/green]")
                
            except Exception as e:
                progress.update(task, description="[red]Research failed[/red]")
                console.print(f"[red]Error:[/red] {e}")
                await agent.close()
                raise typer.Exit(code=1)
        
        await agent.close()
        
        # Display results
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]{result.paper_metadata.title}[/bold]\n\n"
            f"[dim]ArXiv ID: {result.paper_metadata.arxiv_id}[/dim]\n"
            f"[dim]Authors: {', '.join(result.paper_metadata.authors[:3])}{'...' if len(result.paper_metadata.authors) > 3 else ''}[/dim]\n"
            f"[dim]Published: {result.paper_metadata.published}[/dim]\n\n"
            f"[cyan]Completeness Score: {result.completeness_score:.0%}[/cyan]",
            title="Paper Research Complete",
            border_style="green",
        ))
        
        # Show paper overview
        if result.paper_overview:
            console.print("\n[bold]Paper Overview:[/bold]")
            console.print(result.paper_overview[:500] + "..." if len(result.paper_overview) > 500 else result.paper_overview)
        
        # Show key concepts
        if result.key_concepts:
            console.print("\n[bold]Key Concepts:[/bold]")
            for i, (concept, explanation) in enumerate(list(result.key_concepts.items())[:5]):
                console.print(f"  • [cyan]{concept}[/cyan]: {explanation[:100]}...")
            if len(result.key_concepts) > 5:
                console.print(f"  [dim]... and {len(result.key_concepts) - 5} more concepts[/dim]")
        
        # Show verbose output
        if verbose:
            console.print("\n[bold]Methodology Deep-Dive:[/bold]")
            console.print(result.methodology_deep_dive[:800] + "..." if result.methodology_deep_dive and len(result.methodology_deep_dive) > 800 else result.methodology_deep_dive)
        
        # Show citation
        console.print(f"\n[bold]Citation:[/bold]\n[dim]{result.citation}[/dim]")
        
        # Save output
        if output:
            output_path = Path(output)
            output_path.write_text(json.dumps(result.to_dict(), indent=2, default=str))
            console.print(f"\n[green]✓ Saved research to {output}[/green]")
        elif result.research_data_path:
            console.print(f"\n[green]✓ Research saved to {result.research_data_path}[/green]")
    
    asyncio.run(run())


@app.command()
def full(
    arxiv_id: Optional[str] = typer.Option(
        None, "--arxiv-id", "-a", help="ArXiv paper ID"
    ),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Paper title to search for"
    ),
    audience: str = typer.Option(
        "practitioner", "--audience", "-au", help="Target audience"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Output directory for files"
    ),
):
    """
    Research a paper and generate blog
    
    Complete workflow: research → blog generation
    
    Examples:
        paper full --arxiv-id 2508.07407
        paper full -t "BERT" -au beginner
    """
    if not arxiv_id and not title:
        console.print("[red]Error:[/red] Either --arxiv-id or --title must be provided")
        raise typer.Exit(code=1)
    
    async def run():
        from src.lib.agents.arxiv_paper_research_agent import ArXivPaperResearchAgent
        
        agent = ArXivPaperResearchAgent()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Research phase
            task = progress.add_task("Researching paper...", total=None)
            
            try:
                if arxiv_id:
                    research_result = await agent.research_paper_by_id(
                        arxiv_id=arxiv_id,
                        target_audience=audience,
                    )
                else:
                    research_result = await agent.research_paper_by_title(
                        title=title,
                        target_audience=audience,
                    )
                
                progress.update(task, description="Research complete, generating blog...")
                
                # Blog generation phase
                blog_result = await agent.generate_blog_from_research(
                    research_output=research_result,
                    target_audience=audience,
                )
                
                progress.update(task, description="[green]Complete![/green]")
                
            except Exception as e:
                progress.update(task, description="[red]Failed[/red]")
                console.print(f"[red]Error:[/red] {e}")
                await agent.close()
                raise typer.Exit(code=1)
        
        await agent.close()
        
        # Display results
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]{research_result.paper_metadata.title}[/bold]\n\n"
            f"[dim]ArXiv ID: {research_result.paper_metadata.arxiv_id}[/dim]\n"
            f"[cyan]Completeness: {research_result.completeness_score:.0%}[/cyan]",
            title="Paper Research",
            border_style="blue",
        ))
        
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]{blog_result.title}[/bold]\n\n"
            f"[dim]Reading time: {blog_result.estimated_reading_time or 'N/A'}[/dim]\n"
            f"[dim]Tags: {', '.join(blog_result.tags[:5])}[/dim]",
            title="Generated Blog",
            border_style="green",
        ))
        
        # Show blog preview
        if blog_result.content:
            preview = blog_result.content[:600].replace("\n\n", "\n").strip()
            console.print(f"\n[dim]{preview}...[/dim]")
        
        # Show file paths
        if research_result.research_data_path:
            console.print(f"\n[green]✓ Research:[/green] {research_result.research_data_path}")
        if blog_result.file_path:
            console.print(f"[green]✓ Blog:[/green] {blog_result.file_path}")
    
    asyncio.run(run())


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for papers"),
    max_results: int = typer.Option(
        5, "--max", "-m", help="Maximum number of results"
    ),
):
    """
    Search ArXiv for papers
    
    Examples:
        paper search "self-evolving agents"
        paper search "transformer attention" --max 10
    """
    async def run():
        from src.lib.services.arxiv_client import ArXivClient
        
        client = ArXivClient()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching ArXiv...", total=None)
            
            results = await client.search(query, max_results=max_results)
            
            progress.update(task, description=f"[green]Found {len(results)} papers[/green]")
        
        await client.close()
        
        if not results:
            console.print("[yellow]No papers found matching your query.[/yellow]")
            return
        
        # Display results
        table = Table(title=f"ArXiv Search: '{query}'")
        table.add_column("#", style="dim", width=3)
        table.add_column("ArXiv ID", style="cyan", width=12)
        table.add_column("Title", style="white", width=50)
        table.add_column("Authors", style="dim", width=25)
        table.add_column("Published", style="dim", width=10)
        
        for i, paper in enumerate(results, 1):
            authors = paper.get("authors", [])
            author_str = authors[0] if authors else "Unknown"
            if len(authors) > 1:
                author_str += f" et al. ({len(authors)})"
            
            table.add_row(
                str(i),
                paper.get("arxiv_id", "N/A"),
                paper.get("title", "Unknown")[:50] + ("..." if len(paper.get("title", "")) > 50 else ""),
                author_str[:25],
                paper.get("published", "")[:10],
            )
        
        console.print("\n")
        console.print(table)
        console.print("\n[dim]Use 'paper research --arxiv-id <ID>' to research a paper[/dim]")
    
    asyncio.run(run())


@app.command()
def info(
    arxiv_id: str = typer.Argument(..., help="ArXiv paper ID"),
):
    """
    Get paper metadata
    
    Examples:
        paper info 2508.07407
        paper info 1706.03762
    """
    async def run():
        from src.lib.services.arxiv_client import ArXivClient
        from src.lib.services.arxiv_id_parser import validate_arxiv_id, normalize_arxiv_id
        
        if not validate_arxiv_id(arxiv_id):
            console.print(f"[red]Invalid ArXiv ID format:[/red] {arxiv_id}")
            raise typer.Exit(code=1)
        
        normalized_id = normalize_arxiv_id(arxiv_id)
        client = ArXivClient()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching paper info...", total=None)
            
            paper = await client.get_paper(normalized_id)
            
            if paper:
                progress.update(task, description="[green]Found[/green]")
            else:
                progress.update(task, description="[red]Not found[/red]")
        
        await client.close()
        
        if not paper:
            console.print(f"[red]Paper not found:[/red] {normalized_id}")
            raise typer.Exit(code=1)
        
        # Display paper info
        console.print("\n")
        console.print(Panel.fit(
            f"[bold]{paper.get('title', 'Unknown')}[/bold]\n\n"
            f"[cyan]ArXiv ID:[/cyan] {paper.get('arxiv_id', normalized_id)}\n"
            f"[cyan]Published:[/cyan] {paper.get('published', 'Unknown')}\n"
            f"[cyan]Updated:[/cyan] {paper.get('updated', 'N/A')}\n"
            f"[cyan]Categories:[/cyan] {', '.join(paper.get('categories', []))}\n\n"
            f"[bold]Authors:[/bold]\n{', '.join(paper.get('authors', ['Unknown']))}\n\n"
            f"[bold]Abstract:[/bold]\n{paper.get('summary', 'No abstract available')[:500]}{'...' if len(paper.get('summary', '')) > 500 else ''}",
            title="Paper Information",
            border_style="cyan",
        ))
        
        # Show links
        console.print(f"\n[blue]Abstract:[/blue] {paper.get('abs_url', f'https://arxiv.org/abs/{normalized_id}')}")
        console.print(f"[blue]PDF:[/blue] {paper.get('pdf_url', f'https://arxiv.org/pdf/{normalized_id}.pdf')}")
    
    asyncio.run(run())


@app.command()
def batch(
    arxiv_ids: str = typer.Argument(..., help="Comma-separated ArXiv IDs"),
    audience: str = typer.Option(
        "practitioner", "--audience", "-au", help="Target audience"
    ),
    synthesize: bool = typer.Option(
        False, "--synthesize", "-s", help="Synthesize findings into one output"
    ),
):
    """
    Research multiple papers
    
    Examples:
        paper batch "2508.07407,1706.03762"
        paper batch "2508.07407,1706.03762" --synthesize
    """
    ids = [id.strip() for id in arxiv_ids.split(",") if id.strip()]
    
    if len(ids) > 5:
        console.print("[red]Error:[/red] Maximum 5 papers allowed per batch")
        raise typer.Exit(code=1)
    
    if not ids:
        console.print("[red]Error:[/red] No valid ArXiv IDs provided")
        raise typer.Exit(code=1)
    
    async def run():
        from src.lib.agents.arxiv_paper_research_agent import ArXivPaperResearchAgent
        
        agent = ArXivPaperResearchAgent()
        
        if synthesize:
            # Synthesize all papers into one
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Researching {len(ids)} papers...", total=None)
                
                try:
                    result = await agent.research_multiple_papers(
                        arxiv_ids=ids,
                        target_audience=audience,
                    )
                    
                    progress.update(task, description="[green]Complete![/green]")
                    
                except Exception as e:
                    progress.update(task, description="[red]Failed[/red]")
                    console.print(f"[red]Error:[/red] {e}")
                    await agent.close()
                    raise typer.Exit(code=1)
            
            await agent.close()
            
            # Display synthesized results
            console.print("\n")
            console.print(Panel.fit(
                f"[bold]Synthesized Research: {len(ids)} Papers[/bold]\n\n"
                f"[cyan]Completeness: {result.completeness_score:.0%}[/cyan]",
                title="Batch Research Complete",
                border_style="green",
            ))
            
            console.print("\n[bold]Combined Summary:[/bold]")
            console.print(result.topic_summary[:800] + "..." if len(result.topic_summary) > 800 else result.topic_summary)
        
        else:
            # Research each paper individually
            results = []
            for i, paper_id in enumerate(ids, 1):
                console.print(f"\n[dim]({i}/{len(ids)})[/dim] Researching {paper_id}...")
                
                try:
                    result = await agent.research_paper_by_id(
                        arxiv_id=paper_id,
                        target_audience=audience,
                    )
                    results.append(result)
                    console.print(f"  [green]✓[/green] {result.paper_metadata.title}")
                except Exception as e:
                    console.print(f"  [red]✗[/red] Failed: {e}")
            
            await agent.close()
            
            # Summary table
            if results:
                console.print("\n")
                table = Table(title="Batch Research Results")
                table.add_column("ArXiv ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Score", style="green")
                
                for r in results:
                    table.add_row(
                        r.paper_metadata.arxiv_id,
                        r.paper_metadata.title[:40] + "...",
                        f"{r.completeness_score:.0%}",
                    )
                
                console.print(table)
    
    asyncio.run(run())


if __name__ == "__main__":
    app()



