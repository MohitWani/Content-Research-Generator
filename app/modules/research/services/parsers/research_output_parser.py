"""
Research Output Parser Service

Handles parsing of agent messages and outputs into structured data.
"""
import json
from typing import Any, Dict, List, Tuple

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.schemas.agent_schemas import (
    ParsedAgentResponse,
    ResearchOutput,
    ToolCallSchema,
    ToolResultSchema,
)
from app.modules.research.services.tools import SOURCE_TYPE_MAPPING


class ResearchOutputParser:
    """
    Service for parsing research agent outputs.
    
    Handles:
    - Extracting tool calls and results from messages
    - Parsing JSON output from agent responses
    - Building source summaries
    - Calculating completeness scores
    """

    # Labels for source summary
    SOURCE_LABELS = {
        "web_search": "Web Search",
        "arxiv_search": "Academic Papers",
        "wikipedia": "Wikipedia",
        "github_search": "GitHub",
        "scrape_url": "Web Content",
    }

    def extract_from_messages(
        self,
        messages: List[BaseMessage],
    ) -> ParsedAgentResponse:
        """
        Extract tool calls, results, and final content from agent messages.
        
        Args:
            messages: List of messages from agent execution
            
        Returns:
            ParsedAgentResponse containing extracted data
        """
        tool_calls: List[ToolCallSchema] = []
        tool_results: List[ToolResultSchema] = []
        final_content = ""

        logger.info(f"[PARSER] Processing {len(messages)} messages")

        for msg in messages:
            if isinstance(msg, AIMessage):
                tool_calls.extend(self._extract_tool_calls(msg))
                if msg.content:
                    final_content = msg.content

            elif isinstance(msg, ToolMessage) and msg.content:
                tool_result = self._extract_tool_result(msg)
                if tool_result:
                    tool_results.append(tool_result)

        return ParsedAgentResponse(
            tool_calls=tool_calls,
            tool_results=tool_results,
            final_content=final_content,
        )

    def _extract_tool_calls(self, msg: AIMessage) -> List[ToolCallSchema]:
        """Extract tool calls from an AI message."""
        tool_calls = []

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name", "unknown")
                args = tc.get("args", {})
                logger.info(f"[PARSER] Tool call: {name}: {str(args)[:60]}")

                tool_calls.append(
                    ToolCallSchema(
                        tool=name,
                        query=str(args)[:100],
                        type=SOURCE_TYPE_MAPPING.get(name, "web"),
                    )
                )

        return tool_calls

    def _extract_tool_result(self, msg: ToolMessage) -> ToolResultSchema | None:
        """Extract tool result from a tool message."""
        name = getattr(msg, "name", "unknown")
        logger.info(f"[PARSER] Tool result: {name} ({len(msg.content)} chars)")

        return ToolResultSchema(
            tool=name,
            content=msg.content[:4000],
        )

    def parse_output(
        self,
        parsed_response: ParsedAgentResponse,
        query: str,
        category: TopicCategory,
    ) -> ResearchOutput:
        """
        Parse agent response into structured ResearchOutput.
        
        Args:
            parsed_response: Parsed agent response
            query: Original research query
            category: Topic category
            
        Returns:
            Structured ResearchOutput
        """
        # Parse JSON from final content
        data = self._parse_json_content(parsed_response.final_content)

        # Deduplicate sources
        sources = self._deduplicate_sources(parsed_response.tool_calls)

        # Build source summary
        source_summary = self._build_source_summary(parsed_response.tool_results)

        # Use fallback if output is insufficient
        if not data.get("topic_summary") or len(data.get("topic_summary", "")) < 100:
            logger.warning("[PARSER] Using fallback output")
            data = {
                "topic_summary": f"Research on: {query}. Collected {len(sources)} sources.",
                "key_concepts": {"query": query},
            }

        # Create output
        output = ResearchOutput(
            topic_summary=data.get("topic_summary", ""),
            key_concepts=data.get("key_concepts", {}),
            mathematical_foundations=data.get("mathematical_foundations"),
            source_descriptions=source_summary,
            implementation_examples=data.get("implementation_examples"),
            sources=sources,
        )

        # Calculate completeness score
        output.completeness_score = self._calculate_score(output, category)

        logger.info(
            f"[PARSER] Output: {len(output.topic_summary)} chars, {len(sources)} sources"
        )

        return output

    def _parse_json_content(self, content: str) -> Dict[str, Any]:
        """Parse JSON from content string."""
        if not content:
            return {}

        try:
            start = content.find("{")
            end = content.rfind("}") + 1

            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                logger.info(f"[PARSER] JSON keys: {list(data.keys())}")
                return data

        except json.JSONDecodeError as e:
            logger.warning(f"[PARSER] JSON error: {e}")

        return {}

    def _deduplicate_sources(
        self,
        tool_calls: List[ToolCallSchema],
    ) -> List[Dict[str, Any]]:
        """Deduplicate sources from tool calls."""
        sources = []
        seen = set()

        for tc in tool_calls:
            key = f"{tc.tool}:{tc.query[:40]}"
            if key not in seen:
                seen.add(key)
                sources.append(tc.model_dump())

        return sources

    def _build_source_summary(
        self,
        tool_results: List[ToolResultSchema],
    ) -> str:
        """Build source summary from tool results."""
        if not tool_results:
            return ""

        # Group by tool
        grouped: Dict[str, List[int]] = {}
        for result in tool_results:
            grouped.setdefault(result.tool, []).append(1)

        # Build summary parts
        parts = [
            f"**{self.SOURCE_LABELS.get(tool, tool)}** ({len(counts)} results)"
            for tool, counts in grouped.items()
        ]

        return "Sources: " + ", ".join(parts) if parts else ""

    def _calculate_score(
        self,
        output: ResearchOutput,
        category: TopicCategory,
    ) -> float:
        """
        Calculate completeness score (0-1).
        
        Scoring criteria:
        - Topic summary length
        - Number of key concepts
        - Number of sources
        - Category-specific content (math for AI, examples for others)
        """
        score = 0.0

        # Score for topic summary length
        summary_len = len(output.topic_summary)
        if summary_len > 1000:
            score += 2.0
        elif summary_len > 500:
            score += 1.5
        elif summary_len > 200:
            score += 1.0

        # Score for key concepts
        concepts_count = len(output.key_concepts)
        if concepts_count >= 5:
            score += 1.0
        elif concepts_count >= 3:
            score += 0.7
        elif concepts_count >= 1:
            score += 0.3

        # Score for sources
        sources_count = len(output.sources)
        if sources_count >= 8:
            score += 1.0
        elif sources_count >= 5:
            score += 0.7
        elif sources_count >= 3:
            score += 0.4

        # Category-specific scoring
        if category == TopicCategory.CORE_AI:
            if (
                output.mathematical_foundations
                and len(output.mathematical_foundations) > 50
            ):
                score += 1.0
        else:
            if (
                output.implementation_examples
                and len(output.implementation_examples) > 50
            ):
                score += 1.0

        return min(score / 5.0, 1.0)
