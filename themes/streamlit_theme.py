import streamlit as st

def apply_custom_theme(primary_color="#90cdec"):
    """
    Apply a custom theme to a Streamlit app.
    
    Args:
        primary_color (str): The primary color in HEX format
    """
    # Derive complementary colors from the primary color
    primary_color_light = f"{primary_color}33"  # 20% opacity for light background
    primary_color_medium = f"{primary_color}66"  # 40% opacity for medium elements
    secondary_color = "#3A6B87"  # Darker shade for secondary elements
    text_color = "#1E3E4F"  # Dark color for text
    
    # Apply custom CSS with the theme colors
    st.markdown(f"""
    <style>
        /* Main elements */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            color: {secondary_color};
        }}
        
        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid {primary_color};
        }}
        
        h2 {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }}
        
        h3 {{
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 1.2rem;
            margin-bottom: 0.6rem;
        }}
        
        /* Cards and containers */
        .card {{
            background-color: white;
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-left: 4px solid {primary_color};
        }}
        
        .highlight-container {{
            background-color: {primary_color_light};
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid {primary_color};
        }}
        
        /* Custom elements */
        .info-box {{
            background-color: {primary_color_light};
            border: 1px solid {primary_color};
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .success-box {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .warning-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeeba;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        .error-box {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
        }}
        
        /* Data display elements */
        .data-container {{
            overflow-x: auto;
            border-radius: 0.5rem;
            border: 1px solid #e0e0e0;
            margin: 1rem 0;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: {primary_color};
            color: white;
            border: none;
            border-radius: 0.3rem;
            transition: all 0.3s;
        }}
        
        .stButton > button:hover {{
            background-color: {secondary_color};
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        
        /* Inputs */
        div[data-baseweb="input"] {{
            border-radius: 0.3rem;
        }}
        
        /* Sidebar */
        .sidebar .sidebar-content {{
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {primary_color};
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {secondary_color};
        }}
        
        /* Helper classes */
        .text-center {{
            text-align: center;
        }}
        
        .text-primary {{
            color: {primary_color};
        }}
        
        .text-secondary {{
            color: {secondary_color};
        }}
        
        .border-primary {{
            border: 1px solid {primary_color};
        }}
        
        .bg-primary-light {{
            background-color: {primary_color_light};
        }}
        
        .shadow {{
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .rounded {{
            border-radius: 0.5rem;
        }}
        
        .p-3 {{
            padding: 1rem;
        }}
        
        .m-3 {{
            margin: 1rem;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .animate-fadeIn {{
            animation: fadeIn 0.5s ease-in-out;
        }}
    </style>
    """, unsafe_allow_html=True)


def info_box(content, icon="ℹ️"):
    """Display an info box with the theme's styling"""
    st.markdown(f"""
    <div class="info-box">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """, unsafe_allow_html=True)


def success_box(content, icon="✅"):
    """Display a success box with the theme's styling"""
    st.markdown(f"""
    <div class="success-box">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """, unsafe_allow_html=True)


def warning_box(content, icon="⚠️"):
    """Display a warning box with the theme's styling"""
    st.markdown(f"""
    <div class="warning-box">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """, unsafe_allow_html=True)


def error_box(content, icon="❌"):
    """Display an error box with the theme's styling"""
    st.markdown(f"""
    <div class="error-box">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """, unsafe_allow_html=True)


def card(content, title=None):
    """Display content in a card with the theme's styling"""
    title_html = f"<h3>{title}</h3>" if title else ""
    st.markdown(f"""
    <div class="card">
        {title_html}
        {content}
    </div>
    """, unsafe_allow_html=True)


def highlight(content):
    """Display content in a highlighted container"""
    st.markdown(f"""
    <div class="highlight-container">
        {content}
    </div>
    """, unsafe_allow_html=True)


# Additional components can be added as needed