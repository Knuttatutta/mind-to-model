
// Create the main building structure
const buildingGeometry = new THREE.BoxGeometry(20, 15, 10);
const buildingMaterial = new THREE.MeshPhongMaterial({ color: 0xcccccc });
const building = new THREE.Mesh(buildingGeometry, buildingMaterial);

// Create window grid
const windowRowCount = 8;
const windowColumnCount = 6;
const windowWidth = 1.8;
const windowHeight = 1.5;
const windowDepth = 0.1;

const windowGeometry = new THREE.BoxGeometry(windowWidth, windowHeight, windowDepth);
const windowMaterial = new THREE.MeshPhongMaterial({ color: 0x444444 });
const windowGroup = new THREE.Group();

// Create and position windows
for (let row = 0; row < windowRowCount; row++) {
    for (let col = 0; col < windowColumnCount; col++) {
        const window = new THREE.Mesh(windowGeometry, windowMaterial);
        
        // Position each window
        window.position.x = (col - (windowColumnCount - 1) / 2) * (windowWidth + 0.5);
        window.position.y = (row - (windowRowCount - 1) / 2) * (windowHeight + 0.3);
        window.position.z = 5.1; // Slightly in front of the main building
        
        windowGroup.add(window);
    }
}

// Create roof border
const roofBorderGeometry = new THREE.BoxGeometry(20.5, 0.5, 10.5);
const roofBorderMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 });
const roofBorder = new THREE.Mesh(roofBorderGeometry, roofBorderMaterial);
roofBorder.position.y = 7.75;

// Create side panels (stripes on the left side)
const sidePanelGroup = new THREE.Group();
const stripCount = 15;
const stripHeight = 0.3;

for (let i = 0; i < stripCount; i++) {
    const stripGeometry = new THREE.BoxGeometry(0.2, stripHeight, 10);
    const stripMaterial = new THREE.MeshPhongMaterial({ color: 0x999999 });
    const strip = new THREE.Mesh(stripGeometry, stripMaterial);
    
    strip.position.x = -9.9;
    strip.position.y = (i - stripCount/2) * (stripHeight + 0.2);
    
    sidePanelGroup.add(strip);
}

// Add everything to the scene
scene.add(building);
scene.add(windowGroup);
scene.add(roofBorder);
scene.add(sidePanelGroup);

// Position camera
camera.position.set(30, 20, 30);
camera.lookAt(0, 0, 0);

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
