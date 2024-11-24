// Debug output of extracted code
// Create the main building structure
const buildingGeometry = new THREE.BoxGeometry(8, 3, 4);
const buildingMaterial = new THREE.MeshPhongMaterial({ color: 0xcccccc });
const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
building.position.y = 1.5;

// Create window grid
const windowRowCount = 1;
const windowColumnCount = 3;
const windowGeometry = new THREE.BoxGeometry(0.8, 2, 0.1);
const windowMaterial = new THREE.MeshPhongMaterial({ color: 0x444444 });

const windowGroup = new THREE.Group();
for (let row = 0; row < windowRowCount; row++) {
    for (let col = 0; col < windowColumnCount; col++) {
        const window = new THREE.Mesh(windowGeometry, windowMaterial);
        window.position.set(
            (col - 1) * 1.5,
            0,
            2.01  // Slightly offset from the building face
        );
        windowGroup.add(window);
    }
}
building.add(windowGroup);

// Create roof and border elements
const roofGeometry = new THREE.BoxGeometry(8.4, 0.2, 4.4);
const roofMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 });
const roof = new THREE.Mesh(roofGeometry, roofMaterial);
roof.position.y = 3.1;
building.add(roof);

// Create base platform
const platformGeometry = new THREE.BoxGeometry(12, 0.4, 8);
const platformMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 });
const platform = new THREE.Mesh(platformGeometry, platformMaterial);
platform.position.y = -0.2;

// Create side panels
const sidePanelGeometry = new THREE.BoxGeometry(0.2, 3, 4);
const sidePanelMaterial = new THREE.MeshPhongMaterial({ color: 0x999999 });
const leftPanel = new THREE.Mesh(sidePanelGeometry, sidePanelMaterial);
const rightPanel = new THREE.Mesh(sidePanelGeometry, sidePanelMaterial);
leftPanel.position.set(-4.1, 1.5, 0);
rightPanel.position.set(4.1, 1.5, 0);

// Add everything to the scene
scene.add(building);
scene.add(platform);
scene.add(leftPanel);
scene.add(rightPanel);

// Add lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(10, 20, 10);

scene.add(ambientLight);
scene.add(directionalLight);

// Camera position
camera.position.set(15, 10, 15);
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