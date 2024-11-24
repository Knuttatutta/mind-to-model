
import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const Building = () => {
  const mountRef = useRef(null);

  useEffect(() => {
    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    const renderer = new THREE.WebGLRenderer();
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0xf0f0f0);
    mountRef.current.appendChild(renderer.domElement);

    // Create building levels
    const createBuildingLevel = (width, height, depth, yPosition) => {
      const geometry = new THREE.BoxGeometry(width, height, depth);
      const material = new THREE.LineBasicMaterial({ 
        color: 0x000000,
        wireframe: true,
        wireframeLinewidth: 2
      });
      const level = new THREE.Mesh(geometry, material);
      level.position.y = yPosition;
      return level;
    };

    // Create building levels with decreasing sizes
    const buildingGroup = new THREE.Group();
    
    // Bottom level
    const level1 = createBuildingLevel(4, 2, 4, 1);
    buildingGroup.add(level1);
    
    // Middle level
    const level2 = createBuildingLevel(3, 2, 3, 3);
    buildingGroup.add(level2);
    
    // Top level
    const level3 = createBuildingLevel(2, 2, 2, 5);
    buildingGroup.add(level3);

    // Add entrance
    const entranceGeometry = new THREE.BoxGeometry(1, 0.5, 0.1);
    const entranceMaterial = new THREE.LineBasicMaterial({ 
      color: 0x000000,
      wireframe: true
    });
    const entrance = new THREE.Mesh(entranceGeometry, entranceMaterial);
    entrance.position.set(0, 0, 2.1);
    buildingGroup.add(entrance);

    // Add windows
    const addWindows = (level, size, count) => {
      const windowGeometry = new THREE.PlaneGeometry(0.3, 0.3);
      const windowMaterial = new THREE.LineBasicMaterial({ 
        color: 0x000000,
        wireframe: true
      });

      for (let x = -size/2 + 0.5; x < size/2; x += size/count) {
        for (let y = -0.5; y < 0.5; y += 0.5) {
          // Front windows
          const windowMesh = new THREE.Mesh(windowGeometry, windowMaterial);
          windowMesh.position.set(x, level + y, size/2 + 0.01);
          buildingGroup.add(windowMesh);
          
          // Back windows
          const backWindow = windowMesh.clone();
          backWindow.position.z = -size/2 - 0.01;
          buildingGroup.add(backWindow);
          
          // Side windows
          const sideWindow = windowMesh.clone();
          sideWindow.rotation.y = Math.PI / 2;
          sideWindow.position.set(size/2 + 0.01, level + y, x);
          buildingGroup.add(sideWindow);
          
          const otherSideWindow = sideWindow.clone();
          otherSideWindow.position.x = -size/2 - 0.01;
          buildingGroup.add(otherSideWindow);
        }
      }
    };

    // Add windows to each level
    addWindows(1, 4, 4); // Bottom level
    addWindows(3, 3, 3); // Middle level
    addWindows(5, 2, 2); // Top level

    scene.add(buildingGroup);

    // Camera position
    camera.position.set(10, 10, 10);
    camera.lookAt(0, 0, 0);

    // Add controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Animation
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle window resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      mountRef.current.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} />;
};

export default Building;
