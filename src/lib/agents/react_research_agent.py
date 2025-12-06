"""
ReAct Research Agent using LangGraph with LangChain Tools
Implements Thought → Action → Observation loop for deep research
Uses LangChain's built-in tool implementations
Maps to: spec.md → Story 1, Story 8, Story 9, FR2
"""
from typing import Dict, Any, List, Optional, Annotated, TypedDict, Literal
from dataclasses import dataclass, field
import json
from pathlib import Path
from datetime import datetime
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool, BaseTool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# LangChain Community Tools
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.utilities.arxiv import ArxivAPIWrapper
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.document_loaders import WebBaseLoader

from src.lib.llm.model import BedrockLLM
from src.lib.models.research import TopicCategory
from src.lib.models.exceptions import ResearchDataInsufficientError, ExternalAPIError
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


# ============= Agent State =============

class AgentState(TypedDict):
    """State for the ReAct research agent"""
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    category: str
    target_audience: str
    research_data: Dict[str, Any]
    sources: List[Dict[str, Any]]
    iteration_count: int
    max_iterations: int
    is_complete: bool


# ============= Research Output =============

@dataclass
class ResearchOutput:
    """Structured output from research agent"""
    topic_summary: str
    key_concepts: Dict[str, str]
    mathematical_foundations: Optional[str] = None
    historical_context: Optional[str] = None
    implementation_examples: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    research_data_path: Optional[str] = None
    completeness_score: float = 0.0


# ============= LangChain Tools Setup =============

