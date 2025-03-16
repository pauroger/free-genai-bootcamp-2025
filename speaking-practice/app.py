import os
import random
import logging
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import shutil
import sys
from image_generator import ImageGenerator

load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

sys.path.append(str(Path(__file__).parent.parent))

from themes.gradio_theme import apply_custom_theme

theme = apply_custom_theme(primary_color="#90cdec")

import gradio as gr

# Initialize the image generator
generator = ImageGenerator()

# Function to randomly select configuration options
def get_random_config(category):
    if category == "Landscape":
        time_of_day = random.choice(["Day", "Sunset", "Sunrise", "Night"])
        weather = random.choice(["Clear", "Cloudy", "Rainy", "Snowy"])
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
        
        prompt = f"Busy {city_type.lower()} city life with detailed architecture and streets"
        prompt += f" during {time_of_day.lower()}"
        prompt += f" with {weather_condition.lower()} weather conditions"
        prompt += ", photorealistic style with dramatic lighting"
        return prompt
    
    else:  # Interaction
        activity = random.choice(["Dancing", "Meeting", "Celebration", "Sports", "Dining", "Working", "Shopping"])
        location = random.choice(["Indoor", "Outdoor", "Beach", "Park", "Office", "Restaurant", "Street"])
        group_size = random.randint(2, 10)
        
        prompt = f"Realistic image of a group of {group_size} people {activity.lower()}"
        prompt += f" in a {location.lower()} setting"
        prompt += ", natural lighting, candid moment, detailed expressions"
        return prompt

# Function to build prompts based on category
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

# Function to generate image
def generate_image(category):
    try:
        custom_prompt, features, category_name = build_prompt(category)
        
        # Generate the image
        image_path = generator.generate_image(
            custom_prompt=custom_prompt,
            features=features,
            category=category_name
        )
        
        # Copy to a temp file that Gradio can safely access
        temp_dir = Path(tempfile.gettempdir())
        temp_image_path = temp_dir / f"temp_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Copy the image using shutil (more reliable)
        shutil.copy2(image_path, temp_image_path)
        
        return str(temp_image_path)
    except Exception as e:
        return None

# Function to process audio for German language evaluation
def process_audio(audio_filepath, image_path):
    
    if audio_filepath is None:
        return "No audio recorded.", "No evaluation available."
    
    if not client:
        return "OpenAI API key not configured correctly.", "Evaluation not available without API key."
    
    try:
        # Verify the file exists
        if not os.path.exists(audio_filepath):
            return "Error: Audio file not found.", "Evaluation unavailable."
        
        # Log file information
        file_size = os.path.getsize(audio_filepath)
        
        # Get image prompt context if available
        image_context = ""
        if image_path:
            try:
                # Extract the image filename to identify its category/prompt
                image_filename = os.path.basename(image_path)
                
                # Try to determine what type of image was generated
                if "landscape" in image_filename.lower():
                    image_category = "Landscape"
                elif "city" in image_filename.lower():
                    image_category = "City"
                else:
                    image_category = "Interaction"
                
                # Generate a description of what should be in the image
                _, features, _ = build_prompt(image_category)
                if features:
                    if isinstance(features, dict):
                        # For landscape images
                        time = features.get("time_of_day", "")
                        weather = features.get("weather", "")
                        animals = ", ".join(features.get("animals", []))
                        image_context = f"The image shows a landscape during {time} with {weather} weather. "
                        if animals:
                            image_context += f"There may be {animals} visible."
                    else:
                        # For other categories
                        image_context = f"The image prompt was: {features}"

            except Exception as e:
                # Continue without image context if there's an error
                image_context = ""
        
        # Transcribe with OpenAI
        with open(audio_filepath, "rb") as audio_file:
            try:
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="de",
                    response_format="text"
                )
                transcription = transcript_response
            except Exception as e:
                return f"Error transcribing audio: {str(e)}", "Evaluation unavailable due to transcription error."
    
        # If the transcription is empty or too short
        if not transcription or len(transcription.strip()) < 5:
            return "No speech detected or transcription failed.", "Evaluation unavailable due to insufficient speech."
        
        # Evaluate with OpenAI
        try:
            # Include image context in evaluation if available
            image_instruction = ""
            if image_context:
                image_instruction = (
                    f"The user was describing this image: {image_context}\n"
                    "When evaluating, consider how accurately the user described the image. "
                    "If they described something completely different or missed important elements, "
                    "reduce their score and mention this in your feedback."
                )
            
            evaluation_prompt = (
                "Please evaluate the following German speaking transcript based on these categories: "
                "Fluency and Coherence, Lexical Resource, Grammatical Range and Accuracy, and Description Accuracy. "
                "For each category, write a short comment (one or two sentences) about how the speaker performed. "
                f"\n\n{image_instruction}\n\n"
                "Then, based on the overall performance, assign an overall CEFR level for the speaker: A1, A2, B1, B2, C1, or C2. "
                "Ensure the total response does not exceed 200 words. "
                f"Transcript: {transcription}"
            )
            
            evaluation_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert German language examiner."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )
            evaluation = evaluation_response.choices[0].message.content.strip()
        except Exception as e:
            return transcription, f"Error evaluating speech: {str(e)}"
        
        return transcription, evaluation
        
    except Exception as e:
        error_details = traceback.format_exc()
        return f"Error processing audio: {str(e)}", "Evaluation unavailable due to error."

