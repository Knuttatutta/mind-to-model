import os
import base64
import json
from anthropic import Anthropic
from PIL import Image
import tkinter as tk
from tkinter import filedialog

def encode_image(image_path):
    """Encode image to base64 string"""
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')

    from io import BytesIO
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def analyze_building_geometry(image_path, api_key):
    """Extract precise building geometry from image"""
    client = Anthropic(api_key=api_key)

    try:
        base64_image = encode_image(image_path)

        system_prompt = """You are a highly specialized building geometry analyzer. Your task is to analyze building images and generate Python scripts that create accurate geometric representations."""

        detailed_prompt = """Based on this building image, write a Python script that will create a JSON file containing the geometry data. The script should:

1. Create a dictionary with the building geometry
2. Include all visible structural elements
3. Make reasonable assumptions for non-visible elements to complete the structure
4. Save the data to a JSON file

The script must generate a JSON file with this exact structure:
{
  "buildingId": "building_1",
  "components": {
    "walls": [
      {
        "id": "wall_n",
        "vertices": [
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number}
        ]
      }
    ],
    "floors": [
      {
        "id": "floor_n",
        "vertices": [
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number}
        ]
      }
    ],
    "openings": [
      {
        "id": "opening_n",
        "type": "door|window",
        "vertices": [
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number}
        ]
      }
    ],
    "columns": [
      {
        "id": "column_n",
        "vertices": [
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number}
        ]
      }
    ],
    "beams": [
      {
        "id": "beam_n",
        "vertices": [
          {"x": number, "y": number, "z": number},
          {"x": number, "y": number, "z": number}
        ]
      }
    ]
  },
  "units": "meters"
}

Provide only the Python script that generates this JSON file. Do not include any explanations or additional text."""

        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.1,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": detailed_prompt
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        )

        return response.content[0].text

    except Exception as e:
        print(f"Error during API call: {e}")
        return None

def main():
    root = tk.Tk()
    root.withdraw()

    # Get API key from environment variable or use provided key
    api_key = ""
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    print("Please select an image file...")
    image_path = filedialog.askopenfilename(
        title="Select Building Image",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
    )

    if not image_path:
        print("No file selected. Exiting...")
        return

    print("Analyzing building geometry...")
    script_response = analyze_building_geometry(image_path, api_key)

    if script_response:
        output_path = os.path.splitext(image_path)[0] + "_geometry_script.py"
        with open(output_path, 'w') as f:
            f.write(script_response)
        print(f"Python script saved to: {output_path}")
    else:
        print("Failed to generate geometry script")

if __name__ == "__main__":
    main()