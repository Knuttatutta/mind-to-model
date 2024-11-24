from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.utils.image_to_3d import generate_3d_geometry
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
from uuid import uuid4
import re
import logging


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Directory to save generated images
IMAGE_DIRECTORY = "Sample_Images"
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)  # Ensure the directory exists

# Initialize FastAPI app
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="Sample_Images"), name="static")


# Configure CORS for local development
origins = [
    "http://localhost:3000",  # Ensure the correct origin is included
    "https://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Define the data model for incoming requests
class PromptRequest(BaseModel):
    prompt: str
    size: str
    floors: int

# Function to generate an image using DALL-E API
def generate_image(prompt: str, size: str, floors: int) -> str:
    """
    Generates an image using OpenAI's DALL-E API and saves it locally.

    Args:
        prompt (str): The prompt text to generate the image.
        size (str): The size of the building footprint (small, medium, large).
        floors (int): Number of floors in the building.

    Returns:
        str: The file path of the saved image.
    """
    # Replace this with your OpenAI API initialization
    from openai import OpenAI
    client = OpenAI()

    context = """You are an architect and you have to hand draw a simple building structure like boxy 'Seagram Building' 
               with the provided info in prompt. Dont overcomplicate it because it is just the base. 
               Just line draw the a simple boxy building"""
    negative_context = "No environment, No extra Environment, No extra details,very simple building"
    refined_prompt = f"context: {context}. \nnegative context(Remember this): {negative_context}. \nPrompt: {prompt} \nFootprint of Building: {size} \nNumber of Floors: {str(floors)} axiometric view, full view."
    
    try:
        # Make the API call to generate the image
        response = client.images.generate(
            model="dall-e-3",
            prompt=refined_prompt,
            size="1024x1024",
            style="natural",
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url

        # Generate a unique file name
        file_name = f"image.png"
        output_file = os.path.join(IMAGE_DIRECTORY, file_name)

        # Download and save the image
        image_data = requests.get(image_url)
        image_data.raise_for_status()  # Raise exception for HTTP errors

        with open(output_file, "wb") as file:
            file.write(image_data.content)

        return output_file  # Return the file path of the saved image

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")

# API route to handle image generation requests
@app.post("/generate-image/")
async def generate_image_endpoint(request: PromptRequest):
    """
    API endpoint to handle image generation requests.

    Args:
        request (PromptRequest): The request body containing the prompt.

    Returns:
        dict: A dictionary containing the local image path or URL.
    """
    try:
        # Call the image generation function
                # Call the image generation function with all parameters
        saved_image_path = generate_image(
            prompt=request.prompt,
            size=request.size,
            floors=request.floors  # Note: You defined floors as str in function but int in model
        )

        # Construct a URL to access the image (optional if serving via API)
        image_url = f"/static/{os.path.basename(saved_image_path)}"

        return {"image_path": image_url}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    

@app.get("/generate-3d/")
async def generate_3d_endpoint():
    try:
        logger.debug("Starting generate_3d_endpoint")
        
        # Generate the 3D geometry
        response_content = generate_3d_geometry("Sample_Images/image.png")
        
        if response_content and response_content.content:
            logger.debug("Got response content, extracting code")
            
            # Get the text content
            three_js_code = response_content.content[0].text
            logger.debug(f"Raw response text (first 100 chars): {three_js_code[:100]}")
            
            # Write full response for debugging
            with open("/Users/and_seb/Documents/Programming/AEC Hackathon Prep/hackathon-backend/app/full_response.txt", "w") as f:
                f.write(three_js_code)
            
            # Try multiple patterns to extract code
            patterns = [
                r"```javascript\s*(.*?)\s*```",  # Standard javascript code block
                r"```jsx\s*(.*?)\s*```",         # JSX code block
                r"`jsx\s*(.*?)\s*`",             # Single backtick jsx
                r"```\s*(.*?)\s*```"             # Any code block
            ]
            
            extracted_code = None
            for pattern in patterns:
                matches = re.findall(pattern, three_js_code, re.DOTALL)
                if matches:
                    extracted_code = matches[0]
                    logger.debug(f"Found code using pattern: {pattern}")
                    break
            
            if not extracted_code:
                # If no code blocks found, try to extract code between obvious markers
                try:
                    start_marker = "Here's the Three.js code"
                    end_marker = "Would you like me to"
                    start_idx = three_js_code.find(start_marker)
                    end_idx = three_js_code.find(end_marker)
                    
                    if start_idx != -1 and end_idx != -1:
                        extracted_code = three_js_code[start_idx + len(start_marker):end_idx].strip()
                        logger.debug("Extracted code using markers")
                except Exception as e:
                    logger.error(f"Error extracting code with markers: {str(e)}")
            
            if extracted_code:
                # Clean up the code
                extracted_code = extracted_code.strip()
                logger.debug(f"Extracted code (first 100 chars): {extracted_code[:100]}")
                
                # Write the extracted code to files
                try:
                    # Write debug output
                    with open("/Users/and_seb/Documents/Programming/AEC Hackathon Prep/hackathon-backend/app/debug_output.js", "w") as f:
                        f.write("// Debug output of extracted code\n")
                        f.write(extracted_code)
                    logger.debug("Wrote debug output")
                    
                    # Write to threejs.js
                    with open("/Users/and_seb/Documents/Programming/AEC Hackathon Prep/hackathon-backend/app/threejs.js", "w") as f:
                        f.write(extracted_code)
                    logger.debug("Wrote to threejs.js")
                    
                    return {"three_js_code": extracted_code}
                except Exception as e:
                    logger.error(f"Error writing files: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error writing files: {str(e)}")
            else:
                logger.error("No code found in response")
                # Return the full response for debugging
                return {
                    "error": "No code found in response",
                    "full_response": three_js_code
                }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@app.get("/test-3d/")
async def test_3d_endpoint():
    try:
        # Read the content of test4.js
        with open("/Users/and_seb/Documents/Programming/AEC Hackathon Prep/hackathon-backend/test6.js", "r") as file:
            three_js_code = file.read()
        
        # Setup code to run before the test4.js content
        setup_code = """
            // Set up renderer
            renderer.setClearColor(0xf0f0f0);
        """
        
        complete_code = setup_code + three_js_code
        
        return {
            "three_js_code": complete_code,
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
