"""
Content Generation Page
Generate blogs, apply branding, and manage content
"""
import streamlit as st
import json
from utils.styles import status_badge


def render():
    """Render the content generation page"""
    
    st.markdown("# ✍️ Content Generation")
    st.markdown("*Transform research into publication-ready content*")
    
    st.divider()
    
    api = st.session_state.api_client
    
    # ============= Tabs =============
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Generate Blog", "🎨 Branding", "📚 Library", "🚀 Full Pipeline"])
    
    # ============= Generate Blog Tab =============
    with tab1:
        st.markdown("### Generate Blog from Research")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            research_id = st.number_input(
                "Research Query ID",
                min_value=1,
                value=st.session_state.get("selected_research_id", 1),
                help="Enter the ID of a completed research query"
            )
        
        with col2:
            # Quick lookup
            if st.button("🔍 Check Research", use_container_width=True):
                try:
                    result = api.get_research_query(research_id)
                    if result.get("status") == "completed":
                        st.success(f"✅ Ready: {result.get('query_text', '')[:50]}...")
                    else:
                        st.warning(f"Status: {result.get('status')}")
                except:
                    st.error("Research not found")
        
        st.divider()
        
        with st.form("blog_generation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                target_audience = st.selectbox(
                    "Target Audience",
                    options=["beginner", "practitioner", "expert"],
                    index=1,
                    help="Adjusts complexity and depth of content"
                )
            
            with col2:
                tone = st.selectbox(
                    "Writing Tone",
                    options=["professional", "conversational", "technical", "casual"],
                    index=0,
                    help="Sets the voice and style of the blog"
                )
            
            generate_linkedin = st.checkbox(
                "Also generate LinkedIn post",
                value=True,
                help="Creates a LinkedIn post alongside the blog"
            )
            
            submit = st.form_submit_button("✍️ Generate Blog", use_container_width=True, type="primary")
        
        if submit:
            with st.spinner("📝 Generating blog... This may take a minute."):
                progress = st.progress(0, text="Starting generation...")
                
                try:
                    progress.progress(30, text="Generating content...")
                    
                    result = api.generate_blog(
                        research_query_id=research_id,
                        target_audience=target_audience,
                        tone=tone,
                        generate_linkedin_post=generate_linkedin,
                    )
                    
                    progress.progress(100, text="Complete!")
                    
                    st.success("✅ Blog generated successfully!")
                    
                    # Display blog
                    st.markdown(f"### {result.get('title', 'Untitled')}")
                    
                    with st.expander("📖 Full Content", expanded=True):
                        st.markdown(result.get("content", "No content"))
                    
                    # LinkedIn post
                    if result.get("linkedin_post"):
                        with st.expander("📱 LinkedIn Post", expanded=True):
                            st.markdown(result.get("linkedin_post"))
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Content ID", result.get("content_id", "N/A"))
                    
                    with col2:
                        st.download_button(
                            "📥 Download Blog",
                            data=result.get("content", ""),
                            file_name=f"blog_{result.get('content_id', 'draft')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )
                    
                    with col3:
                        if result.get("file_path"):
                            st.write(f"📁 Saved to: `{result.get('file_path')}`")
                    
                    # Store for later
                    st.session_state.last_blog = result
                    
                except Exception as e:
                    progress.empty()
                    st.error(f"Generation failed: {e}")
    
    # ============= Branding Tab =============
    with tab2:
        st.markdown("### Brand Voice Tools")
        st.markdown("Apply consistent brand voice and check content alignment")
        
        subtab1, subtab2, subtab3 = st.tabs(["Apply Branding", "Check Alignment", "Style Suggestions"])
        
        with subtab1:
            st.markdown("#### Apply Brand Voice")
            
            content_input = st.text_area(
                "Content to Brand",
                height=200,
                placeholder="Paste your content here...",
                help="Enter the content you want to apply branding to"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                brand_audience = st.selectbox(
                    "Target Audience",
                    options=["beginner", "practitioner", "expert"],
                    index=1,
                    key="brand_audience"
                )
            
            with col2:
                content_type = st.selectbox(
                    "Content Type",
                    options=["blog", "linkedin_post", "email", "documentation"],
                    index=0,
                )
            
            if st.button("🎨 Apply Branding", type="primary", use_container_width=True):
                if content_input:
                    with st.spinner("Applying brand voice..."):
                        try:
                            result = api.apply_branding(
                                content=content_input,
                                target_audience=brand_audience,
                                content_type=content_type,
                            )
                            
                            # Voice score
                            score = result.get("voice_score", 0)
                            score_color = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🔴"
                            st.metric(f"{score_color} Voice Score", f"{score:.0%}")
                            
                            # Branded content
                            st.markdown("#### Branded Content")
                            st.markdown(result.get("branded_content", ""))
                            
                            # Changes made
                            changes = result.get("changes_made", [])
                            if changes:
                                with st.expander(f"📝 Changes Made ({len(changes)})"):
                                    for change in changes:
                                        st.markdown(f"- {change}")
                            
                            # Suggestions
                            suggestions = result.get("suggestions", [])
                            if suggestions:
                                with st.expander("💡 Suggestions"):
                                    for suggestion in suggestions:
                                        st.markdown(f"- {suggestion}")
                            
                            # Copy button
                            st.download_button(
                                "📋 Download Branded Content",
                                data=result.get("branded_content", ""),
                                file_name="branded_content.md",
                                mime="text/markdown",
                            )
                            
                        except Exception as e:
                            st.error(f"Branding failed: {e}")
                else:
                    st.warning("Please enter content to brand")
        
        with subtab2:
            st.markdown("#### Check Voice Alignment")
            
            check_content = st.text_area(
                "Content to Check",
                height=150,
                placeholder="Paste content to analyze...",
                key="check_content"
            )
            
            check_audience = st.selectbox(
                "Target Audience",
                options=["beginner", "practitioner", "expert"],
                index=1,
                key="check_audience"
            )
            
            if st.button("🔍 Check Alignment", use_container_width=True):
                if check_content:
                    with st.spinner("Analyzing content..."):
                        try:
                            result = api.check_voice_alignment(
                                content=check_content,
                                target_audience=check_audience,
                            )
                            
                            # Score display
                            score = result.get("alignment_score", 0)
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Alignment", f"{score:.0%}")
                            with col2:
                                tone_match = "✅" if result.get("tone_match") else "❌"
                                st.metric("Tone Match", tone_match)
                            with col3:
                                style_match = "✅" if result.get("style_match") else "❌"
                                st.metric("Style Match", style_match)
                            with col4:
                                audience_ok = "✅" if result.get("audience_appropriate") else "❌"
                                st.metric("Audience Fit", audience_ok)
                            
                            # Issues and strengths
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### ⚠️ Issues")
                                for issue in result.get("issues", []):
                                    st.markdown(f"- {issue}")
                            
                            with col2:
                                st.markdown("#### ✅ Strengths")
                                for strength in result.get("strengths", []):
                                    st.markdown(f"- {strength}")
                            
                            # Recommendations
                            st.markdown("#### 💡 Recommendations")
                            for rec in result.get("recommendations", []):
                                st.markdown(f"- {rec}")
                            
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")
                else:
                    st.warning("Please enter content to check")
        
        with subtab3:
            st.markdown("#### Get Style Suggestions")
            
            style_content = st.text_area(
                "Content to Analyze",
                height=150,
                placeholder="Paste content for style suggestions...",
                key="style_content"
            )
            
            if st.button("💡 Get Suggestions", use_container_width=True):
                if style_content:
                    with st.spinner("Generating suggestions..."):
                        try:
                            result = api.get_style_suggestions(style_content)
                            
                            st.markdown("#### Style Improvement Suggestions")
                            for i, suggestion in enumerate(result.get("suggestions", []), 1):
                                st.markdown(f"**{i}.** {suggestion}")
                            
                        except Exception as e:
                            st.error(f"Failed to get suggestions: {e}")
                else:
                    st.warning("Please enter content to analyze")
    
    # ============= Library Tab =============
    with tab3:
        st.markdown("### Content Library")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh", key="refresh_library", use_container_width=True):
                st.rerun()
        
        try:
            blogs = api.get_blogs(limit=20)
            
            if blogs:
                for blog in blogs:
                    with st.expander(f"📝 {blog.get('title', 'Untitled')[:50]}..."):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ID:** {blog.get('id')}")
                            st.write(f"**Audience:** {blog.get('target_audience')}")
                        
                        with col2:
                            st.write(f"**Tone:** {blog.get('tone', 'N/A')}")
                            st.write(f"**Status:** {blog.get('status')}")
                        
                        with col3:
                            st.write(f"**Created:** {blog.get('created_at', 'N/A')[:10]}")
                        
                        st.divider()
                        
                        # Content preview
                        content = blog.get("content", "")
                        st.markdown(content[:500] + "..." if len(content) > 500 else content)
                        
                        # Actions
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "📥 Download",
                                data=content,
                                file_name=f"blog_{blog.get('id')}.md",
                                mime="text/markdown",
                                key=f"dl_{blog.get('id')}",
                                use_container_width=True,
                            )
                        with col2:
                            if st.button("📱 Create Social", key=f"social_{blog.get('id')}", use_container_width=True):
                                st.session_state.selected_content_id = blog.get('id')
                                st.session_state.current_page = "Social"
                                st.rerun()
            else:
                st.info("No blogs in library yet. Generate some content to see it here!")
                
        except Exception as e:
            st.error(f"Failed to load library: {e}")
    
    # ============= Full Pipeline Tab =============
    with tab4:
        st.markdown("### Full Pipeline Execution")
        st.markdown("Execute the complete workflow: **Research → Blog → Branding → Social**")
        
        st.info("💡 This runs the entire content generation pipeline in one click!")
        
        with st.form("full_pipeline_form"):
            query = st.text_area(
                "Research Query",
                placeholder="e.g., Explain how large language models handle context windows",
                height=100,
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                audience = st.selectbox(
                    "Target Audience",
                    options=["beginner", "practitioner", "expert"],
                    index=1,
                    key="pipeline_audience"
                )
            
            with col2:
                tone = st.selectbox(
                    "Tone",
                    options=["professional", "conversational", "technical"],
                    index=0,
                    key="pipeline_tone"
                )
            
            with col3:
                gen_social = st.checkbox("Generate Social Content", value=True)
            
            submit = st.form_submit_button(
                "🚀 Execute Full Pipeline",
                use_container_width=True,
                type="primary"
            )
        
        if submit and query:
            with st.spinner("🔬 Executing full pipeline... This may take several minutes."):
                progress = st.progress(0, text="Starting pipeline...")
                
                try:
                    progress.progress(10, text="Researching topic...")
                    
                    result = api.execute_full_pipeline(
                        query_text=query,
                        target_audience=audience,
                        tone=tone,
                        generate_social=gen_social,
                    )
                    
                    progress.progress(100, text="Pipeline complete!")
                    
                    st.balloons()
                    st.success("🎉 Full pipeline completed successfully!")
                    
                    # Results summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Research ID", result.get("research_query_id"))
                    with col2:
                        st.metric("Content ID", result.get("content_id"))
                    with col3:
                        score = result.get("completeness_score", 0)
                        st.metric("Completeness", f"{score:.0%}")
                    with col4:
                        time = result.get("execution_time_seconds", 0)
                        st.metric("Time", f"{time:.1f}s")
                    
                    st.markdown(f"### 📝 {result.get('blog_title', 'Generated Blog')}")
                    
                    # Load and display blog
                    try:
                        blog = api.get_blog(result.get("content_id"))
                        with st.expander("📖 View Full Blog", expanded=True):
                            st.markdown(blog.get("content", ""))
                    except:
                        pass
                    
                except Exception as e:
                    progress.empty()
                    st.error(f"Pipeline failed: {e}")

