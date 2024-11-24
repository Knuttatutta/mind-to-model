import json
import numpy as np
import math
from openseespy.opensees import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib

matplotlib.use('tkAgg')

# Initialize OpenSees model
wipe()
model('basic', '-ndm', 3, '-ndf', 6)  # 3D model, 6 DOFs per node

# Material and section properties
b = 0.2  # width (m)
h = 0.4  # height (m)
E = 2.0e11  # Young's modulus (Pa)
G = 8.0e10  # Shear modulus (Pa)
nu = 0.3  # Poisson's ratio
rho = 7850  # Density (kg/m³)

# Calculate section properties
A = b * h  # Cross-sectional area (m²)
Iz = (b * h ** 3) / 12  # Moment of inertia about z-axis (m⁴)
Iy = (h * b ** 3) / 12  # Moment of inertia about y-axis (m⁴)
J = b * h * (b ** 2 + h ** 2) / 12  # Torsional constant (m⁴)

# Define materials and sections
matTag = 1
sectionTag = 1

# Elastic material
uniaxialMaterial('Elastic', matTag, E)

# Elastic section
section('Elastic', sectionTag, E, A, Iz, Iy, G, J)

# Load geometry from JSON
with open('building_geometry.json', 'r') as f:
    data = json.load(f)

# Extract and create nodes
nodes = set()
for wall in data["components"]["walls"]:
    for vertex in wall["vertices"]:
        nodes.add((vertex["x"], vertex["y"], vertex["z"]))
for floor in data["components"]["floors"]:
    for vertex in floor["vertices"]:
        nodes.add((vertex["x"], vertex["y"], vertex["z"]))

nodes = list(nodes)

# Create nodes in OpenSees
for i, node_coords in enumerate(nodes, 1):
    node(i, *node_coords)

# Create member elements and store their vectors
member_elements = []
member_vectors = []
for wall in data["components"]["walls"]:
    vertices = wall["vertices"]
    for i in range(len(vertices)):
        current = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = vertices[(i + 1) % len(vertices)]
        next_coords = (next_vertex["x"], next_vertex["y"], next_vertex["z"])
        member_elements.append((nodes.index(current) + 1, nodes.index(next_coords) + 1))

        # Calculate member vector
        dx = next_coords[0] - current[0]
        dy = next_coords[1] - current[1]
        dz = next_coords[2] - current[2]
        member_vectors.append((dx, dy, dz))

for floor in data["components"]["floors"]:
    vertices = floor["vertices"]
    for i in range(len(vertices)):
        current = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = vertices[(i + 1) % len(vertices)]
        next_coords = (next_vertex["x"], next_vertex["y"], next_vertex["z"])
        member_elements.append((nodes.index(current) + 1, nodes.index(next_coords) + 1))

        # Calculate member vector
        dx = next_coords[0] - current[0]
        dy = next_coords[1] - current[1]
        dz = next_coords[2] - current[2]
        member_vectors.append((dx, dy, dz))


# Function to create appropriate transformation for each element
def create_geometric_transformation(member_vector):
    dx, dy, dz = member_vector

    # Calculate vector magnitude
    length = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    # Normalize the vector
    x_axis = np.array([dx / length, dy / length, dz / length])

    # Choose appropriate perpendicular vector for local y-axis
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:  # Vertical member
        y_axis = np.array([1.0, 0.0, 0.0])
    else:
        # Use cross product with vertical direction to get perpendicular vector
        temp = np.cross(x_axis, np.array([0.0, 0.0, 1.0]))
        y_axis = temp / np.linalg.norm(temp)

    # Calculate local z-axis using cross product
    z_axis = np.cross(x_axis, y_axis)
    z_axis = z_axis / np.linalg.norm(z_axis)

    return y_axis[0], y_axis[1], y_axis[2], z_axis[0], z_axis[1], z_axis[2]


# Create elements with appropriate transformations
for i, ((node_i, node_j), member_vector) in enumerate(zip(member_elements, member_vectors), 1):
    # Create unique transformation for each element
    y_vec, z_vec = create_geometric_transformation(member_vector)[:3], create_geometric_transformation(member_vector)[
                                                                       3:]

    # Create geometric transformation
    geomTransfTag = i
    geomTransf('Linear', geomTransfTag, *y_vec)

    # Create element
    element('elasticBeamColumn', i, node_i, node_j, A, E, G, J, Iy, Iz, geomTransfTag)

