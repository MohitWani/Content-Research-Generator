"""
Research Data Service

Handles persistence of research data to files.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config.environment_config import settings
from app.core.logging.logger import logger
from app.modules.research.schemas.agent_schemas import ResearchOutput


class ResearchDataService:
    """
    Service for persisting research data to files.
    
    Handles:
    - Saving research output to JSON files
    - Managing research data directory
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the research data service.
        
        Args:
            data_dir: Base data directory (defaults to settings.DATA_DIR)
        """
        self.data_dir = Path(data_dir or settings.DATA_DIR)
        self.research_dir = self.data_dir / "research" / "summaries"

    def _ensure_directory(self) -> None:
        """Ensure the research directory exists."""
        self.research_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, query: str) -> str:
        """
        Generate a filename for the research data.
        
        Args:
            query: Research query
            
        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c if c.isalnum() else "_" for c in query[:50])
        return f"{timestamp}_{safe_query}.json"

    async def save(self, query: str, output: ResearchOutput) -> str:
        """
        Save research output to a JSON file.
        
        Args:
            query: Original research query
            output: Research output to save
            
        Returns:
            Path to the saved file, or empty string on failure
        """
        try:
            self._ensure_directory()

            filename = self._generate_filename(query)
            filepath = self.research_dir / filename

            data = {
                "query": query,
                "agent_type": "agentic_researcher",
                "topic_summary": output.topic_summary,
                "key_concepts": output.key_concepts,
                "mathematical_foundations": output.mathematical_foundations,
                "source_summary": output.source_descriptions,
                "implementation_examples": output.implementation_examples,
                "sources": output.sources,
                "completeness_score": output.completeness_score,
                "created_at": datetime.now().isoformat(),
            }

            filepath.write_text(
                json.dumps(data, indent=2, default=str)
            )

            logger.info(f"[DATA] Saved research to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"[DATA] Failed to save research: {e}")
            return ""

    def load(self, filepath: str) -> Optional[dict]:
        """
        Load research data from a file.
        
        Args:
            filepath: Path to the research data file
            
        Returns:
            Research data dictionary, or None on failure
        """
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"[DATA] File not found: {filepath}")
                return None

            data = json.loads(path.read_text())
            logger.info(f"[DATA] Loaded research from {filepath}")
            return data

        except Exception as e:
            logger.error(f"[DATA] Failed to load research: {e}")
            return None

    def list_research_files(self) -> list[str]:
        """
        List all research data files.
        
        Returns:
            List of file paths
        """
        try:
            self._ensure_directory()
            files = sorted(
                self.research_dir.glob("*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            return [str(f) for f in files]

        except Exception as e:
            logger.error(f"[DATA] Failed to list files: {e}")
            return []
