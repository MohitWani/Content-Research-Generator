"""
AI Research Agent - Streamlit UI
Modern, intuitive interface for AI research and content generation
"""
import streamlit as st
from pathlib import Path

# Page config must be first Streamlit command
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import pages after config
from pages import dashboard, research, content, social, settings
from utils.api_client import APIClient
from utils.styles import load_custom_css

# Load custom CSS
load_custom_css()

# Initialize API client in session state
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"


def main():
    """Main application entry point"""
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div class="logo-container">
            <h1>🔬 AI Research</h1>
            <p class="tagline">Deep Research & Content Generation</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        pages = {
            "📊 Dashboard": "Dashboard",
            "🔍 Research": "Research",
            "✍️ Content": "Content",
            "📱 Social": "Social",
            "⚙️ Settings": "Settings",
        }
        
        for label, page in pages.items():
            if st.button(
                label, 
                key=f"nav_{page}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page else "secondary"
            ):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        try:
            queries = st.session_state.api_client.get_research_queries(limit=100)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Queries", len(queries))
            with col2:
                completed = len([q for q in queries if q.get("status") == "completed"])
                st.metric("Completed", completed)
        except:
            st.caption("API not available")
        
        # Footer
        st.markdown("""
        <div class="sidebar-footer">
            <p>v1.0.0 • Built with ❤️</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    page = st.session_state.current_page
    
    if page == "Dashboard":
        dashboard.render()
    elif page == "Research":
        research.render()
    elif page == "Content":
        content.render()
    elif page == "Social":
        social.render()
    elif page == "Settings":
        settings.render()


if __name__ == "__main__":
    main()