def create_langchain_tools() -> List[BaseTool]:
    """
    Create research tools using LangChain's built-in implementations
    
    Returns:
        List of LangChain tools for research
    """
    tools = []
    
    # 1. Tavily Search Tool (AI-powered web search)
    try:
        tavily_api_key = config.TAVILY_API_KEY
        if tavily_api_key:
            tavily_search = TavilySearchResults(
                max_results=3,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
                include_images=False,
                name="tavily_search",
                description="""Search the web using Tavily AI Search for comprehensive, AI-optimized results.
Use this tool for:
- General web searches about AI topics
- Finding tutorials and documentation
- Getting current information and news
- Searching for explanations and guides

Input should be a search query string.
Returns: List of search results with titles, URLs, and content snippets."""
            )
            tools.append(tavily_search)
            logger.info("Initialized Tavily Search tool")
        else:
            logger.warning("Tavily API key not configured, skipping Tavily tool")
    except Exception as e:
        logger.warning(f"Failed to initialize Tavily tool: {e}")
    
    # 2. ArXiv Search Tool (Academic papers)
    try:
        arxiv_wrapper = ArxivAPIWrapper(
            top_k_results=5,
            doc_content_chars_max=4000,
            load_max_docs=5,
            load_all_available_meta=True,
        )
        arxiv_tool = ArxivQueryRun(
            api_wrapper=arxiv_wrapper,
            name="arxiv_search",
            description="""Search ArXiv for academic research papers on AI, ML, and related topics.
Use this tool to:
- Find foundational papers and seminal research
- Get theoretical foundations and mathematical formulations
- Discover recent research and cutting-edge work
- Find papers by specific authors or on specific topics

Input should be a search query string (e.g., "attention mechanism transformers" or "1706.03762" for paper ID).
Returns: Paper titles, authors, abstracts, and publication details."""
        )
        tools.append(arxiv_tool)
        logger.info("Initialized ArXiv Search tool")
    except Exception as e:
        logger.warning(f"Failed to initialize ArXiv tool: {e}")
    
    # 3. Wikipedia Tool (Background knowledge)
    try:
        wikipedia_wrapper = WikipediaAPIWrapper(
            top_k_results=3,
            doc_content_chars_max=4000,
        )
        wikipedia_tool = WikipediaQueryRun(
            api_wrapper=wikipedia_wrapper,
            name="wikipedia_search",
            description="""Search Wikipedia for background information and general knowledge.
Use this tool to:
- Get historical context and background
- Understand fundamental concepts
- Find biographical information about researchers
- Get overview of broad topics

Input should be a search query string.
Returns: Wikipedia article summaries and content."""
        )
        tools.append(wikipedia_tool)
        logger.info("Initialized Wikipedia Search tool")
    except Exception as e:
        logger.warning(f"Failed to initialize Wikipedia tool: {e}")
    
    # 4. Web Page Loader Tool (Scrape specific URLs)
    @tool
    def scrape_webpage(url: str) -> str:
        """
        Load and extract content from a specific webpage URL.
        Use this tool to get detailed content from pages found in search results.
        
        Args:
            url: The URL of the webpage to load
        
        Returns:
            Extracted text content from the webpage
        """
        try:
            loader = WebBaseLoader(
                web_paths=[url],
                requests_kwargs={"timeout": 10},
            )
            docs = loader.load()
            
            if docs:
                content = docs[0].page_content
                # Truncate very long content
                if len(content) > 6000:
                    content = content[:6000] + "\n\n[Content truncated...]"
                return f"**Content from {url}:**\n\n{content}"
            return f"Could not extract content from {url}"
            
        except Exception as e:
            return f"Error loading webpage: {str(e)}"
    
    tools.append(scrape_webpage)
    logger.info("Initialized Web Scraper tool")
    
    # 5. GitHub Search Tool (Code repositories)
    @tool
    def github_search(query: str, language: str = "python", max_results: int = 5) -> str:
        """
        Search GitHub for repositories related to AI/ML implementations and code examples.
        Use this tool to:
        - Find reference implementations
        - Discover popular libraries and frameworks
        - Get practical code examples
        - Find trending AI projects
        
        Args:
            query: Search query for repositories
            language: Programming language filter (default: python)
            max_results: Maximum number of repos to return (default: 5)
        
        Returns:
            List of repositories with names, descriptions, stars, and URLs
        """
        import httpx
        
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "AI-Research-Agent",
            }
            
            # Add token if available
            github_token = getattr(config, 'GITHUB_TOKEN', None)
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            search_query = f"{query} language:{language}"
            params = {
                "q": search_query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(max_results, 10),
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    "https://api.github.com/search/repositories",
                    params=params,
                    headers=headers,
                )
                
                if response.status_code != 200:
                    return f"GitHub API error: {response.status_code}"
                
                data = response.json()
                repos = data.get("items", [])
                
                if not repos:
                    return "No repositories found."
                
                output_parts = [f"**Found {len(repos)} repositories:**\n"]
                
                for i, repo in enumerate(repos[:max_results], 1):
                    topics = ", ".join(repo.get("topics", [])[:5]) or "N/A"
                    output_parts.append(
                        f"{i}. **{repo['full_name']}** ⭐ {repo['stargazers_count']:,}\n"
                        f"   URL: {repo['html_url']}\n"
                        f"   Language: {repo.get('language', 'N/A')}\n"
                        f"   Topics: {topics}\n"
                        f"   Description: {repo.get('description', 'No description')[:200] if repo.get('description') else 'No description'}"
                    )
                
                return "\n\n".join(output_parts)
                
        except Exception as e:
            return f"Error searching GitHub: {str(e)}"
    
    tools.append(github_search)
    logger.info("Initialized GitHub Search tool")
    
    # 6. DuckDuckGo Search Tool (Fallback web search)
    @tool
    def web_search(query: str, max_results: int = 5) -> str:
        """
        Search the web using DuckDuckGo as a fallback search engine.
        Use this tool when Tavily is not available or for additional search coverage.
        
        Args:
            query: Search query string
            max_results: Maximum number of results (default: 5)
        
        Returns:
            Search results with titles, URLs, and snippets
        """
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            
            wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results)
            search = DuckDuckGoSearchResults(api_wrapper=wrapper)
            
            results = search.run(query)
            return f"**Web Search Results:**\n\n{results}"
            
        except ImportError:
            return "DuckDuckGo search not available. Please use tavily_search instead."
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    tools.append(web_search)
    logger.info("Initialized DuckDuckGo Search tool")
    
    logger.info(f"Created {len(tools)} LangChain research tools")
    return tools


# ============= ReAct Prompt =============

