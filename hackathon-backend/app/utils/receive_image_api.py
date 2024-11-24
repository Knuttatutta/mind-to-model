import base64
import json
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Function to encode an image file into a base64 string
def encode_image(image_path):
    """
    Encodes an image file as a base64 string.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        # Read the image file and encode it to a base64 string
        return base64.b64encode(image_file.read()).decode("utf-8")

# Path to the image file (modify this to point to your specific sketch)
image_path = "Sample Images/hand_house_sketch.jpg"

# Convert the image to a base64-encoded string
base64_image = encode_image(image_path)

try:
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "I want you to analyse this sketch and provide me the 3D geometry equivalent of this image as a JSON file.",
            },
            {
            "type": "image_url",
            "image_url": {
                "url":  f"data:image/jpeg;base64,{base64_image}"
            },
            },
        ],
        }
    ],
    )

    # Extract the response content
    result = response.choices[0].message["content"]

    # Parse the JSON result to validate it
    parsed_geometry = json.loads(result)

    # Save the geometry data to a JSON file
    output_file = "geometry_output.json"
    with open(output_file, "w") as json_file:
        json.dump(parsed_geometry, json_file, indent=4)
    
    print(f"Geometry data saved to {output_file}")

except Exception as e:
    print(f"An error occurred: {e}")
