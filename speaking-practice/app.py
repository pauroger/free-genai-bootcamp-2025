import sys
import os
import random
from pathlib import Path
from PIL import Image
from image_generator import ImageGenerator

sys.path.append(str(Path(__file__).parent.parent))

from themes.streamlit_theme import (
    apply_custom_theme,
    info_box,
    success_box,
    warning_box,
    error_box,
    card,
    highlight
)

import streamlit as st

# Set page config as the VERY FIRST Streamlit command
st.set_page_config(
    page_title="🗣️ Speaking Tutor",
    page_icon="🗣️",
    layout="wide",
)

# Main app layout
st.title("🗣️ Speaking Tutor")

apply_custom_theme(primary_color="#90cdec")

# Initialize the image generator
generator = ImageGenerator()

# Add description
st.markdown("""
    Select a category and click 'Generate Image' to create a random image.
""")

# Create a dropdown for selecting the image category
category = st.selectbox(
    "Select image category:",
    ["Landscape", "City", "Interaction"]
)

# Create columns for layout
col1, col2 = st.columns([1, 2])

with col1:
    # Add generate button
    generate_button = st.button("Generate Image", type="primary")

# Function to randomly select configuration options
def get_random_config(category):
    if category == "Landscape":
        time_of_day = random.choice(["Day", "Sunset", "Sunrise", "Night"])
        weather = random.choice(["Clear", "Cloudy", "Rainy", "Snowy"])
        # Randomly select 0-3 animals
        all_animals = ["Deer", "Bears", "Wolves", "Eagles", "Foxes", "Rabbits"]
        animals = random.sample(all_animals, random.randint(0, 3))
        return {
            "time_of_day": time_of_day.lower(),
            "weather": weather.lower(),
            "animals": animals
        }
    
    elif category == "City":
        time_of_day = random.choice(["Day", "Night", "Dawn", "Dusk"])
        weather_condition = random.choice(["Thunderstorm", "Heavy Snow", "Fog", "Heatwave", "Hurricane", "Clear Sky"])
        city_type = random.choice(["Modern", "Futuristic", "Historical", "Cyberpunk"])
        
        # Custom city prompt
        prompt = f"Busy {city_type.lower()} city life with detailed architecture and streets"
        prompt += f" during {time_of_day.lower()}"
        prompt += f" with {weather_condition.lower()} weather conditions"
        prompt += ", photorealistic style with dramatic lighting"
        return prompt
    
    else:  # Interaction
        activity = random.choice(["Dancing", "Meeting", "Celebration", "Sports", "Dining", "Working", "Shopping"])
        location = random.choice(["Indoor", "Outdoor", "Beach", "Park", "Office", "Restaurant", "Street"])
        group_size = random.randint(2, 10)
        
        # Custom interaction prompt
        prompt = f"Realistic image of a group of {group_size} people {activity.lower()}"
        prompt += f" in a {location.lower()} setting"
        prompt += ", natural lighting, candid moment, detailed expressions"
        return prompt

# Function to build prompts based on category and random options
def build_prompt(category):
    if category == "Landscape":
        features = get_random_config(category)
        return None, features, "landscape"
    
    elif category == "City":
        prompt = get_random_config(category)
        return prompt, None, None
    
    else:  # Interaction
        prompt = get_random_config(category)
        return prompt, None, None

# Display area for the generated image
with col2:
    if generate_button:
        with st.spinner("Generating image..."):
            try:
                # Get the appropriate prompt based on category with random config
                custom_prompt, features, category_name = build_prompt(category)
                
                # Generate the image
                st.session_state.image_path = generator.generate_image(
                    custom_prompt=custom_prompt,
                    features=features,
                    category=category_name
                )
                
                # Success message
                st.success("Image generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating image: {str(e)}")
    
    # Display the generated image if available
    if 'image_path' in st.session_state and os.path.exists(st.session_state.image_path):
        st.image(st.session_state.image_path, caption="Generated Image", use_container_width=True)
        
        # Add download button
        with open(st.session_state.image_path, "rb") as file:
            btn = st.download_button(
                label="Download Image",
                data=file,
                file_name=os.path.basename(st.session_state.image_path),
                mime="image/png"
            )

# Add footer
st.markdown("---")
