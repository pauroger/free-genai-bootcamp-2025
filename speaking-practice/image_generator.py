import boto3
import json
import os
import base64
from typing import Dict, List, Optional
from datetime import datetime
import tempfile
from PIL import Image
import io

# MODEL_ID for Stable Diffusion
MODEL_ID = "amazon.titan-image-generator-v1"

class ImageGenerator:
    def __init__(self):
        # Initialize AWS Bedrock client
        self.bedrock = boto3.client('bedrock-runtime', region_name="eu-west-1")
        self.model_id = MODEL_ID
        
        # Create image output directory
        self.image_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "./images"
        )
        os.makedirs(self.image_dir, exist_ok=True)
        
        # Hard-coded landscape prompts with animals
        self.landscape_prompts = [
            "A serene mountain landscape with deer grazing in a meadow, photorealistic",
            "A tropical beach with palm trees and colorful birds flying overhead, vivid colors, detailed",
            "A dense forest with a family of bears searching for food, morning light, mist, detailed foliage",
            "A savanna at sunset with elephants walking in the distance, golden hour lighting, atmospheric",
            "A snowy mountain range with wolves standing on a ridge, dramatic lighting, high detail"
        ]
        
        # Category-specific base prompts
        self.category_prompts = {
            "landscape": "Create a whimsical landscape, with mountains and trees. Feature some animals doing an activity.",
            "city": "Busy city life, add some extreme weather conditions, they can be good or bad.",
            "interaction": "Realistic image of a group of people doing an interaction."
        }

    def _invoke_bedrock(self, prompt: str) -> bytes:
        """Invoke Bedrock with the given prompt using the image generation model"""
        # Format depends on the model being used
        if "stability" in self.model_id:
            body = json.dumps({
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 8,
                "steps": 50,
                "seed": 42,
                "style_preset": "photographic"
            })
        elif "amazon.titan-image" in self.model_id:
            body = json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": "blurry, bad quality, distorted, disfigured",
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "quality": "standard",
                    "cfgScale": 8.0,
                    "seed": 42
                }
            })
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            response_body = json.loads(response.get('body').read())
            # Extract the base64-encoded image based on model
            if "stability" in self.model_id:
                image_data = response_body.get('artifacts')[0].get('base64')
            elif "amazon.titan-image" in self.model_id:
                image_data = response_body.get('images')[0]
            return base64.b64decode(image_data)
        except Exception as e:
            print(f"Error in Bedrock invoke_model: {str(e)}")
            raise e

    def get_random_prompt(self) -> str:
        """Returns a random landscape prompt"""
        import random
        return random.choice(self.landscape_prompts)
    
    def get_category_prompt(self, category: str) -> str:
        """Returns the base prompt for a specific category"""
        category = category.lower()
        return self.category_prompts.get(category, self.category_prompts["landscape"])

    def customize_prompt(self, base_prompt: str, features: Dict = None) -> str:
        """
        Customize a prompt with additional features if provided.
        
        Args:
            base_prompt: The starting prompt
            features: Dict with optional customizations like:
                - time_of_day: "sunrise", "day", "sunset", "night"
                - weather: "clear", "cloudy", "rainy", "snowy"
                - animals: List of animals to include
                
        Returns:
            Customized prompt string
        """
        if not features:
            return base_prompt
            
        customized = base_prompt
        
        if 'time_of_day' in features:
            time_mapping = {
                "sunrise": "at sunrise with soft pink and orange light",
                "day": "during daytime with clear blue skies",
                "sunset": "at sunset with golden light and long shadows",
                "night": "at night under a starry sky with moonlight"
            }
            time_desc = time_mapping.get(features['time_of_day'].lower(), "")
            if time_desc:
                customized = customized.replace("with", time_desc + " with", 1)
        
        if 'weather' in features:
            weather_mapping = {
                "clear": "clear skies",
                "cloudy": "partly cloudy skies with dramatic cloud formations",
                "rainy": "light rain creating a misty atmosphere",
                "snowy": "gentle snowfall creating a winter wonderland"
            }
            weather_desc = weather_mapping.get(features['weather'].lower(), "")
            if weather_desc:
                customized += f", {weather_desc}"
        
        if 'animals' in features and isinstance(features['animals'], list) and features['animals']:
            animals = ", ".join(features['animals'])
            # Check if the base prompt already mentions animals
            if "with" in customized and not any(animal in customized.lower() for animal in features['animals']):
                customized = customized.replace("with", f"with {animals} and", 1)
            else:
                customized += f", featuring {animals}"
        
        return customized

    def generate_image(self, custom_prompt: str = None, features: Dict = None, category: str = None) -> str:
        """
        Generate an image based on a prompt.
        
        Args:
            custom_prompt: A fully formed custom prompt to use directly
            features: Dict with features to customize a base prompt
            category: Category to use for base prompt if no custom prompt provided
            
        Returns:
            Path to the generated image file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.image_dir, f"generated_{timestamp}.png")
        
        try:
            # Determine which prompt to use
            if custom_prompt:
                # Use the provided custom prompt directly
                final_prompt = custom_prompt
            elif category:
                # Get base prompt for category and customize if features provided
                base_prompt = self.get_category_prompt(category)
                final_prompt = self.customize_prompt(base_prompt, features)
            else:
                # Use random landscape prompt as fallback and customize
                base_prompt = self.get_random_prompt()
                final_prompt = self.customize_prompt(base_prompt, features)
            
            print(f"Generating image with prompt: {final_prompt}")
            
            # Generate the image
            image_data = self._invoke_bedrock(final_prompt)
            
            # Save the image
            image = Image.open(io.BytesIO(image_data))
            image.save(output_file)
            
            return output_file
            
        except Exception as e:
            if os.path.exists(output_file):
                os.unlink(output_file)
            raise Exception(f"Image generation failed: {str(e)}")

    def batch_generate(self, count: int = 3, custom_prompt: str = None, features: Dict = None, category: str = None) -> List[str]:
        """
        Generate multiple images.
        Returns a list of paths to the generated image files.
        """
        image_paths = []
        for _ in range(count):
            try:
                image_path = self.generate_image(custom_prompt=custom_prompt, features=features, category=category)
                image_paths.append(image_path)
            except Exception as e:
                print(f"Error generating image: {str(e)}")
        
        return image_paths


# Example usage
if __name__ == "__main__":
    generator = ImageGenerator()
    
    # Generate with default prompt
    image_path = generator.generate_image()
    print(f"Generated image: {image_path}")
    
    # Generate with custom features
    features = {
        "time_of_day": "sunset",
        "weather": "clear",
        "animals": ["wolves", "eagles"]
    }
    
    custom_image = generator.generate_image(features=features)
    print(f"Generated custom image: {custom_image}")
    
    # Generate with category
    category_image = generator.generate_image(category="city")
    print(f"Generated category image: {category_image}")
    
    # Generate with fully custom prompt
    custom_prompt = "A futuristic city skyline at night with neon lights and flying cars, cyberpunk style"
    prompt_image = generator.generate_image(custom_prompt=custom_prompt)
    print(f"Generated custom prompt image: {prompt_image}")
    
    # Batch generate
    batch_paths = generator.batch_generate(count=2)
    print(f"Generated batch images: {batch_paths}")
