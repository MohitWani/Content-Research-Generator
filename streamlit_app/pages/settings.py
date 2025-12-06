"""
Settings Page
Voice profile, API configuration, and system settings
"""
import streamlit as st


def render():
    """Render the settings page"""
    
    st.markdown("# ⚙️ Settings")
    st.markdown("*Configure your AI Research Agent*")
    
    st.divider()
    
    api = st.session_state.api_client
    
    # ============= Tabs =============
    tab1, tab2, tab3 = st.tabs(["🎨 Voice Profile", "🔌 API Status", "ℹ️ About"])
    
    # ============= Voice Profile Tab =============
    with tab1:
        st.markdown("### Brand Voice Profile")
        st.markdown("View and understand your current brand voice configuration")
        
        try:
            profile = api.get_voice_profile()
            
            # Main profile info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Brand Identity")
                st.markdown(f"""
                <div class="card">
                    <h3 style="margin:0; color: #818cf8;">{profile.get('brand_name', 'AI Insights')}</h3>
                    <p><strong>Tone:</strong> {profile.get('tone', 'N/A')}</p>
                    <p><strong>Style:</strong> {profile.get('style', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### Voice Characteristics")
                characteristics = profile.get("voice_characteristics", {})
                
                for key, value in characteristics.items():
                    # Create a visual indicator
                    if isinstance(value, str):
                        level = {"low": 25, "medium": 50, "high": 75, "very high": 100}.get(value.lower(), 50)
                    else:
                        level = 50
                    
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                    st.progress(level / 100)
            
            st.divider()
            
            # Target audiences
            st.markdown("#### Target Audience Descriptions")
            audiences = profile.get("target_audiences", {})
            
            if audiences:
                cols = st.columns(len(audiences) if audiences else 1)
                for i, (audience, description) in enumerate(audiences.items()):
                    with cols[i % len(cols)]:
                        st.markdown(f"""
                        <div class="card">
                            <h4 style="color: #10b981; margin-bottom: 0.5rem;">
                                👤 {audience.title()}
                            </h4>
                            <p style="font-size: 0.9rem; color: #94a3b8;">
                                {description}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No audience descriptions configured")
            
            st.divider()
            
            # Do's and Don'ts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ✅ Do's")
                do_list = profile.get("do_list", [])
                if do_list:
                    for item in do_list:
                        st.markdown(f"- {item}")
                else:
                    st.info("No guidelines configured")
            
            with col2:
                st.markdown("#### ❌ Don'ts")
                dont_list = profile.get("dont_list", [])
                if dont_list:
                    for item in dont_list:
                        st.markdown(f"- {item}")
                else:
                    st.info("No restrictions configured")
            
            st.divider()
            
            # Get guidelines for each audience
            st.markdown("#### 📋 Full Guidelines by Audience")
            
            selected_audience = st.selectbox(
                "Select Audience",
                options=["beginner", "practitioner", "expert"],
                index=1,
            )
            
            if st.button("📄 Generate Guidelines", use_container_width=True):
                try:
                    from utils.api_client import APIClient
                    # Note: This would need a new endpoint, using mock for now
                    guidelines = f"""
                    **Guidelines for {selected_audience.title()} Audience**
                    
                    Brand: {profile.get('brand_name')}
                    Tone: {profile.get('tone')}
                    Style: {profile.get('style')}
                    
                    Audience Description: {audiences.get(selected_audience, 'General audience')}
                    
                    Voice Characteristics:
                    """
                    for k, v in characteristics.items():
                        guidelines += f"\n- {k}: {v}"
                    
                    st.markdown(guidelines)
                    
                except Exception as e:
                    st.error(f"Failed to generate guidelines: {e}")
            
        except Exception as e:
            st.error(f"Failed to load voice profile: {e}")
            st.info("Make sure the API is running and has a voice profile configured.")
    
    # ============= API Status Tab =============
    with tab2:
        st.markdown("### API Connection Status")
        
        # Connection test
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔄 Test Connection", use_container_width=True):
                st.rerun()
        
        try:
            health = api.health_check()
            
            st.success("✅ API Connected Successfully")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Health Status")
                st.json(health)
            
            with col2:
                st.markdown("#### Configuration")
                st.markdown(f"""
                - **Base URL:** `{api.base_url}`
                - **Timeout:** {api.config.timeout}s
                - **Status:** Online
                """)
            
            st.divider()
            
            # Quick API tests
            st.markdown("#### Quick Tests")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Test Research API", use_container_width=True):
                    try:
                        queries = api.get_research_queries(limit=1)
                        st.success(f"✅ Research API OK ({len(queries)} queries found)")
                    except Exception as e:
                        st.error(f"❌ {e}")
            
            with col2:
                if st.button("✍️ Test Content API", use_container_width=True):
                    try:
                        blogs = api.get_blogs(limit=1)
                        st.success(f"✅ Content API OK ({len(blogs)} blogs found)")
                    except Exception as e:
                        st.error(f"❌ {e}")
            
            with col3:
                if st.button("🎨 Test Branding API", use_container_width=True):
                    try:
                        profile = api.get_voice_profile()
                        st.success(f"✅ Branding API OK")
                    except Exception as e:
                        st.error(f"❌ {e}")
            
        except ConnectionError:
            st.error("❌ Cannot connect to API")
            st.markdown("""
            **Troubleshooting:**
            1. Make sure the API server is running
            2. Check the API URL in environment variables
            3. Verify network connectivity
            
            **To start the API:**
            ```bash
            docker compose up -d
            # or
            uvicorn src.api.main:app --reload
            ```
            """)
        except Exception as e:
            st.error(f"❌ Connection error: {e}")
    
    # ============= About Tab =============
    with tab3:
        st.markdown("### About AI Research Agent")
        
        st.markdown("""
        <div class="card">
            <h2 style="margin: 0; background: linear-gradient(135deg, #6366f1 0%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🔬 AI Research Agent
            </h2>
            <p style="font-size: 1.1rem; margin-top: 0.5rem;">
                Deep research and content generation for AI topics
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🚀 Features")
            st.markdown("""
            - **ReAct Research Agent** - LangGraph-powered research with tool use
            - **Multi-Source Data** - ArXiv, Tavily, Wikipedia, GitHub, Web scraping
            - **Blog Generation** - Transform research into publication-ready content
            - **Brand Voice** - Consistent tone and style across all content
            - **Social Content** - LinkedIn posts and Twitter threads
            - **Full Pipeline** - End-to-end content generation
            """)
        
        with col2:
            st.markdown("#### 🛠️ Tech Stack")
            st.markdown("""
            - **Backend:** FastAPI + Python 3.11
            - **AI:** AWS Bedrock (Claude) + LangChain
            - **Orchestration:** LangGraph
            - **Database:** PostgreSQL + SQLAlchemy
            - **UI:** Streamlit
            - **Deployment:** Docker Compose
            """)
        
        st.divider()
        
        st.markdown("#### 📚 API Endpoints")
        
        endpoints = {
            "Research": [
                ("POST", "/api/v1/research/query", "Submit research query"),
                ("GET", "/api/v1/research/queries", "List all queries"),
                ("POST", "/api/v1/research/execute", "Execute research"),
            ],
            "Content": [
                ("POST", "/api/v1/content/blog/generate", "Generate blog"),
                ("GET", "/api/v1/content/blogs", "List all blogs"),
            ],
            "Social": [
                ("POST", "/api/v1/social/linkedin", "Generate LinkedIn post"),
                ("POST", "/api/v1/social/thread", "Generate thread"),
            ],
            "Branding": [
                ("POST", "/api/v1/branding/apply", "Apply branding"),
                ("GET", "/api/v1/branding/profile", "Get voice profile"),
            ],
            "Pipelines": [
                ("POST", "/api/v1/pipelines/full", "Execute full pipeline"),
            ],
        }
        
        for category, routes in endpoints.items():
            with st.expander(f"📁 {category}"):
                for method, path, description in routes:
                    badge_color = {"GET": "#10b981", "POST": "#3b82f6"}.get(method, "#6366f1")
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="background: {badge_color}; color: white; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">{method}</span>
                        <code style="font-size: 0.85rem;">{path}</code>
                        <span style="color: #94a3b8; font-size: 0.85rem;">- {description}</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("#### 📖 Documentation")
        st.markdown(f"""
        - **API Docs:** [{api.base_url}/docs]({api.base_url}/docs)
        - **Health Check:** [{api.base_url}/health]({api.base_url}/health)
        """)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #64748b;">
            <p>Version 1.0.0 • Built with ❤️</p>
        </div>
        """, unsafe_allow_html=True)

