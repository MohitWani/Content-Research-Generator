"""
Custom CSS Styles for Streamlit UI
Modern, clean aesthetic with dark theme accents
"""
import streamlit as st


def load_custom_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
    /* ============= Global Styles ============= */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-light: #818cf8;
        --primary-dark: #4f46e5;
        --secondary: #10b981;
        --accent: #f59e0b;
        --background: #0f172a;
        --surface: #1e293b;
        --surface-light: #334155;
        --text: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #334155;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --info: #3b82f6;
    }
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* ============= Sidebar ============= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--background) 0%, var(--surface) 100%);
        border-right: 1px solid var(--border);
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: transparent;
        border: 1px solid var(--border);
        color: var(--text);
        font-weight: 500;
        transition: all 0.2s ease;
        border-radius: 8px;
        margin-bottom: 4px;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: var(--surface-light);
        border-color: var(--primary);
        transform: translateX(4px);
    }
    
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: var(--primary);
        border-color: var(--primary);
    }
    
    .logo-container {
        text-align: center;
        padding: 1rem 0;
    }
    
    .logo-container h1 {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .logo-container .tagline {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }
    
    .sidebar-footer {
        position: fixed;
        bottom: 1rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-align: center;
        width: 100%;
    }
    
    /* ============= Cards ============= */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .card:hover {
        border-color: var(--primary);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text);
        margin: 0;
    }
    
    .card-subtitle {
        font-size: 0.85rem;
        color: var(--text-muted);
    }
    
    /* ============= Status Badges ============= */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-success {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .badge-warning {
        background: rgba(245, 158, 11, 0.15);
        color: var(--warning);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    
    .badge-error {
        background: rgba(239, 68, 68, 0.15);
        color: var(--error);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    .badge-info {
        background: rgba(59, 130, 246, 0.15);
        color: var(--info);
        border: 1px solid rgba(59, 130, 246, 0.3);
    }
    
    .badge-pending {
        background: rgba(148, 163, 184, 0.15);
        color: var(--text-muted);
        border: 1px solid rgba(148, 163, 184, 0.3);
    }
    
    /* ============= Metrics ============= */
    .metric-card {
        background: linear-gradient(135deg, var(--surface) 0%, var(--surface-light) 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-light);
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-top: 0.5rem;
    }
    
    /* ============= Content Display ============= */
    .content-preview {
        background: var(--background);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        line-height: 1.6;
        max-height: 300px;
        overflow-y: auto;
    }
    
    .content-full {
        background: var(--background);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.5rem;
        line-height: 1.8;
    }
    
    /* ============= Buttons ============= */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    /* ============= Inputs ============= */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* ============= Tabs ============= */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--surface);
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
    }
    
    /* ============= Progress ============= */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        border-radius: 9999px;
    }
    
    /* ============= Expander ============= */
    .streamlit-expanderHeader {
        background: var(--surface);
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* ============= Tables ============= */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* ============= Dividers ============= */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.5rem 0;
    }
    
    /* ============= Animations ============= */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* ============= Custom Components ============= */
    .stat-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .hashtag {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: var(--primary-light);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .source-link {
        color: var(--info);
        text-decoration: none;
        font-size: 0.85rem;
    }
    
    .source-link:hover {
        text-decoration: underline;
    }
    
    /* ============= Empty States ============= */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--text-muted);
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    /* ============= Tooltips ============= */
    [data-tooltip] {
        position: relative;
        cursor: help;
    }
    
    [data-tooltip]:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: var(--background);
        border: 1px solid var(--border);
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        white-space: nowrap;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Generate HTML for status badge"""
    badge_class = {
        "completed": "badge-success",
        "pending": "badge-pending",
        "processing": "badge-info",
        "failed": "badge-error",
        "ready": "badge-success",
    }.get(status.lower(), "badge-info")
    
    return f'<span class="badge {badge_class}">{status}</span>'


def metric_card(value: str, label: str) -> str:
    """Generate HTML for metric card"""
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def card(title: str, content: str, subtitle: str = "") -> str:
    """Generate HTML for card"""
    subtitle_html = f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="card fade-in">
        <div class="card-header">
            <h3 class="card-title">{title}</h3>
            {subtitle_html}
        </div>
        <div class="card-body">
            {content}
        </div>
    </div>
    """