# Create the Gradio interface
css = """
    h1 {
        margin-bottom: 1rem;
        text-align: center;
    }
    .image-container img {
        max-height: 400px;
        object-fit: contain;
    }
"""

with gr.Blocks(theme=theme, css=css) as demo:
    gr.Markdown("<h1>🗣️ German Speaking Tutor</h1>")
    gr.Markdown("Generate an image and practice describing it in German. Your speech will be transcribed and evaluated.")
    
    # Move instructions to the top with better formatting
    with gr.Accordion("📚 How to use this app", open=True):
        gr.Markdown("""
        #### 🖼️ Step 1: Generate an Image
        • Select an image category from the dropdown
        • Click 'Generate Image' to create a random scene
        • The image will appear in the left panel
        
        #### 🎙️ Step 2: Practice Speaking German
        • Use the microphone buttons to record yourself speaking
        • Describe the image you see in German
        • Click 'Process Recording' when you're done
        • View your transcription and language evaluation
        
        #### 💡 Tips for Better Practice
        • Try describing what you see in complete sentences
        • Use varied vocabulary and descriptive language
        • Pay attention to German grammar and sentence structure
        • Practice regularly to build confidence and fluency
        """)
    
    # Add some spacing after instructions
    gr.Markdown("<br>")
    
    with gr.Row():
        # Left column: image generation
        with gr.Column():
            gr.Markdown("### 1 - Image Prompt Generator")
            category = gr.Dropdown(
                ["Landscape", "City", "Interaction"],
                label="Select image category",
                value="Landscape"
            )
            generate_button = gr.Button("Generate Image", variant="primary")
            image_display = gr.Image(
                label="Generated Image", 
                type="filepath",
                container=True,
                elem_classes="image-container"
            )
        
        # Right column: German practice
        with gr.Column():
            gr.Markdown("### 2 - Practice Speaking")
            gr.Markdown("Record yourself describing the image in German. Your recording will be transcribed and evaluated.")
            
            # Audio component with just recording interface
            audio_component = gr.Audio(
                source="microphone",
                type="filepath",
                label="Record your description (max 2 min)",
                format="wav",
                duration=120,
                interactive=True
            )
            
            with gr.Row():
                redo_button = gr.Button("Redo Recording", variant="secondary")
                process_button = gr.Button("Process Recording", variant="primary")
            
            with gr.Tabs():
                with gr.TabItem("Transcription"):
                    output_transcript = gr.Markdown("*Your transcription will appear here*")
                with gr.TabItem("Evaluation"):
                    feedback = gr.Markdown("*Your evaluation will appear here*")
    
    # Set up event handlers
    generate_button.click(
        fn=generate_image,
        inputs=[category],
        outputs=[image_display]
    )
    
    # Set up redo button to clear recording
    redo_button.click(
        fn=lambda: None,
        inputs=None,
        outputs=[audio_component]
    )
    
    # Process recording on button click
    process_button.click(
        fn=process_audio,
        inputs=[audio_component, image_display],  # Add image as input
        outputs=[output_transcript, feedback]
    )

# Launch the app
if __name__ == "__main__":
    # Add the allowed_paths parameter to include your images directory
    allowed_paths = [
        os.path.join(os.getcwd(), "images"),  # Add the images directory
        os.path.dirname(os.path.abspath(__file__))  # Add the current script directory
    ]
    
    demo.launch(
        server_port=7861,
        server_name="127.0.0.1",
        show_error=True,
        allowed_paths=allowed_paths,
        share=False
    )
