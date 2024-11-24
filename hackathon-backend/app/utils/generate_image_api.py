import requests
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from uuid import uuid4

# Directory to save generated images
IMAGE_DIRECTORY = "Sample_Images"
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)  # Ensure the directory exists

# Function to generate an image using DALL-E API
def generate_image(prompt: str) -> str:
    """
    Generates an image using OpenAI's DALL-E API and saves it locally.

    Args:
        prompt (str): The prompt text to generate the image.

    Returns:
        str: The file path of the saved image.
    """
    # Replace this with your OpenAI API initialization
    from openai import OpenAI
    client = OpenAI()

    try:
        # Make the API call to generate the image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url

        # Generate a unique file name
        file_name = f"{uuid4()}.png"
        output_file = os.path.join(IMAGE_DIRECTORY, file_name)

        # Download and save the image
        image_data = requests.get(image_url)
        image_data.raise_for_status()  # Raise exception for HTTP errors

        with open(output_file, "wb") as file:
            file.write(image_data.content)

        return output_file  # Return the file path of the saved image

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")
