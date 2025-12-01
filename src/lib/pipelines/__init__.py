"""
Pipeline orchestration for automated workflows
"""
from src.lib.pipelines.research_pipeline import ResearchPipeline
from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline

__all__ = [
    "ResearchPipeline",
    "BlogGenerationPipeline",
]

