import React, { useState, useEffect, useRef } from 'react';
import { RotateCcw } from 'lucide-react';
import { 
  Box, 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel 
} from '@mui/material';
import { Download } from 'lucide-react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import './App.css';
import LOGO from '../src/assets/logo.png'

// Process Navigation Component
const ProcessNavigation = ({ currentStep, hasImage, has3D }) => {
  // Define the base step that's always visible
  const getVisibleSteps = () => {
    const steps = [
      { id: 'description', label: 'Description' }
    ];

    // Add Visual Outcome step if image is generated
    if (hasImage) {
      steps.push({ id: 'visual', label: 'Visual Outcome' });
    }

    // Add 3D Outcome and Download steps if 3D is generated
    if (has3D) {
      steps.push({ id: '3d', label: '3D Outcome' });
      steps.push({ id: 'download', label: 'Download' });
    }

    return steps;
  };

  // Helper function to determine if step is active
  const isStepActive = (index) => {
    return index <= currentStep;
  };

  const steps = getVisibleSteps();

  return (
    <div className="process-navigation">
      {steps.map((step, index) => (
        <React.Fragment key={step.id}>
          <div 
            className={`process-step ${isStepActive(index) ? 'active' : ''}`}
            // Add animation classes for smooth entrance
            style={{
              animation: 'fadeSlideIn 0.5s ease forwards',
              animationDelay: `${index * 0.1}s`
            }}
          >
            <span className="step-text">{step.label}</span>
          </div>
          {index < steps.length - 1 && (
            <div 
              className="step-line"
              style={{
                animation: 'growLine 0.5s ease forwards',
                animationDelay: `${index * 0.1}s`
              }}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

const App = () => {
  const [prompt, setPrompt] = useState('');
  const [image, setImage] = useState(null);
  const [imageKey, setImageKey] = useState(null);
  const [loading, setLoading] = useState(false);
  const [size, setSize] = useState('medium');
  const [floors, setFloors] = useState(3);
  const [show3D, setShow3D] = useState(false);
  const [loading3D, setLoading3D] = useState(false);
  const [threeJsCode, setThreeJsCode] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);

  /**
 * Resets all state variables to their initial values
 * This effectively restarts the entire workflow
 */
  const handleReset = () => {
    // Reset form inputs
    setPrompt('');
    setSize('medium');
    setFloors(3);
    
    // Reset generation states
    setImage(null);
    setImageKey(null);
    setLoading(false);
    
    // Reset 3D states
    setShow3D(false);
    setLoading3D(false);
    setThreeJsCode(null);
    
    // Reset step tracking
    setCurrentStep(0);
  };

  // Update current step based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      
      // Calculate progress through the page (0 to 1)
      const progress = scrollPosition / (documentHeight - windowHeight);
      
      // Map progress to steps (0 to 4)
      const step = Math.min(Math.floor(progress * 5), 4);
      setCurrentStep(step);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleImageGeneration = async (e) => {
    e.preventDefault();
    if (!prompt) return;
    
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/generate-image/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, size, floors }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setImage(data.image_path);
        setImageKey(Date.now()); // Add this line to force re-render
        console.log('response was ok')
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handle3DGeneration = async () => {
    setLoading3D(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/generate-3d/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();
      console.log('Received test 3D data:', data);
      
      if (data.three_js_code) {
        setShow3D(true);
        setThreeJsCode(data.three_js_code);
        console.log('Using code from:', data.file_path);
      } else {
        console.error('No Three.js code in response');
      }

    } catch (error) {
      console.error('Error generating 3D:', error);
    } finally {
      setLoading3D(false);
    }
  };

  // Add this function to handle test mode
  const handleTest3D = async () => {
    setLoading3D(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/test-3d/');
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Server error:', errorData);
        return;
      }
      
      const data = await response.json();
      console.log('Received test 3D data:', data);
      
      if (data.three_js_code) {
        setThreeJsCode(data.three_js_code);
        console.log('Using code from:', data.file_path);
      } else {
        console.error('No Three.js code in response');
      }
    } catch (error) {
      console.error('Error loading test 3D:', error);
    } finally {
      setLoading3D(false);
    }
  };

  // Reference to store the current scene for exporting
  const sceneRef = useRef(null);

  // Function to handle GLTF export
  const handleGLTFExport = () => {
    if (!sceneRef.current) {
      console.error('No scene available to export');
      return;
    }

    // Initialize GLTFExporter
    const exporter = new GLTFExporter();

    // Export options
    const options = {
      trs: true, // Transform, Rotation, Scale
      binary: false, // Set to true for .glb format
      maxTextureSize: 4096
    };

    // Perform the export
    exporter.parse(
      sceneRef.current,
      (gltf) => {
        // Create download link
        const downloadLink = document.createElement('a');
        const blob = new Blob([JSON.stringify(gltf)], { type: 'application/json' });
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = 'scene.gltf';
        
        // Trigger download
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      },
      (error) => {
        console.error('An error occurred while exporting:', error);
      },
      options
    );
  };


const Dynamic3DViewer = ({ code }) => {
  const containerRef = useRef(null);
  
  useEffect(() => {
    if (!code || !containerRef.current) return;

    try {
      // Clear any existing content
      while (containerRef.current.firstChild) {
        containerRef.current.removeChild(containerRef.current.firstChild);
      }

      // Set up Three.js environment
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(
        75,
        containerRef.current.clientWidth / containerRef.current.clientHeight,
        0.1,
        1000
      );
      const renderer = new THREE.WebGLRenderer();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      containerRef.current.appendChild(renderer.domElement);

      // Execute the code
      const executeThreeJSCode = new Function(
        'THREE',
        'OrbitControls',
        'scene',
        'camera',
        'renderer',
        'container',
        code
      );

      executeThreeJSCode(
        THREE,
        OrbitControls,
        scene,
        camera,
        renderer,
        containerRef.current
      );

      // Add resize handler
      const handleResize = () => {
        camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
      };
      window.addEventListener('resize', handleResize);

      // Cleanup
      return () => {
        window.removeEventListener('resize', handleResize);
        if (containerRef.current?.firstChild) {
          containerRef.current.removeChild(renderer.domElement);
        }
      };
    } catch (error) {
      console.error('Error executing Three.js code:', error);
    }
  }, [code]);

  return (
    <div 
      ref={containerRef} 
      style={{ 
        width: '100%', 
        height: '500px',
        backgroundColor: '#f0f0f0',
        borderRadius: '4px'
      }} 
    />
  );
};

  return (
    <Box className="app-wrapper">
      <ProcessNavigation 
        currentStep={currentStep} 
        hasImage={Boolean(image)}
        has3D={Boolean(threeJsCode)}
      />
      <Container className="app-container">
        {/* Reset Button Container at the top */}
        <Box className="reset-container">
          <Button
            variant="outlined"
            startIcon={<RotateCcw className="w-4 h-4" />}
            onClick={handleReset}
            className="reset-button"
            // Disable reset if nothing to reset (initial state)
            disabled={!prompt && !image && !threeJsCode}
          >
            Reset
          </Button>
        </Box>
        {/* Logo */}
        <Box className="logo-container">
          <img 
            src={LOGO}
            alt="MindModel Logo" 
            className="logo-image"
          />
        </Box>

       
        {/* Input Section */}
        <Box className="input-section">
          <Typography className="description-label">Description</Typography>
          <Box component="form" onSubmit={handleImageGeneration} className="input-form">
            <TextField
              fullWidth
              placeholder="Enter your design idea..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              variant="outlined"
              className="text-input"
            />
            
            {/* Sliders */}
            <Box className="sliders-container">
              <Box className="slider-box">
                <FormControl fullWidth>
                  <InputLabel id="size-select-label">Size</InputLabel>
                  <Select
                    labelId="size-select-label"
                    id="size-select"
                    value={size}
                    label="Size"
                    onChange={(e) => setSize(e.target.value)}
                  >
                    <MenuItem value="small">Small</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="large">Large</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              <Box className="slider-box">
                <Typography className="slider-label">Number of Floors</Typography>
                <Slider
                  value={floors}
                  onChange={(_, value) => setFloors(value)}
                  min={1}
                  max={10}
                  aria-label="Floors"
                  valueLabelDisplay="auto"
                />
              </Box>
            </Box>

            <Button
              type="submit"
              variant="contained"
              className="general-button"
              disabled={loading || loading3D}
            >
              {loading ? 'Generating Image...' : 'Generate Image'}
            </Button>
          </Box>
        </Box>

        {/* Visual Outcome Section */}
        {image && (
          <Box className="outcome-section">
            <Box className="image-container">
              <img
                // src={`http://127.0.0.1:8000${image}`}
                src={`http://127.0.0.1:8000${image}?key=${imageKey}`}
                alt="Generated visual"
                className="generated-image"
              />
            </Box>

            <Box className="action-buttons">
              <Button
                variant="contained"
                className="general-button"
                onClick={handle3DGeneration}
                disabled={loading3D}
              >
                {loading3D ? 'Generating 3D...' : 'Create 3D Data'}
              </Button>
              <Button
                variant="outlined"
                className="outline-button"
                onClick={handleImageGeneration}
                disabled={loading3D}
              >
                {loading ? 'Recreating Image...' : 'Recreate Image'}
              </Button>
            </Box>
          </Box>
        )}

        {/* Dynamic 3D Visualization Section */}
        {threeJsCode && (
          <Box className="visualization-section">
            <Dynamic3DViewer code={threeJsCode} />

            {/* Download Options */}
            <Box className="download-options">
              {['Revit', '.json', 'Grasshopper'].map((format) => (
                <Button
                  key={format}
                  variant="contained"
                  startIcon={<Download className="w-4 h-4" />}
                  className="general-button"
                >
                  {format}
                </Button>
              ))}
              <Button
                variant="contained"
                startIcon={<Download className="w-4 h-4" />}
                className="general-button"
                onClick={handleGLTFExport}
              >
                .ifc
              </Button>
            </Box>
        </Box>
        )}
      </Container>
    </Box>
  );
};

export default App;

