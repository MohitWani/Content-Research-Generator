"""
API Client for Streamlit UI
Wraps all API calls to the FastAPI backend
"""
import os
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API Configuration"""
    base_url: str = os.getenv("API_URL", "http://localhost:8000")
    timeout: int = 120  # Long timeout for research operations


class APIClient:
    """Client for interacting with AI Research Agent API"""
    
    def __init__(self, config: Optional[APIConfig] = None):
        self.config = config or APIConfig()
        self.base_url = self.config.base_url.rstrip("/")
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to API at {self.base_url}")
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out")
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            raise Exception(f"API Error: {error_detail}")
    
    # ============= Health =============
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._request("GET", "/health")
    
    # ============= Research =============
    
    def submit_research_query(
        self,
        query: str,
        target_audience: str = "practitioner",
        content_type: str = "blog",
    ) -> Dict[str, Any]:
        """Submit a new research query"""
        return self._request("POST", "/api/v1/research/query", data={
            "query": query,
            "target_audience": target_audience,
            "content_type": content_type,
        })
    
    def get_research_queries(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get list of research queries"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return self._request("GET", "/api/v1/research/queries", params=params)
    
    def get_research_query(self, query_id: int) -> Dict[str, Any]:
        """Get research query by ID"""
        return self._request("GET", f"/api/v1/research/query/{query_id}")
    
    def get_research_result(self, query_id: int) -> Dict[str, Any]:
        """Get research result for query"""
        return self._request("GET", f"/api/v1/research/query/{query_id}/result")
    
    def execute_research(
        self,
        query: str,
        target_audience: str = "practitioner",
    ) -> Dict[str, Any]:
        """Execute research pipeline"""
        return self._request("POST", "/api/v1/research/execute", data={
            "query": query,
            "target_audience": target_audience,
        })
    
    # ============= Content =============
    
    def generate_blog(
        self,
        research_query_id: int,
        target_audience: str = "practitioner",
        tone: str = "professional",
        generate_linkedin_post: bool = False,
    ) -> Dict[str, Any]:
        """Generate blog from research"""
        return self._request("POST", "/api/v1/content/blog/generate", data={
            "research_query_id": research_query_id,
            "target_audience": target_audience,
            "tone": tone,
            "generate_linkedin_post": generate_linkedin_post,
        })
    
    def get_blog(self, content_id: int) -> Dict[str, Any]:
        """Get blog by content ID"""
        return self._request("GET", f"/api/v1/content/blog/{content_id}")
    
    def get_blogs(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get list of blogs"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return self._request("GET", "/api/v1/content/blogs", params=params)
    
    def get_content_for_query(self, query_id: int) -> List[Dict[str, Any]]:
        """Get all content for a research query"""
        return self._request("GET", f"/api/v1/content/query/{query_id}/content")
    
    # ============= Pipelines =============
    
    def execute_full_pipeline(
        self,
        query_text: str,
        target_audience: str = "practitioner",
        tone: str = "professional",
        generate_social: bool = True,
    ) -> Dict[str, Any]:
        """Execute full pipeline: Research → Blog → Social"""
        return self._request("POST", "/api/v1/pipelines/full", data={
            "query_text": query_text,
            "target_audience": target_audience,
            "tone": tone,
            "generate_social": generate_social,
        })
    
    def get_pipeline_executions(
        self,
        skip: int = 0,
        limit: int = 20,
        pipeline_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get pipeline executions"""
        params = {"skip": skip, "limit": limit}
        if pipeline_type:
            params["pipeline_type"] = pipeline_type
        if status:
            params["status"] = status
        return self._request("GET", "/api/v1/pipelines/executions", params=params)
    
    # ============= Social =============
    
    def generate_linkedin_post(
        self,
        content_id: Optional[int] = None,
        research_query_id: Optional[int] = None,
        custom_content: Optional[str] = None,
        target_audience: str = "practitioner",
        include_hashtags: bool = True,
        include_cta: bool = True,
    ) -> Dict[str, Any]:
        """Generate LinkedIn post"""
        data = {
            "target_audience": target_audience,
            "include_hashtags": include_hashtags,
            "include_cta": include_cta,
        }
        if content_id:
            data["content_id"] = content_id
        if research_query_id:
            data["research_query_id"] = research_query_id
        if custom_content:
            data["custom_content"] = custom_content
        
        return self._request("POST", "/api/v1/social/linkedin", data=data)
    
    def generate_twitter_thread(
        self,
        content_id: Optional[int] = None,
        research_query_id: Optional[int] = None,
        custom_content: Optional[str] = None,
        max_posts: int = 5,
        platform: str = "twitter",
    ) -> Dict[str, Any]:
        """Generate Twitter/X thread"""
        data = {
            "max_posts": max_posts,
            "platform": platform,
        }
        if content_id:
            data["content_id"] = content_id
        if research_query_id:
            data["research_query_id"] = research_query_id
        if custom_content:
            data["custom_content"] = custom_content
        
        return self._request("POST", "/api/v1/social/thread", data=data)
    
    def summarize_for_social(
        self,
        content: str,
        max_length: int = 280,
    ) -> Dict[str, Any]:
        """Create social summary"""
        return self._request("POST", "/api/v1/social/summarize", data={
            "content": content,
            "max_length": max_length,
        })
    
    # ============= Branding =============
    
    def apply_branding(
        self,
        content: str,
        target_audience: str = "practitioner",
        content_type: str = "blog",
    ) -> Dict[str, Any]:
        """Apply brand voice to content"""
        return self._request("POST", "/api/v1/branding/apply", data={
            "content": content,
            "target_audience": target_audience,
            "content_type": content_type,
        })
    
    def check_voice_alignment(
        self,
        content: str,
        target_audience: str = "practitioner",
    ) -> Dict[str, Any]:
        """Check voice alignment"""
        return self._request("POST", "/api/v1/branding/check", data={
            "content": content,
            "target_audience": target_audience,
        })
    
    def get_voice_profile(self) -> Dict[str, Any]:
        """Get voice profile"""
        return self._request("GET", "/api/v1/branding/profile")
    
    def get_style_suggestions(self, content: str) -> Dict[str, Any]:
        """Get style suggestions"""
        return self._request("POST", "/api/v1/branding/suggestions", data={
            "content": content,
        })

