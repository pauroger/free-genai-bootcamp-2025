import gradio as gr
from gradio.themes.utils import colors, fonts, sizes

def apply_custom_theme(primary_color="#90cdec"):
    """
    Apply a custom theme to a Gradio app.
    
    Args:
        primary_color (str): The primary color in HEX format
        
    Returns:
        gr.Theme: A Gradio theme object
    """
    # Derive complementary colors from the primary color
    primary_color_light = f"{primary_color}33"  # 20% opacity for light background  
    primary_color_medium = f"{primary_color}66"  # 40% opacity for medium elements
    secondary_color = "#3A6B87"  # Darker shade for secondary elements
    text_color = "#1E3E4F"  # Dark color for text
    
    # Create custom Gradio theme
    return gr.themes.Base(
        primary_hue=colors.Color(
            name="custom",
            c50=primary_color_light,
            c100=primary_color_light,
            c200=primary_color_light,
            c300=primary_color_medium,
            c400=primary_color_medium,
            c500=primary_color,
            c600=primary_color,
            c700=secondary_color,
            c800=secondary_color,
            c900=secondary_color,
            c950=text_color,
        ),
        neutral_hue=colors.gray,
        font=(
            fonts.GoogleFont("Inter"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ),
        spacing_size=sizes.spacing_md,
        radius_size=sizes.radius_md,
        text_size=sizes.text_md,
    )


# Custom component functions similar to Streamlit version
def info_box(content, icon="ℹ️"):
    """Display an info box with the theme's styling"""
    return gr.HTML(f"""
    <div style="background-color: rgba(144, 205, 236, 0.2); 
                border: 1px solid #90cdec; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin: 1rem 0;">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """)


def success_box(content, icon="✅"):
    """Display a success box with the theme's styling"""
    return gr.HTML(f"""
    <div style="background-color: #d4edda; 
                border: 1px solid #c3e6cb; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin: 1rem 0;">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """)


def warning_box(content, icon="⚠️"):
    """Display a warning box with the theme's styling"""
    return gr.HTML(f"""
    <div style="background-color: #fff3cd; 
                border: 1px solid #ffeeba; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin: 1rem 0;">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """)


def error_box(content, icon="❌"):
    """Display an error box with the theme's styling"""
    return gr.HTML(f"""
    <div style="background-color: #f8d7da; 
                border: 1px solid #f5c6cb; 
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin: 1rem 0;">
        <span style="font-size:1.5rem;margin-right:0.5rem;">{icon}</span>
        {content}
    </div>
    """)


def card(content, title=None):
    """Display content in a card with the theme's styling"""
    title_html = f"<h3 style='color: #3A6B87; font-size: 1.4rem; font-weight: 600; margin-top: 0.5rem; margin-bottom: 0.6rem;'>{title}</h3>" if title else ""
    return gr.HTML(f"""
    <div style="background-color: white;
                border-radius: 0.5rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border-left: 4px solid #90cdec;">
        {title_html}
        {content}
    </div>
    """)


def highlight(content):
    """Display content in a highlighted container"""
    return gr.HTML(f"""
    <div style="background-color: rgba(144, 205, 236, 0.2);
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
                border-left: 4px solid #90cdec;">
        {content}
    </div>
    """)


# Add custom CSS to enhance the theme
def add_custom_css():
    """Add additional custom CSS to further style the Gradio app"""
    return gr.HTML("""
    <style>
        /* Headers */
        h1, h2, h3 {
            color: #3A6B87;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #90cdec;
        }
        
        h2 {
            font-size: 1.8rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }
        
        h3 {
            font-size: 1.4rem;
            font-weight: 600;
            margin-top: 1.2rem;
            margin-bottom: 0.6rem;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #90cdec;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #3A6B87;
        }
        
        /* Helper classes */
        .text-center {
            text-align: center;
        }
        
        .text-primary {
            color: #90cdec;
        }
        
        .text-secondary {
            color: #3A6B87;
        }
        
        .border-primary {
            border: 1px solid #90cdec;
        }
        
        .bg-primary-light {
            background-color: rgba(144, 205, 236, 0.2);
        }
        
        .shadow {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .rounded {
            border-radius: 0.5rem;
        }
        
        .p-3 {
            padding: 1rem;
        }
        
        .m-3 {
            margin: 1rem;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .animate-fadeIn {
            animation: fadeIn 0.5s ease-in-out;
        }
        
        /* Gradio-specific styles */
        button.primary {
            background-color: #90cdec !important;
            color: white !important;
            border: none !important;
            transition: all 0.3s !important;
        }
        
        button.primary:hover {
            background-color: #3A6B87 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
        }
        
        .gradio-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Improve input fields */
        input, select, textarea {
            border-radius: 0.3rem !important;
        }
    </style>
    """)


# Example usage
def create_themed_app(primary_color="#90cdec"):
    """
    Create a Gradio app with the custom theme applied
    
    Args:
        primary_color (str): The primary color in HEX format
        
    Returns:
        gr.Blocks: A Gradio app with the theme applied
    """
    theme = apply_custom_theme(primary_color)
    
    with gr.Blocks(theme=theme) as app:
        add_custom_css()
        
        gr.Markdown("# Themed Gradio App")
        gr.Markdown("This app demonstrates the custom theme")
        
        with gr.Row():
            with gr.Column():
                info_box("This is an info box component.")
                success_box("This is a success box component.")
            with gr.Column():
                warning_box("This is a warning box component.")
                error_box("This is an error box component.")
        
        with gr.Row():
            card("<p>This is a card component with some content.</p>", title="Card Title")
            highlight("<p>This is highlighted content.</p>")
        
        with gr.Row():
            gr.Button("Primary Button")
    
    return app


# If running this file directly, create and launch a demo app
if __name__ == "__main__":
    app = create_themed_app()
    app.launch()
