"""
Repository layer for Research module
"""
from app.modules.research.repositories.research_repository import (
    ResearchQueryRepository,
    ResearchResultRepository,
)

__all__ = [
    "ResearchQueryRepository",
    "ResearchResultRepository",
]
