import streamlit as st
import os
from PIL import Image
from image_generator import ImageGenerator

# Initialize the image generator
generator = ImageGenerator()

# Set page title and configuration
st.set_page_config(page_title="AI Image Generator", layout="wide")
st.title("AI Landscape Image Generator")

# Add description
st.markdown("""
    This app generates AI images based on different categories.
    Select a category, configure options if desired, and click 'Generate Image'.
""")

# Create a dropdown for selecting the image category
category = st.selectbox(
    "Select image category:",
    ["Landscape", "City", "Interaction"]
)

# Create columns for layout
col1, col2 = st.columns([1, 2])

with col1:
    # Add options based on the category
    with st.expander("Configuration Options", expanded=True):
        if category == "Landscape":
            time_of_day = st.selectbox("Time of day:", ["Day", "Sunset", "Sunrise", "Night"])
            weather = st.selectbox("Weather:", ["Clear", "Cloudy", "Rainy", "Snowy"])
            animals = st.multiselect("Animals:", ["Deer", "Bears", "Wolves", "Eagles", "Foxes", "Rabbits"])
        
        elif category == "City":
            time_of_day = st.selectbox("Time of day:", ["Day", "Night", "Dawn", "Dusk"])
            weather_condition = st.selectbox(
                "Extreme weather:", 
                ["Thunderstorm", "Heavy Snow", "Fog", "Heatwave", "Hurricane", "Clear Sky"]
            )
            city_type = st.selectbox("City type:", ["Modern", "Futuristic", "Historical", "Cyberpunk"])
        
        elif category == "Interaction":
            activity = st.selectbox(
                "Activity type:", 
                ["Dancing", "Meeting", "Celebration", "Sports", "Dining", "Working", "Shopping"]
            )
            location = st.selectbox(
                "Location:", 
                ["Indoor", "Outdoor", "Beach", "Park", "Office", "Restaurant", "Street"]
            )
            group_size = st.slider("Group size:", 2, 10, 4)

    # Add generate button
    generate_button = st.button("Generate Image", type="primary")

# Function to build prompts based on category and options
def build_prompt():
    if category == "Landscape":
        base_prompt = "Create a whimsical landscape, with mountains and trees. Feature some animals doing an activity."
        features = {
            "time_of_day": time_of_day.lower(),
            "weather": weather.lower(),
            "animals": animals
        }
        return None, features
    
    elif category == "City":
        # Custom city prompt
        prompt = f"Busy {city_type.lower()} city life with detailed architecture and streets"
        prompt += f" during {time_of_day.lower()}"
        prompt += f" with {weather_condition.lower()} weather conditions"
        prompt += ", photorealistic style with dramatic lighting"
        return prompt, None
    
    else:  # Interaction
        # Custom interaction prompt
        prompt = f"Realistic image of a group of {group_size} people {activity.lower()}"
        prompt += f" in a {location.lower()} setting"
        prompt += ", natural lighting, candid moment, detailed expressions"
        return prompt, None

# Display area for the generated image
with col2:
    if generate_button:
        with st.spinner("Generating image..."):
            try:
                # Get the appropriate prompt based on category
                custom_prompt, features = build_prompt()
                
                # Generate the image
                st.session_state.image_path = generator.generate_image(
                    custom_prompt=custom_prompt,
                    features=features
                )
                
                # Success message
                st.success("Image generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
    
    # Display the generated image if available
    if 'image_path' in st.session_state and os.path.exists(st.session_state.image_path):
        st.image(st.session_state.image_path, caption="Generated Image", use_column_width=True)
        
        # Add download button
        with open(st.session_state.image_path, "rb") as file:
            btn = st.download_button(
                label="Download Image",
                data=file,
                file_name=os.path.basename(st.session_state.image_path),
                mime="image/png"
            )