REACT_SYSTEM_PROMPT = """You are an expert AI Research Agent. Your task is to conduct comprehensive research on AI/ML topics using available tools.

## Your Research Process (ReAct Pattern)

You must follow the ReAct (Reasoning + Acting) pattern for each step:

**Thought**: First, analyze what information you need and plan your next action.
Think about:
- What do I already know about this topic?
- What gaps remain in my understanding?
- Which tool would be most effective for getting the needed information?

**Action**: Then, use one of the available tools to gather information.

**Observation**: After receiving the tool's output, reflect on what you learned and decide next steps.

## Available Tools

1. **tavily_search**: AI-powered web search - best for current information, tutorials, documentation
2. **arxiv_search**: Academic paper search - best for research papers, theoretical foundations
3. **wikipedia_search**: Wikipedia search - best for background, history, and general context
4. **scrape_webpage**: Load specific URLs - use to get detailed content from found pages
5. **github_search**: GitHub repository search - best for code implementations and libraries
6. **web_search**: DuckDuckGo fallback search - use if Tavily unavailable

## Research Strategy

For **{category}** topics:
{category_guidelines}

Target Audience: **{target_audience}**
- Beginner: Focus on intuitive explanations and analogies
- Practitioner: Balance theory with practical implementation
- Expert: Deep technical details and cutting-edge research

## Research Checklist

Ensure comprehensive coverage:
1. ☐ **Core Concept**: What is it? How does it work?
2. ☐ **Key Terminology**: Important terms and definitions
3. ☐ **Mathematical Foundations**: Formulas and theory (if applicable)
4. ☐ **Historical Context**: Origin, key milestones, important researchers
5. ☐ **Implementation**: Code examples, libraries, practical guidance
6. ☐ **Sources**: At least 5-10 authoritative references

## Important Rules

1. Use multiple tools to cross-verify information
2. Prioritize authoritative sources (papers, official docs)
3. Extract specific facts, not just general summaries
4. Maximum {max_iterations} tool calls allowed
5. Stop when you have comprehensive coverage

## Output Format

After gathering enough information, provide a synthesis. Always think step by step.

Begin your research now."""

CATEGORY_GUIDELINES = {
    "core_ai": """- Use arxiv_search to find foundational papers
- Use wikipedia_search for historical context
- Use tavily_search for explanations and tutorials
- Use github_search for canonical implementations
- Focus on mathematical formulations and theoretical foundations""",
    
    "practical_implementation": """- Use github_search to find working code examples
- Use tavily_search for tutorials and best practices
- Use arxiv_search for recent applied research
- Focus on production-ready implementations
- Include deployment and scaling considerations"""
}


# ============= ReAct Research Agent =============

