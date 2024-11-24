// Create the scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff); // White background

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Add ambient lighting
const ambientLight = new THREE.AmbientLight(0x404040, 2); // Soft light
scene.add(ambientLight);

// Add directional light
const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 10, 7.5);
scene.add(directionalLight);

// Add OrbitControls
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; // Smooth rotation
controls.dampingFactor = 0.1;
controls.enablePan = true;
controls.enableZoom = true;
controls.minDistance = 1;
controls.maxDistance = 50;


// Set the camera position for better view
camera.position.set(0, 5, 20);

function loadModel(filePath, position, scale, rotation) {
    const loader = new THREE.GLTFLoader();
    loader.load(
        filePath,
        (gltf) => {
            const model = gltf.scene;

            // Calculate the bounding box
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());

            // Recenter the model to the origin and place its base on the ground
            model.position.set(
                -center.x + position.x,
                -box.min.y + position.y, // Align the base to y = 0
                -center.z + position.z
            );

            // Apply scale and rotation
            model.scale.set(scale.x, scale.y, scale.z);
            model.rotation.set(rotation.x, rotation.y, rotation.z);

            // Add the model to the scene
            scene.add(model);
        },
        undefined,
        (error) => {
            console.error('An error occurred while loading the model:', error);
        }
    );
}

// Define the models to load
const models = [
    { file: './assets/model_whole.glb', position: {x: 0, y: 0, z: 0}, scale: {x: 1, y: 1, z: 1}, rotation: {x: 0, y: 0, z: 0} }
    // { file: './assets/model_2.glb', position: {x: 2, y: 0, z: -1}, scale: {x: 0.5, y: 0.5, z: 0.5}, rotation: {x: 0, y: Math.PI / 4, z: 0} }
    // { file: './assets/model3.glb', position: {x: -2, y: 1, z: 1}, scale: {x: 0.8, y: 0.8, z: 0.8}, rotation: {x: 0, y: 0, z: Math.PI / 2} }
];

// Load all models
models.forEach((modelData) => {
    loadModel(modelData.file, modelData.position, modelData.scale, modelData.rotation);
});

// Create a flat green plane under the models
function addPlane() {
    // Create a plane geometry (width, height)
    const planeGeometry = new THREE.PlaneGeometry(100, 100); // Adjust size as needed
    const planeMaterial = new THREE.MeshStandardMaterial({ color: 0x00ff00 }); // Green material
    const plane = new THREE.Mesh(planeGeometry, planeMaterial);

    // Rotate the plane to lie flat (facing upwards)
    plane.rotation.x = -Math.PI / 2;

    // Position the plane (optional, depends on model heights)
    plane.position.y = 0;

    // Add the plane to the scene
    scene.add(plane);
}

// Call the function to add the plane
addPlane();

// Animation loop
function animate() {
    requestAnimationFrame(animate);

    // Update controls for smooth interaction
    controls.update();

    renderer.render(scene, camera);
}

// Start rendering
animate();

// Handle window resizing
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