# Find bottom and top nodes
bottom_z = min(node[2] for node in nodes)
top_z = max(node[2] for node in nodes)
bottom_nodes = [i + 1 for i, node in enumerate(nodes) if node[2] == bottom_z]
top_nodes = [i + 1 for i, node in enumerate(nodes) if node[2] == top_z]

# Fix bottom nodes
for node_tag in bottom_nodes:
    fix(node_tag, 1, 1, 1, 1, 1, 1)  # Fix all 6 DOFs

# Define mass
for node_tag in range(1, len(nodes) + 1):
    mass(node_tag, rho * A, rho * A, rho * A, rho * J, rho * Iy, rho * Iz)

# Time series for seismic loading
dt = 0.1  # Time step
duration = 10.0  # Duration in seconds
num_steps = int(duration / dt)
tStart = 0.0

# Create time series (simulated earthquake)
tsTag = 1
timeSeries('Sine', tsTag, 0.0, duration, 2.0)  # 2.0 Hz frequency

# Create load pattern
patternTag = 1
pattern('Plain', patternTag, tsTag)

# Apply forces to top nodes
max_force = 50000.0  # Maximum force in N
for node_tag in top_nodes:
    load(node_tag, max_force, max_force, 0.0, 0.0, 0.0, 0.0)  # Forces in X and Y directions

# Define Rayleigh damping parameters
omega1 = 2 * np.pi * 0.5  # First mode frequency (estimated)
omega2 = 2 * np.pi * 2.0  # Second mode frequency (estimated)
zeta = 0.05  # 5% damping ratio
a0 = 2 * zeta * omega1 * omega2 / (omega1 + omega2)
a1 = 2 * zeta / (omega1 + omega2)
rayleigh(a0, a1, 0.0, 0.0)

# Analysis settings
constraints('Plain')
numberer('RCM')
system('BandGen')
test('NormDispIncr', 1.0e-6, 10)
algorithm('Newton')
integrator('Newmark', 0.5, 0.25)
analysis('Transient')

# Storage for results
time_history = []
top_displacements = {node: {'x': [], 'y': [], 'z': []} for node in top_nodes}

# Perform the analysis
print("Starting analysis...")
for i in range(num_steps):
    t = i * dt
    ok = analyze(1, dt)

    if ok != 0:
        print(f"Convergence issue at time {t}")
        break

    time_history.append(t)
    for node in top_nodes:
        top_displacements[node]['x'].append(nodeDisp(node, 1))
        top_displacements[node]['y'].append(nodeDisp(node, 2))
        top_displacements[node]['z'].append(nodeDisp(node, 3))

    if i % 10 == 0:
        print(f"Analysis at {t:.1f}s completed")

# Plot results
fig= plt.figure(figsize=(12, 8))
#ax = fig.add_subplot(111, projection='2d')
for node in top_nodes:
    plt.plot(time_history, top_displacements[node]['x'], label=f'Node {node} - X')
 #   plt.plot(time_history, top_displacements[node]['y'], label=f'Node {node} - Y')

plt.xlabel('Time (s)',fontsize=20, labelpad=10)
plt.ylabel('Displacement (m)',fontsize=20, labelpad=10)

# Adjust tick parameters
plt.tick_params(axis='x', which='major', labelsize=20, pad=10)
plt.tick_params(axis='y', which='major', labelsize=20, pad=10)


plt.title('Top Node Displacements vs Time',fontsize=20)
plt.legend()
plt.grid(True)
plt.savefig('displacement_history.png')
plt.show()

# Calculate and print maximum displacements
print("\nMaximum Displacements:")
for node in top_nodes:
    max_x = max(abs(min(top_displacements[node]['x'])), abs(max(top_displacements[node]['x'])))
    max_y = max(abs(min(top_displacements[node]['y'])), abs(max(top_displacements[node]['y'])))
    print(f"Node {node}:")
    print(f"  Max X displacement: {max_x:.6f} m")
    print(f"  Max Y displacement: {max_y:.6f} m")

wipe()