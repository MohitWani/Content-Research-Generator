"""
Social Media Content Page
Generate LinkedIn posts, Twitter threads, and social summaries
"""
import streamlit as st


def render():
    """Render the social media content page"""
    
    st.markdown("# 📱 Social Media")
    st.markdown("*Create engaging social content from your research and blogs*")
    
    st.divider()
    
    api = st.session_state.api_client
    
    # ============= Tabs =============
    tab1, tab2, tab3 = st.tabs(["💼 LinkedIn", "🐦 Twitter/X Thread", "📋 Quick Summary"])
    
    # ============= LinkedIn Tab =============
    with tab1:
        st.markdown("### Generate LinkedIn Post")
        st.markdown("Create engaging LinkedIn posts from your research or blog content")
        
        # Source selection
        source_type = st.radio(
            "Content Source",
            options=["From Research", "From Blog", "Custom Text"],
            horizontal=True,
        )
        
        source_id = None
        custom_content = None
        
        if source_type == "From Research":
            source_id = st.number_input(
                "Research Query ID",
                min_value=1,
                value=st.session_state.get("selected_research_id", 1),
                key="linkedin_research_id"
            )
            source_key = "research_query_id"
        elif source_type == "From Blog":
            source_id = st.number_input(
                "Blog Content ID",
                min_value=1,
                value=st.session_state.get("selected_content_id", 1),
                key="linkedin_blog_id"
            )
            source_key = "content_id"
        else:
            custom_content = st.text_area(
                "Custom Content",
                height=150,
                placeholder="Paste your content here to convert to a LinkedIn post...",
            )
            source_key = "custom_content"
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            audience = st.selectbox(
                "Target Audience",
                options=["beginner", "practitioner", "expert"],
                index=1,
                key="linkedin_audience"
            )
        
        with col2:
            include_hashtags = st.checkbox("Include Hashtags", value=True)
        
        with col3:
            include_cta = st.checkbox("Include Call-to-Action", value=True)
        
        if st.button("📱 Generate LinkedIn Post", type="primary", use_container_width=True):
            with st.spinner("Creating your LinkedIn post..."):
                try:
                    kwargs = {
                        "target_audience": audience,
                        "include_hashtags": include_hashtags,
                        "include_cta": include_cta,
                    }
                    
                    if source_type == "Custom Text":
                        if not custom_content:
                            st.warning("Please enter some content")
                            st.stop()
                        kwargs["custom_content"] = custom_content
                    elif source_type == "From Research":
                        kwargs["research_query_id"] = source_id
                    else:
                        kwargs["content_id"] = source_id
                    
                    result = api.generate_linkedin_post(**kwargs)
                    
                    st.success("✅ LinkedIn post generated!")
                    
                    # Display post
                    st.markdown("### Your LinkedIn Post")
                    
                    # Hook highlight
                    hook = result.get("hook", "")
                    if hook:
                        st.markdown(f"**🎣 Hook:** {hook}")
                        st.divider()
                    
                    # Main content
                    content = result.get("content", "")
                    st.markdown(
                        f'<div style="background: #0a66c2; padding: 1.5rem; border-radius: 12px; color: white; font-size: 1rem; line-height: 1.6; white-space: pre-wrap;">{content}</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Hashtags
                    hashtags = result.get("hashtags", [])
                    if hashtags:
                        st.markdown("**#️⃣ Hashtags:**")
                        hashtag_html = " ".join([f'<span class="hashtag">#{tag}</span>' for tag in hashtags])
                        st.markdown(hashtag_html, unsafe_allow_html=True)
                    
                    # CTA
                    cta = result.get("call_to_action")
                    if cta:
                        st.markdown(f"**📢 Call-to-Action:** {cta}")
                    
                    # Stats
                    st.divider()
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        chars = result.get("character_count", 0)
                        limit = 3000
                        status = "✅" if chars <= limit else "⚠️"
                        st.metric(f"{status} Characters", f"{chars}/{limit}")
                    
                    with col2:
                        st.metric("Audience", result.get("target_audience", "practitioner").title())
                    
                    with col3:
                        if result.get("file_path"):
                            st.write(f"📁 Saved")
                    
                    # Copy button
                    full_post = content
                    if hashtags:
                        full_post += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
                    
                    st.download_button(
                        "📋 Download Post",
                        data=full_post,
                        file_name="linkedin_post.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                    
                except Exception as e:
                    st.error(f"Generation failed: {e}")
    
    # ============= Twitter Tab =============
    with tab2:
        st.markdown("### Generate Twitter/X Thread")
        st.markdown("Create engaging threads that break down complex topics")
        
        # Source selection
        thread_source = st.radio(
            "Content Source",
            options=["From Research", "From Blog", "Custom Text"],
            horizontal=True,
            key="thread_source"
        )
        
        if thread_source == "From Research":
            thread_source_id = st.number_input(
                "Research Query ID",
                min_value=1,
                value=st.session_state.get("selected_research_id", 1),
                key="thread_research_id"
            )
        elif thread_source == "From Blog":
            thread_source_id = st.number_input(
                "Blog Content ID",
                min_value=1,
                value=st.session_state.get("selected_content_id", 1),
                key="thread_blog_id"
            )
        else:
            thread_custom = st.text_area(
                "Custom Content",
                height=150,
                placeholder="Paste your content here to convert to a thread...",
                key="thread_custom"
            )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_posts = st.slider(
                "Number of Posts",
                min_value=3,
                max_value=15,
                value=5,
                help="How many posts should be in the thread"
            )
        
        with col2:
            platform = st.selectbox(
                "Platform",
                options=["twitter", "threads"],
                format_func=lambda x: "Twitter/X" if x == "twitter" else "Threads",
            )
        
        if st.button("🧵 Generate Thread", type="primary", use_container_width=True):
            with st.spinner("Creating your thread..."):
                try:
                    kwargs = {
                        "max_posts": max_posts,
                        "platform": platform,
                    }
                    
                    if thread_source == "Custom Text":
                        if not thread_custom:
                            st.warning("Please enter some content")
                            st.stop()
                        kwargs["custom_content"] = thread_custom
                    elif thread_source == "From Research":
                        kwargs["research_query_id"] = thread_source_id
                    else:
                        kwargs["content_id"] = thread_source_id
                    
                    result = api.generate_twitter_thread(**kwargs)
                    
                    st.success(f"✅ Thread generated with {result.get('total_posts', 0)} posts!")
                    
                    # Display thread
                    st.markdown(f"### 🧵 Thread: {result.get('topic', 'Your Topic')}")
                    
                    posts = result.get("posts", [])
                    
                    for post in posts:
                        position = post.get("position", 1)
                        content = post.get("content", "")
                        char_count = post.get("character_count", 0)
                        
                        # Character limit check
                        limit = 280 if platform == "twitter" else 500
                        status = "✅" if char_count <= limit else "⚠️"
                        
                        st.markdown(f"""
                        <div style="
                            background: #15202b; 
                            border: 1px solid #38444d; 
                            border-radius: 16px; 
                            padding: 1rem 1.25rem; 
                            margin-bottom: 0.75rem;
                            position: relative;
                        ">
                            <div style="color: #8899a6; font-size: 0.8rem; margin-bottom: 0.5rem;">
                                Post {position}/{len(posts)} • {char_count}/{limit} chars {status}
                            </div>
                            <div style="color: white; line-height: 1.5; white-space: pre-wrap;">
                                {content}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Download full thread
                    full_thread = "\n\n---\n\n".join([p.get("content", "") for p in posts])
                    
                    st.download_button(
                        "📋 Download Thread",
                        data=full_thread,
                        file_name="twitter_thread.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                    
                except Exception as e:
                    st.error(f"Generation failed: {e}")
    
    # ============= Quick Summary Tab =============
    with tab3:
        st.markdown("### Quick Social Summary")
        st.markdown("Create a brief, punchy summary for any platform")
        
        summary_content = st.text_area(
            "Content to Summarize",
            height=200,
            placeholder="Paste any content here to create a brief social summary...",
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_length = st.slider(
                "Maximum Characters",
                min_value=100,
                max_value=500,
                value=280,
                step=10,
                help="Twitter: 280, LinkedIn: 3000, etc."
            )
        
        with col2:
            st.markdown("**Character Presets:**")
            preset_col1, preset_col2 = st.columns(2)
            with preset_col1:
                if st.button("Twitter (280)", use_container_width=True):
                    st.session_state.summary_length = 280
                    st.rerun()
            with preset_col2:
                if st.button("LinkedIn (700)", use_container_width=True):
                    st.session_state.summary_length = 700
                    st.rerun()
        
        if st.button("✨ Generate Summary", type="primary", use_container_width=True):
            if summary_content:
                with st.spinner("Summarizing..."):
                    try:
                        result = api.summarize_for_social(
                            content=summary_content,
                            max_length=max_length,
                        )
                        
                        summary = result.get("summary", "")
                        char_count = result.get("character_count", len(summary))
                        
                        st.success("✅ Summary generated!")
                        
                        # Display summary
                        st.markdown(
                            f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; font-size: 1.1rem; line-height: 1.6;">{summary}</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Stats
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Characters", f"{char_count}/{max_length}")
                        with col2:
                            compression = (1 - char_count / len(summary_content)) * 100 if summary_content else 0
                            st.metric("Compression", f"{compression:.0f}%")
                        
                        # Copy
                        st.download_button(
                            "📋 Copy Summary",
                            data=summary,
                            file_name="social_summary.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )
                        
                    except Exception as e:
                        st.error(f"Summarization failed: {e}")
            else:
                st.warning("Please enter content to summarize")
    
    # ============= Tips Sidebar =============
    st.divider()
    
    with st.expander("💡 Social Media Tips"):
        st.markdown("""
        **LinkedIn Best Practices:**
        - Start with a hook that stops the scroll
        - Use white space and short paragraphs
        - Include 3-5 relevant hashtags
        - End with a question or call-to-action
        - Optimal length: 1,300-2,000 characters
        
        **Twitter/X Thread Tips:**
        - First tweet should hook and promise value
        - Each tweet should stand alone but connect
        - Use numbers and bullet points
        - End with a summary and CTA
        - 5-10 tweets is the sweet spot
        
        **General Tips:**
        - Post at optimal times (8-10 AM, 12-1 PM)
        - Engage with comments within first hour
        - Use visuals when possible
        - Be authentic and add personal perspective
        """)

