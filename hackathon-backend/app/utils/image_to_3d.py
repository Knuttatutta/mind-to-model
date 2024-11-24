import anthropic
import base64
import re

# Initialize the Claude client
client = anthropic.Anthropic(api_key="Your API Key")

user_prompt = """Given this image, generate Three.js code to create a 3D visualization of the building. The code must follow this exact structure and style:

1. Use MeshPhongMaterial instead of wireframes
2. Create distinct building parts with these material colors:
   - Main building: color: 0xcccccc
   - Windows: color: 0x444444
   - Roof and borders: color: 0x888888
   - Side details: color: 0x999999

Required code structure:
```javascript
// Create the main building structure
const buildingGeometry = new THREE.BoxGeometry(/* dimensions */);
const buildingMaterial = new THREE.MeshPhongMaterial({ color: 0xcccccc });
const building = new THREE.Mesh(buildingGeometry, buildingMaterial);

// Create window grid
// Use nested loops for window placement
const windowRowCount = /* number */;
const windowColumnCount = /* number */;
// ... window creation and positioning ...

// Create roof and border elements
// ... roof code ...

// Create side panels or additional details
// ... panels code ...

// Add everything to the scene
scene.add(building);
// ... add other elements ...

// Add lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(10, 20, 10);

scene.add(ambientLight);
scene.add(directionalLight);

// Camera position
camera.position.set(10, 10, 10);
camera.lookAt(0, 0, 0);

// Add controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;

// Animation
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
```

Important requirements:
1. DO NOT use wireframe materials
2. DO use MeshPhongMaterial for all meshes
3. DO include proper lighting setup
4. DO create organized window grid using loops
5. DO add proper materials and colors as specified above
6. DO structure the code exactly as shown in the example
7. DO NOT include any scene/renderer creation (they are provided)
8. DO NOT include any import statements or React code

The code should focus on solid geometry visualization with proper lighting and materials, not wireframes."""

model="claude-3-5-sonnet-latest"
max_tokens=4096


# Function to encode an image in Base64 format
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            # Read the binary content of the file and encode it in Base64
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"An error occurred while encoding the image: {e}")
        return None
    

# Function to send context, prompt, and an image to Claude's API
def generate_3d_geometry(image_path):
    # try:
        # Encode the image if provided
        encoded_image = None
        if image_path:
            encoded_image = encode_image_to_base64(image_path)
            if not encoded_image:
                print("Failed to encode the image. Exiting.")
                return None

        # Construct the messages array
        messages = [
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
        ]

        # Add the image content block if an image is provided
        if encoded_image:
            messages[0]["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",  # Specify PNG as the media type
                    "data": encoded_image,
                },
            })

        # Send the request to Claude's API
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            # system=fixed_context,  # Top-level system parameter for context
            messages=messages,
        )


        return response
