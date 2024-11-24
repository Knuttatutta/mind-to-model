
// Create materials
const buildingMaterial = new THREE.MeshPhongMaterial({
    color: 0xcccccc,
    wireframe: false
});

const lineMaterial = new THREE.LineBasicMaterial({
    color: 0x000000,
    linewidth: 1
});

// Create the main building group
const building = new THREE.Group();

// Define dimensions for each tier (from bottom to top)
const tiers = [
    { width: 4, height: 2, depth: 4 },
    { width: 3, height: 2, depth: 3 },
    { width: 2, height: 2, depth: 2 }
];

// Create each tier
tiers.forEach((tier, index) => {
    const geometry = new THREE.BoxGeometry(tier.width, tier.height, tier.depth);
    const cube = new THREE.Mesh(geometry, buildingMaterial);
    
    // Position each tier
    const yOffset = index * 2; // Stack tiers vertically
    cube.position.y = yOffset + tier.height/2;
    
    // Add edges to each tier
    const edges = new THREE.EdgesGeometry(geometry);
    const lines = new THREE.LineSegments(edges, lineMaterial);
    lines.position.copy(cube.position);
    
    building.add(cube);
    building.add(lines);
});

// Create entrance
const entranceGeometry = new THREE.BoxGeometry(0.8, 0.8, 0.1);
const entrance = new THREE.Mesh(entranceGeometry, buildingMaterial);
entrance.position.set(0, 0.4, 2.05);
building.add(entrance);

// Create windows
const createWindow = (x, y, z) => {
    const windowGeometry = new THREE.BoxGeometry(0.4, 0.4, 0.1);
    const window = new THREE.Mesh(windowGeometry, buildingMaterial);
    window.position.set(x, y, z);
    return window;
};

// Add windows to each tier
// Bottom tier windows
[-1.2, 0, 1.2].forEach(x => {
    [0.7, 1.5].forEach(y => {
        building.add(createWindow(x, y, 2));
    });
});

// Middle tier windows
[-0.8, 0.8].forEach(x => {
    [2.7, 3.5].forEach(y => {
        building.add(createWindow(x, y, 1.5));
    });
});

// Top tier windows
[4.7, 5.5].forEach(y => {
    building.add(createWindow(0, y, 1));
});

// Center and add the building to the scene
building.position.y = -1;
scene.add(building);

// Add lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(5, 5, 5);
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