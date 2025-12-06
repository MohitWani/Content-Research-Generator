"""
Research Page
Submit queries, view results, and manage research data
"""
import streamlit as st
import json
from utils.styles import status_badge


def render():
    """Render the research page"""
    
    st.markdown("# 🔍 Research")
    st.markdown("*Deep AI research with multi-source data collection*")
    
    st.divider()
    
    api = st.session_state.api_client
    
    # ============= Tabs =============
    tab1, tab2, tab3 = st.tabs(["📝 New Query", "📋 Query History", "📊 Results"])
    
    # ============= New Query Tab =============
    with tab1:
        st.markdown("### Submit Research Query")
        st.markdown("Enter your AI topic to research. The agent will gather information from academic papers, web sources, and code repositories.")
        
        with st.form("research_form"):
            query = st.text_area(
                "Research Query",
                placeholder="e.g., Explain the attention mechanism in transformers and its impact on NLP",
                height=100,
                help="Be specific about what you want to learn. Include context for better results."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                audience = st.selectbox(
                    "Target Audience",
                    options=["beginner", "practitioner", "expert"],
                    index=1,
                    help="This affects the depth and technicality of the research"
                )
            
            with col2:
                content_type = st.selectbox(
                    "Content Type",
                    options=["blog", "linkedin_post", "short_form"],
                    index=0,
                    help="The type of content you plan to generate from this research"
                )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                submit_only = st.form_submit_button(
                    "📥 Submit Query",
                    use_container_width=True,
                )
            
            with col2:
                execute_full = st.form_submit_button(
                    "🚀 Execute Research",
                    use_container_width=True,
                    type="primary"
                )
        
        if submit_only and query:
            with st.spinner("Submitting query..."):
                try:
                    result = api.submit_research_query(
                        query=query,
                        target_audience=audience,
                        content_type=content_type,
                    )
                    st.success(f"✅ Query submitted! ID: {result.get('query_id')}")
                    st.info("The query has been added to the queue. Go to 'Query History' to check status.")
                except Exception as e:
                    st.error(f"Failed to submit query: {e}")
        
        if execute_full and query:
            with st.spinner("🔬 Executing research... This may take a few minutes."):
                progress_bar = st.progress(0, text="Starting research pipeline...")
                
                try:
                    progress_bar.progress(20, text="Categorizing topic...")
                    
                    result = api.execute_research(
                        query=query,
                        target_audience=audience,
                    )
                    
                    progress_bar.progress(100, text="Research complete!")
                    
                    st.success(f"✅ Research completed!")
                    
                    # Show result summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Query ID", result.get("query_id", "N/A"))
                    with col2:
                        st.metric("Category", result.get("topic_category", "N/A"))
                    with col3:
                        score = result.get("completeness_score", 0)
                        st.metric("Completeness", f"{score:.0%}")
                    
                    # Store for later use
                    st.session_state.last_research_id = result.get("query_id")
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"Research failed: {e}")
    
    # ============= Query History Tab =============
    with tab2:
        st.markdown("### Research Query History")
        
        # Filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col2:
            status_filter = st.selectbox(
                "Status",
                options=["all", "completed", "pending", "processing", "failed"],
                index=0,
            )
        
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Get queries
        try:
            status = status_filter if status_filter != "all" else None
            queries = api.get_research_queries(limit=50, status=status)
            
            if queries:
                for query in queries:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{query.get('query_text', 'Unknown')[:60]}...**")
                            st.caption(f"ID: {query.get('id')} • Created: {query.get('created_at', 'N/A')[:19]}")
                        
                        with col2:
                            status = query.get('status', 'pending')
                            status_emoji = {"completed": "✅", "pending": "⏳", "processing": "🔄", "failed": "❌"}.get(status, "❓")
                            st.write(f"{status_emoji} {status.title()}")
                        
                        with col3:
                            st.write(f"🎯 {query.get('target_audience', 'practitioner')}")
                        
                        with col4:
                            if st.button("View", key=f"view_{query.get('id')}", use_container_width=True):
                                st.session_state.selected_query_id = query.get('id')
                        
                        st.divider()
            else:
                st.info("No queries found. Submit a research query to get started!")
                
        except Exception as e:
            st.error(f"Failed to load queries: {e}")
    
    # ============= Results Tab =============
    with tab3:
        st.markdown("### Research Results")
        
        # Query selector
        query_id = st.number_input(
            "Query ID",
            min_value=1,
            value=st.session_state.get("selected_query_id", st.session_state.get("last_research_id", 1)),
            help="Enter the research query ID to view results"
        )
        
        if st.button("🔍 Load Results", type="primary"):
            with st.spinner("Loading research results..."):
                try:
                    result = api.get_research_result(query_id)
                    
                    if result:
                        # Summary section
                        st.markdown("#### 📖 Topic Summary")
                        st.markdown(result.get("topic_summary", "No summary available"))
                        
                        st.divider()
                        
                        # Key concepts
                        if result.get("key_concepts"):
                            st.markdown("#### 🔑 Key Concepts")
                            concepts = result.get("key_concepts", {})
                            
                            if isinstance(concepts, dict):
                                for concept, explanation in concepts.items():
                                    with st.expander(f"**{concept}**"):
                                        st.write(explanation)
                            else:
                                st.write(concepts)
                        
                        # Mathematical foundations
                        if result.get("mathematical_foundations"):
                            st.markdown("#### 📐 Mathematical Foundations")
                            st.markdown(result.get("mathematical_foundations"))
                        
                        # Historical context
                        if result.get("historical_context"):
                            st.markdown("#### 📚 Historical Context")
                            st.markdown(result.get("historical_context"))
                        
                        # Implementation examples
                        if result.get("implementation_examples"):
                            st.markdown("#### 💻 Implementation Examples")
                            st.code(result.get("implementation_examples"), language="python")
                        
                        # Sources
                        if result.get("sources"):
                            st.markdown("#### 📚 Sources")
                            sources = result.get("sources", [])
                            
                            for i, source in enumerate(sources[:10]):
                                if isinstance(source, dict):
                                    title = source.get("title", source.get("tool", f"Source {i+1}"))
                                    url = source.get("url", "")
                                    st.markdown(f"- **{title}**" + (f" ([link]({url}))" if url else ""))
                                else:
                                    st.markdown(f"- {source}")
                        
                        # Metrics
                        st.divider()
                        col1, col2 = st.columns(2)
                        with col1:
                            score = result.get("completeness_score", 0)
                            st.metric("Completeness Score", f"{score:.0%}")
                        with col2:
                            if result.get("research_data_path"):
                                st.write(f"📁 Data: `{result.get('research_data_path')}`")
                        
                        # Actions
                        st.divider()
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✍️ Generate Blog", use_container_width=True, type="primary"):
                                st.session_state.current_page = "Content"
                                st.session_state.selected_research_id = query_id
                                st.rerun()
                        
                        with col2:
                            if st.button("📱 Create LinkedIn Post", use_container_width=True):
                                st.session_state.current_page = "Social"
                                st.session_state.selected_research_id = query_id
                                st.rerun()
                        
                        with col3:
                            # Download raw data
                            st.download_button(
                                "📥 Download JSON",
                                data=json.dumps(result, indent=2, default=str),
                                file_name=f"research_{query_id}.json",
                                mime="application/json",
                                use_container_width=True,
                            )
                    else:
                        st.warning("No results found for this query. The research may still be processing.")
                        
                except Exception as e:
                    st.error(f"Failed to load results: {e}")