class ReActResearchAgent:
    """
    LangGraph-based ReAct agent for deep research
    Uses LangChain's built-in tools with Thought → Action → Observation loop
    """
    
    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize the ReAct research agent with LangChain tools
        
        Args:
            llm: Language model for reasoning
            max_iterations: Maximum number of tool calls
        """
        self.llm = llm or BedrockLLM()
        self.max_iterations = max_iterations
        
        # Create LangChain tools
        self.tools = create_langchain_tools()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"Initialized ReActResearchAgent with {len(self.tools)} LangChain tools")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph for ReAct agent"""
        
        # Bind tools to LLM
        llm_with_tools = self.llm.llm.bind_tools(self.tools)
        
        # Define the agent node
        async def agent_node(state: AgentState) -> Dict[str, Any]:
            """The agent reasons and decides on actions"""
            
            # Check iteration limit
            if state["iteration_count"] >= state["max_iterations"]:
                logger.info("Reached maximum iterations, synthesizing results")
                return {
                    "messages": [AIMessage(content="Maximum iterations reached. Synthesizing collected research...")],
                    "is_complete": True,
                }
            
            # Build system prompt with context
            category = state.get("category", "core_ai")
            category_guidelines = CATEGORY_GUIDELINES.get(category, CATEGORY_GUIDELINES["core_ai"])
            
            system_prompt = REACT_SYSTEM_PROMPT.format(
                category=category,
                category_guidelines=category_guidelines,
                target_audience=state.get("target_audience", "practitioner"),
                max_iterations=state["max_iterations"],
            )
            
            # Call LLM with tool binding
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = await llm_with_tools.ainvoke(messages)
            
            # Log the thought process
            if response.content:
                logger.debug(f"Agent thought: {response.content[:200]}...")
            
            return {
                "messages": [response],
                "iteration_count": state["iteration_count"] + 1,
            }
        
        # Define the tool execution node using LangGraph's ToolNode
        tool_node = ToolNode(self.tools)
        
        async def tools_node(state: AgentState) -> Dict[str, Any]:
            """Execute tools and track sources"""
            last_message = state["messages"][-1]
            
            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return {"messages": []}
            
            # Execute tools using ToolNode
            tool_messages = []
            new_sources = []
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                logger.info(f"Executing LangChain tool: {tool_name} with args: {tool_args}")
                
                # Find and execute the tool
                for t in self.tools:
                    if t.name == tool_name:
                        try:
                            # Execute tool (sync or async)
                            if hasattr(t, 'ainvoke'):
                                result = await t.ainvoke(tool_args)
                            else:
                                result = t.invoke(tool_args)
                            
                            # Extract and track sources from tool results
                            extracted_sources = self._extract_sources_from_result(
                                tool_name, tool_args, result
                            )
                            new_sources.extend(extracted_sources)
                            
                            tool_messages.append(
                                ToolMessage(
                                    content=str(result),
                                    tool_call_id=tool_call["id"],
                                )
                            )
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            tool_messages.append(
                                ToolMessage(
                                    content=f"Error: {str(e)}",
                                    tool_call_id=tool_call["id"],
                                )
                            )
                        break
            
            return {
                "messages": tool_messages,
                "sources": new_sources,
            }
        
        # Define routing logic
        def should_continue(state: AgentState) -> Literal["tools", "synthesize", END]:
            """Determine next step based on agent's response"""
            
            if state.get("is_complete"):
                return END  # Already synthesized
            
            last_message = state["messages"][-1]
            
            # If there are tool calls, execute them
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            
            # If reached max iterations or have enough data, synthesize
            if state["iteration_count"] >= state["max_iterations"]:
                logger.info(f"Max iterations reached ({state['iteration_count']}), synthesizing...")
                return "synthesize"
            
            if len(state.get("sources", [])) >= 3:
                logger.info(f"Collected {len(state.get('sources', []))} sources, synthesizing...")
                return "synthesize"
            
            # If no more tool calls but we have some data, synthesize anyway
            if state["iteration_count"] >= 2:
                logger.info("No more tool calls, synthesizing with available data...")
                return "synthesize"
            
            # Otherwise, synthesize (don't leave without synthesis)
            return "synthesize"
        
        # Synthesis node
        async def synthesize_node(state: AgentState) -> Dict[str, Any]:
            """Synthesize all collected research into final output"""
            
            logger.info(f"Synthesizing research with {len(state.get('sources', []))} sources...")
            
            # Build context from collected sources
            sources_summary = ""
            for i, src in enumerate(state.get("sources", [])[:10], 1):
                sources_summary += f"\n{i}. {src.get('title', 'Source')} - {src.get('url', '')}"
            
            synthesis_prompt = f"""Based on all the research you've gathered, synthesize a comprehensive research report.

Query: {state['query']}
Category: {state['category']}
Target Audience: {state['target_audience']}

Sources collected:{sources_summary}

Provide your response as a JSON object with the following structure:
{{
    "topic_summary": "A comprehensive summary of the topic (500-1000 words). Be thorough and informative.",
    "key_concepts": {{
        "concept_name": "detailed explanation",
        "another_concept": "another explanation"
    }},
    "mathematical_foundations": "Key formulas and mathematical concepts (if applicable, otherwise null)",
    "historical_context": "Origin, key milestones, and important researchers",
    "implementation_examples": "Code examples and practical implementation guidance (if applicable)"
}}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, just the raw JSON object."""
            
            messages = state["messages"] + [HumanMessage(content=synthesis_prompt)]
            
            try:
                response = await self.llm.llm.ainvoke(messages)
                logger.info(f"Synthesis response received: {len(response.content)} chars")
                
                return {
                    "messages": [response],
                    "is_complete": True,
                }
            except Exception as e:
                logger.error(f"Synthesis LLM call failed: {e}")
                # Return a fallback response
                fallback_content = json.dumps({
                    "topic_summary": f"Research on: {state['query']}. Unable to synthesize due to an error.",
                    "key_concepts": {"query": state['query']},
                    "mathematical_foundations": None,
                    "historical_context": None,
                    "implementation_examples": None,
                })
                return {
                    "messages": [AIMessage(content=fallback_content)],
                    "is_complete": True,
                }
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tools_node)
        workflow.add_node("synthesize", synthesize_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "synthesize": "synthesize",
                END: END,
            }
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("synthesize", END)
        
        # Compile with memory checkpointer
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def conduct_research(
        self,
        query: str,
        category: TopicCategory,
        target_audience: str = "practitioner",
    ) -> ResearchOutput:
        """
        Conduct comprehensive research using ReAct agent with LangChain tools
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience level
        
        Returns:
            ResearchOutput with synthesized research
        """
        logger.info(f"Starting ReAct research with LangChain tools: {query[:100]}...")
        
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=f"Research the following topic thoroughly: {query}")],
            "query": query,
            "category": category.value,
            "target_audience": target_audience,
            "research_data": {},
            "sources": [],
            "iteration_count": 0,
            "max_iterations": self.max_iterations,
            "is_complete": False,
        }
        
        # Run the agent
        config = {"configurable": {"thread_id": f"research_{datetime.now().timestamp()}"}}
        
        # Accumulate state across all stream events
        accumulated_sources = []
        all_messages = []
        synthesis_content = ""
        
        async for state in self.graph.astream(initial_state, config):
            # Log and accumulate from each node's output
            for node_name, node_state in state.items():
                if isinstance(node_state, dict):
                    # Accumulate sources
                    if "sources" in node_state and node_state["sources"]:
                        accumulated_sources.extend(node_state["sources"])
                        logger.debug(f"[{node_name}] Collected {len(node_state['sources'])} sources")
                    
                    # Collect messages
                    if "messages" in node_state and node_state["messages"]:
                        for msg in node_state["messages"]:
                            if hasattr(msg, "content") and msg.content:
                                all_messages.append(msg.content)
                                # Check if this looks like synthesis output (JSON with topic_summary)
                                if '"topic_summary"' in msg.content:
                                    synthesis_content = msg.content
                                    logger.info(f"[{node_name}] Got synthesis response")
                                else:
                                    logger.debug(f"[{node_name}] {msg.content[:100]}...")
        
        # Extract final response
        research_output = self._parse_final_output(
            synthesis_content, accumulated_sources, all_messages, query, category
        )
        
        # Save research data
        research_output.research_data_path = await self._save_research_data(
            query, research_output
        )
        
        logger.info(
            f"ReAct research completed with {len(research_output.sources)} sources "
            f"and completeness score {research_output.completeness_score:.2f}"
        )
        
        return research_output
    
    def _parse_final_output(
        self,
        synthesis_content: str,
        accumulated_sources: List[Dict],
        all_messages: List[str],
        query: str,
        category: TopicCategory,
    ) -> ResearchOutput:
        """Parse the final state into ResearchOutput"""
        
        logger.info(f"Parsing output: synthesis={len(synthesis_content)} chars, sources={len(accumulated_sources)}")
        
        # Parse JSON from synthesis
        data = {}
        try:
            if synthesis_content:
                json_start = synthesis_content.find("{")
                json_end = synthesis_content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = synthesis_content[json_start:json_end]
                    data = json.loads(json_str)
                    logger.info(f"Successfully parsed synthesis JSON with keys: {list(data.keys())}")
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse synthesis JSON: {e}")
        
        # Fallback: if no synthesis, create summary from collected research
        if not data.get("topic_summary"):
            logger.warning("No synthesis content, creating fallback from research data")
            # Combine message content for a basic summary
            combined_research = "\n".join([m for m in all_messages if len(m) > 50][:5])
            data = {
                "topic_summary": f"Research on: {query}\n\n{combined_research[:2000] if combined_research else 'Research data collected.'}",
                "key_concepts": {"research_query": query},
            }
        
        # Deduplicate sources
        unique_sources = []
        seen_urls = set()
        for source in accumulated_sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
            elif not url:
                unique_sources.append(source)
        
        output = ResearchOutput(
            topic_summary=data.get("topic_summary", ""),
            key_concepts=data.get("key_concepts", {}),
            mathematical_foundations=data.get("mathematical_foundations"),
            historical_context=data.get("historical_context"),
            implementation_examples=data.get("implementation_examples"),
            sources=unique_sources,
        )
        
        output.completeness_score = self._calculate_completeness(output, category)
        
        logger.info(f"Research output: summary={len(output.topic_summary)} chars, concepts={len(output.key_concepts)}, sources={len(output.sources)}")
        
        return output
    
    def _calculate_completeness(
        self,
        research: ResearchOutput,
        category: TopicCategory,
    ) -> float:
        """Calculate research completeness score based on category"""
        score = 0.0
        max_score = 0.0
        
        # Base requirements for all categories
        max_score += 3.0
        if research.topic_summary and len(research.topic_summary) > 100:
            score += 1.0
        if research.key_concepts and len(research.key_concepts) >= 2:
            score += 1.0
        if len(research.sources) >= 5:
            score += 1.0
        elif len(research.sources) >= 3:
            score += 0.5
        
        # Category-specific requirements
        if category == TopicCategory.CORE_AI:
            # Core AI needs math, history, and examples
            max_score += 3.0
            if research.mathematical_foundations and len(research.mathematical_foundations) > 50:
                score += 1.0
            if research.historical_context and len(research.historical_context) > 50:
                score += 1.0
            if research.implementation_examples and len(research.implementation_examples) > 50:
                score += 1.0
        elif category == TopicCategory.PRACTICAL_IMPLEMENTATION:
            # Practical AI needs code examples
            max_score += 2.0
            if research.implementation_examples and len(research.implementation_examples) > 100:
                score += 1.5
            if len(research.sources) >= 3:
                score += 0.5
        elif category in [TopicCategory.SOFTWARE_DEVELOPMENT, TopicCategory.WEB_DEVELOPMENT]:
            # Software dev needs code and best practices
            max_score += 2.0
            if research.implementation_examples and len(research.implementation_examples) > 100:
                score += 1.0
            if research.key_concepts and len(research.key_concepts) >= 3:
                score += 1.0
        elif category == TopicCategory.DEVOPS:
            # DevOps needs practical examples and tools
            max_score += 2.0
            if research.implementation_examples and len(research.implementation_examples) > 50:
                score += 1.0
            if len(research.sources) >= 3:
                score += 1.0
        else:
            # General tech - flexible requirements
            max_score += 1.5
            if research.implementation_examples or research.historical_context:
                score += 1.0
            if len(research.sources) >= 2:
                score += 0.5
        
        return min(score / max_score, 1.0)
    
    def _extract_sources_from_result(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Any,
    ) -> List[Dict[str, Any]]:
        """Extract source information from tool results"""
        sources = []
        query = tool_args.get("query", "") if isinstance(tool_args, dict) else str(tool_args)
        
        try:
            # Handle different tool result formats
            if tool_name == "tavily_search":
                # Tavily returns list of results
                if isinstance(result, list):
                    for item in result[:5]:  # Top 5 results
                        if isinstance(item, dict):
                            sources.append({
                                "type": "web",
                                "title": item.get("title", "Web Article"),
                                "url": item.get("url", ""),
                                "tool": tool_name,
                                "query": query,
                            })
                        elif isinstance(item, str):
                            sources.append({
                                "type": "web",
                                "title": f"Result for: {query[:50]}",
                                "url": "",
                                "tool": tool_name,
                                "query": query,
                            })
                            break
                elif isinstance(result, str):
                    sources.append({
                        "type": "web",
                        "title": f"Search: {query[:50]}",
                        "url": "",
                        "tool": tool_name,
                        "query": query,
                    })
                    
            elif tool_name == "arxiv_search":
                # ArXiv returns formatted string or list
                result_str = str(result)
                if "Title:" in result_str:
                    # Parse arxiv result format
                    lines = result_str.split("\n")
                    current_source = {"type": "paper", "tool": tool_name}
                    for line in lines:
                        if line.startswith("Title:"):
                            current_source["title"] = line.replace("Title:", "").strip()
                        elif line.startswith("Authors:"):
                            # Parse authors as a list (split by comma)
                            authors_str = line.replace("Authors:", "").strip()
                            current_source["authors"] = [a.strip() for a in authors_str.split(",") if a.strip()]
                        elif line.startswith("Published:"):
                            current_source["published"] = line.replace("Published:", "").strip()
                        elif line.startswith("Summary:"):
                            if "title" in current_source:
                                sources.append(current_source.copy())
                                current_source = {"type": "paper", "tool": tool_name}
                    if "title" in current_source:
                        sources.append(current_source)
                else:
                    sources.append({
                        "type": "paper",
                        "title": f"ArXiv: {query[:50]}",
                        "tool": tool_name,
                        "query": query,
                    })
                    
            elif tool_name == "wikipedia_search":
                # Wikipedia returns text content
                sources.append({
                    "type": "encyclopedia",
                    "title": f"Wikipedia: {query}",
                    "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    "tool": tool_name,
                    "query": query,
                })
                
            elif tool_name == "github_search":
                # GitHub search returns list or string
                if isinstance(result, list):
                    for item in result[:3]:
                        if isinstance(item, dict):
                            sources.append({
                                "type": "github",
                                "title": item.get("name", item.get("full_name", "GitHub Repo")),
                                "url": item.get("html_url", item.get("url", "")),
                                "tool": tool_name,
                            })
                else:
                    sources.append({
                        "type": "github",
                        "title": f"GitHub: {query[:50]}",
                        "tool": tool_name,
                        "query": query,
                    })
                    
            elif tool_name in ["web_search", "scrape_webpage"]:
                url = tool_args.get("url", "") if isinstance(tool_args, dict) else ""
                sources.append({
                    "type": "web",
                    "title": f"Web: {query[:50] or url[:50]}",
                    "url": url or "",
                    "tool": tool_name,
                    "query": query,
                })
            else:
                # Generic source
                sources.append({
                    "type": "web",
                    "title": f"{tool_name}: {query[:50]}",
                    "tool": tool_name,
                    "query": query,
                })
                
        except Exception as e:
            logger.warning(f"Error extracting sources from {tool_name}: {e}")
            sources.append({
                "type": "web",
                "title": f"{tool_name}: {query[:50]}",
                "tool": tool_name,
                "query": query,
            })
        
        return sources
    
    async def _save_research_data(
        self,
        query: str,
        research_output: ResearchOutput,
    ) -> str:
        """Save research data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:50])
            filename = f"{timestamp}_{safe_query}.json"
            
            research_dir = config.RESEARCH_DIR / "summaries"
            research_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = research_dir / filename
            
            data = {
                "query": query,
                "agent_type": "react_langchain",
                "tools_used": [t.name for t in self.tools],
                "topic_summary": research_output.topic_summary,
                "key_concepts": research_output.key_concepts,
                "mathematical_foundations": research_output.mathematical_foundations,
                "historical_context": research_output.historical_context,
                "implementation_examples": research_output.implementation_examples,
                "sources": research_output.sources,
                "completeness_score": research_output.completeness_score,
                "created_at": datetime.now().isoformat(),
            }
            
            filepath.write_text(json.dumps(data, indent=2, default=str))
            
            logger.debug(f"Saved research data to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save research data: {e}")
            return ""
    
    async def close(self):
        """Cleanup resources"""
        pass  # LangChain tools handle their own cleanup


def get_react_research_agent(
    llm: Optional[BedrockLLM] = None,
    max_iterations: int = 10,
) -> ReActResearchAgent:
    """Factory function to create ReActResearchAgent"""
    return ReActResearchAgent(llm=llm, max_iterations=max_iterations)
