"""
ArXiv Paper Research API Routes
Endpoints for paper research and blog generation
Maps to: spec.md → Stories 1-8, FR1-FR10 | plan.md → Section 7 (API Design)
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.common.database import get_db, get_session
from src.lib.agents.arxiv_paper_research_agent import (
    ArXivPaperResearchAgent,
    PaperResearchOutput,
    PaperMetadata,
    BlogOutput,
)
from src.lib.services.arxiv_client import ArXivClient
from src.lib.services.arxiv_id_parser import validate_arxiv_id, normalize_arxiv_id
from src.lib.models.schemas import (
    PaperResearchRequest,
    PaperResearchResponse,
    PaperFullResponse,
    PaperSearchRequest,
    PaperBlogRequest,
    MultiplePaperResearchRequest,
    PaperMetadataSchema,
    EnhancedResearchResultSchema,
    BlogGenerationResponse,
    StatusEnum,
    SourceSchema,
    ErrorResponse,
)
from src.lib.models.exceptions import (
    InvalidArXivIdError,
    PaperNotFoundError,
    PaperContentInsufficientError,
    MultiplePapersLimitError,
)
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


def _convert_paper_metadata(metadata: PaperMetadata) -> PaperMetadataSchema:
    """Convert PaperMetadata dataclass to Pydantic schema"""
    return PaperMetadataSchema(
        arxiv_id=metadata.arxiv_id,
        title=metadata.title,
        authors=metadata.authors,
        abstract=metadata.abstract,
        published=metadata.published,
        updated=metadata.updated,
        categories=metadata.categories,
        pdf_url=metadata.pdf_url,
        abs_url=metadata.abs_url,
    )


def _convert_research_output(output: PaperResearchOutput) -> EnhancedResearchResultSchema:
    """Convert PaperResearchOutput dataclass to Pydantic schema"""
    sources = [
        SourceSchema(
            type=s.get("type", "paper"),
            title=s.get("title", ""),
            url=s.get("url"),
            authors=s.get("authors"),
        )
        for s in output.sources
    ]
    
    return EnhancedResearchResultSchema(
        topic_summary=output.topic_summary,
        key_concepts=output.key_concepts,
        mathematical_foundations=output.mathematical_foundations,
        historical_context=output.historical_context,
        implementation_examples=output.implementation_examples,
        sources=sources,
        paper_overview=output.paper_overview,
        methodology_deep_dive=output.methodology_deep_dive,
        experimental_results=output.experimental_results,
        practical_implications=output.practical_implications,
        limitations_future_work=output.limitations_future_work,
        related_work_summary=output.related_work_summary,
        citation=output.citation,
        paper_metadata=_convert_paper_metadata(output.paper_metadata),
        completeness_score=output.completeness_score,
        research_data_path=output.research_data_path,
    )


def _convert_blog_output(output: BlogOutput) -> BlogGenerationResponse:
    """Convert BlogOutput dataclass to Pydantic schema"""
    return BlogGenerationResponse(
        content_id=0,  # Will be set if persisted
        title=output.title,
        content=output.content,
        file_path=output.file_path,
        status=StatusEnum.COMPLETED,
    )


# ============= Paper Research Endpoints =============

@router.post(
    "/research/sync",
    response_model=EnhancedResearchResultSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ArXiv ID format"},
        404: {"model": ErrorResponse, "description": "Paper not found"},
        422: {"model": ErrorResponse, "description": "Paper content insufficient"},
    },
)
async def research_paper_sync(
    request: PaperResearchRequest,
) -> EnhancedResearchResultSchema:
    """
    Research an ArXiv paper synchronously
    
    Accepts either arxiv_id or title_search.
    Returns comprehensive research with enhanced sections.
    
    **Response time:** 30-60 seconds depending on paper complexity.
    """
    try:
        agent = ArXivPaperResearchAgent()
        
        target_audience = request.target_audience.value if request.target_audience else "practitioner"
        
        if request.paper.arxiv_id:
            result = await agent.research_paper_by_id(
                arxiv_id=request.paper.arxiv_id,
                target_audience=target_audience,
            )
        elif request.paper.title_search:
            result = await agent.research_paper_by_title(
                title=request.paper.title_search,
                target_audience=target_audience,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either arxiv_id or title_search must be provided"
            )
        
        await agent.close()
        
        logger.info(f"Completed paper research: {result.paper_metadata.arxiv_id}")
        
        return _convert_research_output(result)
    
    except InvalidArXivIdError as e:
        logger.warning(f"Invalid ArXiv ID: {e.arxiv_id}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except PaperNotFoundError as e:
        logger.warning(f"Paper not found: {e.arxiv_id}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except PaperContentInsufficientError as e:
        logger.warning(f"Insufficient paper content: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error(f"Paper research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/full/sync",
    response_model=PaperFullResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ArXiv ID format"},
        404: {"model": ErrorResponse, "description": "Paper not found"},
    },
)
async def research_and_blog_sync(
    request: PaperResearchRequest,
) -> PaperFullResponse:
    """
    Research an ArXiv paper and generate blog synchronously
    
    Combined endpoint for full workflow: paper research + blog generation.
    
    **Response time:** 60-120 seconds.
    """
    try:
        agent = ArXivPaperResearchAgent()
        
        target_audience = request.target_audience.value if request.target_audience else "practitioner"
        
        # Conduct research
        if request.paper.arxiv_id:
            research_result = await agent.research_paper_by_id(
                arxiv_id=request.paper.arxiv_id,
                target_audience=target_audience,
            )
        elif request.paper.title_search:
            research_result = await agent.research_paper_by_title(
                title=request.paper.title_search,
                target_audience=target_audience,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either arxiv_id or title_search must be provided"
            )
        
        # Generate blog if requested
        blog_result = None
        if request.generate_blog:
            blog_output = await agent.generate_blog_from_research(
                research_output=research_result,
                target_audience=target_audience,
            )
            blog_result = _convert_blog_output(blog_output)
        
        await agent.close()
        
        logger.info(f"Completed full paper workflow: {research_result.paper_metadata.arxiv_id}")
        
        return PaperFullResponse(
            research_id=0,  # ID would be set if persisted to DB
            paper_metadata=_convert_paper_metadata(research_result.paper_metadata),
            research=_convert_research_output(research_result),
            blog=blog_result,
            status=StatusEnum.COMPLETED,
        )
    
    except InvalidArXivIdError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except PaperNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Full paper workflow failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/blog/sync",
    response_model=BlogGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Paper not found"},
    },
)
async def generate_paper_blog_sync(
    request: PaperResearchRequest,
) -> BlogGenerationResponse:
    """
    Generate blog from ArXiv paper synchronously
    
    Conducts research and generates blog post in one call.
    """
    try:
        agent = ArXivPaperResearchAgent()
        
        target_audience = request.target_audience.value if request.target_audience else "practitioner"
        
        # Conduct research first
        if request.paper.arxiv_id:
            research_result = await agent.research_paper_by_id(
                arxiv_id=request.paper.arxiv_id,
                target_audience=target_audience,
            )
        elif request.paper.title_search:
            research_result = await agent.research_paper_by_title(
                title=request.paper.title_search,
                target_audience=target_audience,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either arxiv_id or title_search must be provided"
            )
        
        # Generate blog
        blog_output = await agent.generate_blog_from_research(
            research_output=research_result,
            target_audience=target_audience,
        )
        
        await agent.close()
        
        logger.info(f"Generated blog for paper: {research_result.paper_metadata.arxiv_id}")
        
        return _convert_blog_output(blog_output)
    
    except InvalidArXivIdError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except PaperNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Paper Search Endpoints =============

@router.post(
    "/search",
    response_model=List[PaperMetadataSchema],
    responses={
        400: {"model": ErrorResponse, "description": "Invalid search query"},
    },
)
async def search_papers(
    request: PaperSearchRequest,
) -> List[PaperMetadataSchema]:
    """
    Search ArXiv for papers by query
    
    Returns list of matching papers with metadata.
    """
    try:
        arxiv_client = ArXivClient()
        
        results = await arxiv_client.search(
            query=request.query,
            max_results=request.max_results or 5,
        )
        
        await arxiv_client.close()
        
        return [
            PaperMetadataSchema(
                arxiv_id=paper.get("arxiv_id", ""),
                title=paper.get("title", ""),
                authors=paper.get("authors", []),
                abstract=paper.get("summary", ""),
                published=paper.get("published", ""),
                updated=paper.get("updated"),
                categories=paper.get("categories", []),
                pdf_url=paper.get("pdf_url"),
                abs_url=paper.get("abs_url"),
            )
            for paper in results
        ]
    
    except Exception as e:
        logger.error(f"Paper search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/info/{arxiv_id:path}",
    response_model=PaperMetadataSchema,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid ArXiv ID"},
        404: {"model": ErrorResponse, "description": "Paper not found"},
    },
)
async def get_paper_info(
    arxiv_id: str,
) -> PaperMetadataSchema:
    """
    Get paper metadata by ArXiv ID
    
    Quick lookup of paper information without full research.
    """
    try:
        if not validate_arxiv_id(arxiv_id):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ArXiv ID format: {arxiv_id}"
            )
        
        normalized_id = normalize_arxiv_id(arxiv_id)
        arxiv_client = ArXivClient()
        
        paper = await arxiv_client.get_paper(normalized_id)
        
        await arxiv_client.close()
        
        if not paper:
            raise HTTPException(
                status_code=404,
                detail=f"Paper not found: {normalized_id}"
            )
        
        return PaperMetadataSchema(
            arxiv_id=paper.get("arxiv_id", normalized_id),
            title=paper.get("title", ""),
            authors=paper.get("authors", []),
            abstract=paper.get("summary", ""),
            published=paper.get("published", ""),
            updated=paper.get("updated"),
            categories=paper.get("categories", []),
            pdf_url=paper.get("pdf_url"),
            abs_url=paper.get("abs_url"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Paper info lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Multiple Papers Endpoint =============

@router.post(
    "/research/multiple/sync",
    response_model=EnhancedResearchResultSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or too many papers"},
        404: {"model": ErrorResponse, "description": "No papers found"},
    },
)
async def research_multiple_papers_sync(
    request: MultiplePaperResearchRequest,
) -> EnhancedResearchResultSchema:
    """
    Research multiple ArXiv papers and synthesize findings
    
    Maximum 5 papers per request.
    Returns synthesized research combining all papers.
    """
    try:
        agent = ArXivPaperResearchAgent()
        
        target_audience = request.target_audience.value if request.target_audience else "practitioner"
        
        result = await agent.research_multiple_papers(
            arxiv_ids=request.arxiv_ids,
            target_audience=target_audience,
        )
        
        await agent.close()
        
        logger.info(f"Completed multiple paper research: {len(request.arxiv_ids)} papers")
        
        return _convert_research_output(result)
    
    except MultiplePapersLimitError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except PaperNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except InvalidArXivIdError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Multiple paper research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
