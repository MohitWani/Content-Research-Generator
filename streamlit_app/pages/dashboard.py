"""
Dashboard Page
Overview of research and content generation activities
"""
import streamlit as st
from datetime import datetime
from utils.styles import status_badge, metric_card


def render():
    """Render the dashboard page"""
    
    st.markdown("# 📊 Dashboard")
    st.markdown("*Overview of your AI research and content generation*")
    
    st.divider()
    
    api = st.session_state.api_client
    
    # Check API health
    try:
        health = api.health_check()
        api_status = "🟢 Connected"
    except:
        api_status = "🔴 Disconnected"
        st.error("Cannot connect to API. Make sure the server is running.")
        return
    
    # ============= Metrics Row =============
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        queries = api.get_research_queries(limit=100)
        blogs = api.get_blogs(limit=100)
        
        completed_research = len([q for q in queries if q.get("status") == "completed"])
        pending_research = len([q for q in queries if q.get("status") == "pending"])
        
        with col1:
            st.metric(
                label="Total Queries",
                value=len(queries),
                delta=f"{pending_research} pending"
            )
        
        with col2:
            st.metric(
                label="Completed Research",
                value=completed_research,
                delta=f"{(completed_research/max(len(queries),1)*100):.0f}% done" if queries else "0%"
            )
        
        with col3:
            st.metric(
                label="Blogs Generated",
                value=len(blogs),
            )
        
        with col4:
            st.metric(
                label="API Status",
                value="Online",
                delta="healthy"
            )
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
        return
    
    st.divider()
    
    # ============= Recent Activity =============
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Recent Research Queries")
        
        if queries:
            for query in queries[:5]:
                with st.container():
                    status = query.get("status", "pending")
                    status_emoji = {
                        "completed": "✅",
                        "pending": "⏳",
                        "processing": "🔄",
                        "failed": "❌"
                    }.get(status, "❓")
                    
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">{status_emoji} {query.get('query_text', 'Unknown')[:50]}...</span>
                        </div>
                        <div class="card-subtitle">
                            {status_badge(status)} • 
                            {query.get('target_audience', 'practitioner')} • 
                            ID: {query.get('id')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No research queries yet. Start by submitting a query!")
    
    with col2:
        st.markdown("### ✍️ Recent Content")
        
        if blogs:
            for blog in blogs[:5]:
                with st.container():
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">📝 {blog.get('title', 'Untitled')[:40]}...</span>
                        </div>
                        <div class="card-subtitle">
                            {status_badge(blog.get('status', 'ready'))} • 
                            {blog.get('target_audience', 'practitioner')} • 
                            ID: {blog.get('id')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No content generated yet. Run the full pipeline to create content!")
    
    st.divider()
    
    # ============= Quick Actions =============
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 New Research", use_container_width=True, type="primary"):
            st.session_state.current_page = "Research"
            st.rerun()
    
    with col2:
        if st.button("✍️ Generate Blog", use_container_width=True):
            st.session_state.current_page = "Content"
            st.rerun()
    
    with col3:
        if st.button("📱 Create Social Post", use_container_width=True):
            st.session_state.current_page = "Social"
            st.rerun()
    
    # ============= Pipeline Status =============
    st.divider()
    st.markdown("### 🔄 Recent Pipeline Executions")
    
    try:
        executions = api.get_pipeline_executions(limit=5)
        
        if executions:
            for exe in executions:
                with st.expander(
                    f"{exe.get('pipeline_type', 'Unknown')} - {exe.get('status', 'unknown')}",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**ID:** {exe.get('id')}")
                    with col2:
                        st.write(f"**Status:** {exe.get('status')}")
                    with col3:
                        st.write(f"**Started:** {exe.get('started_at', 'N/A')[:19]}")
                    
                    if exe.get('error_message'):
                        st.error(f"Error: {exe.get('error_message')}")
        else:
            st.info("No pipeline executions yet.")
    except:
        st.info("Pipeline execution history not available.")

