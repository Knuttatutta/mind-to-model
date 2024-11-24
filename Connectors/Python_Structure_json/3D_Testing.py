import json
import numpy as np
import math
from openseespy.opensees import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
matplotlib.use('tkAgg')

# Load JSON file
with open('test_image_geometry.json', 'r') as f:
    data = json.load(f)

# Extract walls and floors
walls = data["components"]["walls"]
floors = data["components"]["floors"]

# Initialize OpenSees model
wipe()
model('basic', '-ndm', 3, '-ndf', 6)  # 3D model, 6 DOFs per node

# Extract all coordinates (vertices) from walls and floors
nodes = set()

# Collect vertices from walls
for wall in data["components"]["walls"]:
    for vertex in wall["vertices"]:
        nodes.add((vertex["x"], vertex["y"], vertex["z"]))

# Collect vertices from floors
for floor in data["components"]["floors"]:
    for vertex in floor["vertices"]:
        nodes.add((vertex["x"], vertex["y"], vertex["z"]))

# Display the unique nodes (coordinates)
for node in nodes:
    print(node)

# Convert nodes to a list for easier handling
nodes = list(nodes)

# Initialize a list to store member elements (edges)
member_elements = []

# Create member elements for walls
for wall in data["components"]["walls"]:
    vertices = wall["vertices"]
    for i in range(len(vertices)):
        # Get the current and next vertices
        current_vertex = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = (vertices[(i + 1) % len(vertices)]["x"], vertices[(i + 1) % len(vertices)]["y"],
                       vertices[(i + 1) % len(vertices)]["z"])

        # Create member element (edge) between the two vertices
        member_elements.append((current_vertex, next_vertex))

# Create member elements for floors
for floor in data["components"]["floors"]:
    vertices = floor["vertices"]
    for i in range(len(vertices)):
        # Get the current and next vertices
        current_vertex = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = (vertices[(i + 1) % len(vertices)]["x"], vertices[(i + 1) % len(vertices)]["y"],
                       vertices[(i + 1) % len(vertices)]["z"])

        # Create member element (edge) between the two vertices
        member_elements.append((current_vertex, next_vertex))

# Display the member elements (edges)
for member in member_elements:
    print(member)

# Extract x, y, z coordinates
x = [node[0] for node in nodes]
y = [node[1] for node in nodes]
z = [node[2] for node in nodes]




## BOUNDARY CONDITIONS
# Function to find the bottom nodes
def find_bottom_nodes(nodes):
    # Find the minimum Z-coordinate value (bottom of the structure)
    min_z = min([node[2] for node in nodes])

    # Identify all nodes with the minimum Z value (bottom nodes)
    bottom_nodes = [node for node in nodes if node[2] == min_z]

    return bottom_nodes


# Function to apply boundary conditions
def apply_boundary_conditions(nodes):
    # Create a dictionary to store the boundary conditions
    boundary_conditions = {}

    # Identify the bottom nodes
    bottom_nodes = find_bottom_nodes(nodes)

    # For each node, apply the boundary condition (fix it in all directions if it's a bottom node)
    for node in nodes:
        # If it's a bottom node, apply boundary conditions (fix in all directions)
        if node in bottom_nodes:
            boundary_conditions[node] = {"x": 0, "y": 0, "z": 0}  # Fix all directions
        else:
            boundary_conditions[node] = {"x": None, "y": None, "z": None}  # No constraint

    return boundary_conditions


# Example usage
boundary_conditions = apply_boundary_conditions(nodes)

# Display the boundary conditions
for node, condition in boundary_conditions.items():
    print(f"Node {node} -> Boundary Conditions: {condition}")

# Convert nodes to separate x, y, z coordinates for plotting
x_nodes, y_nodes, z_nodes = zip(*nodes)

# Create a 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot nodes as red dots
ax.scatter(x, y, z, color='r', s=50, label='Nodes')

# Plot member elements (edges) as lines connecting the nodes
for member in member_elements:
    x_line = [member[0][0], member[1][0]]
    y_line = [member[0][1], member[1][1]]
    z_line = [member[0][2], member[1][2]]
    ax.plot(x_line, y_line, z_line, color='b', marker='o')

# Labels and title
ax.set_xlabel('X [m]')
ax.set_ylabel('Y [m]')
ax.set_zlabel('Z [m]')
ax.set_title('3D Structural Frame')


# Show plot
plt.show()

# Ensure layout is not clipped
plt.tight_layout()

# Save the figure before displaying it
file_path = "./3D_plot.png"  # Save in the current directory
plt.savefig(file_path, format='png', dpi=300)  # Save with high resolution

# Display the plot
#plt.show()

print(f"Plot saved as: {file_path}")


# Step 4: Define Materials and Geometric Transformation for Beam Elements
b= 0.2 #m width
h=0.4 #m height
E = 2.0e11  # Young's modulus (Pa)
A = b*h    # Cross-sectional area (m^2)
G = 8.0e10  # Shear modulus (Pa) - Example value
J = 1.0e-4  # Torsional constant (m^4) - Example value
Iy = (b*h**3)/12  # Moment of inertia about the y-axis (m^4)
Iz = (b*h**3)/12  # Moment of inertia about the z-axis (m^4)
gamma=b*h*7850 #(kg/m)
# Cross-section for visualisation purposes only
shape='rect'

# Elements
transfType='Linear'
shapes={}
memberLengths=[]
for n, mbr in enumerate(member):
    transfTag = n + 1  # transform tag for this element
    eleTag = n + 1  # element tag for this element

    shapes[eleTag] = [shape, [b, h]]

    node_i = mbr[0]
    node_j = mbr[1]

    # Accessing the coordinates correctly
    ix = nodes[node_i - 1][0]  # x-coordinate of node_i
    iy = nodes[node_i - 1][1]  # y-coordinate of node_i
    iz = nodes[node_i - 1][2]  # z-coordinate of node_i

    jx = nodes[node_j - 1][0]  # x-coordinate of node_j
    jy = nodes[node_j - 1][1]  # y-coordinate of node_j
    jz = nodes[node_j - 1][2]  # z-coordinate of node_j

    dx = jx - ix
    dy = iy - jy
    dz = iz - jz
    length = math.sqrt(dx**2 + dy**2 + dz**2)
    memberLengths.append(length)

    local_x_unit = np.array([dx, dy, dz]) / length

    i_offset = np.array([ix, iy, iz + 1])  # Adding 1 to the z-coordinate of node_i
    j_offset = np.array([jx, jy, jz])
    node_k = i_offset + 0.5 * (j_offset - i_offset)
    node_i = np.array([ix, iy, iz])
    vector_in_plane = node_k - node_i
    local_y_vector = vector_in_plane - np.dot(vector_in_plane, local_x_unit) * local_x_unit
    magY = math.sqrt(local_y_vector[0]**2 + local_y_vector[1]**2 + local_y_vector[2]**2)
    local_y_unit = local_y_vector / magY

    local_z_unit = np.cross(local_x_unit, local_y_unit)

    vecxz = local_z_unit


    # Define a geometric transformation for this member
    #geomTransf(transfType, transfTag, vecxz[0], vecxz[1], vecxz[2])

    # Create the beam element using the transformation
    #element('elasticBeamColumn', eleTag, node_i, node_j, A, E, G, J, Iy, Iz, transfTag)

    # Define geometric transformation for beam element
    # geomTransf('Linear', transfTag, dx / length, dy / length, dz / length)

    # Create the elastic beam-column element
    # element('elasticBeamColumn', eleTag, node_i, node_j, A, E, G, J, Iy, Iz, transfTag)


    #geomTransf('Linear', transfTag, *local_x_unit)

    # Create the elastic beam-column element
    #element('elasticBeamColumn', eleTag, node_i, node_j, A, E, G, J, Iy, Iz, transfTag)


# Define geometric transformations for 3D elements
# For columns: local z-axis along global Y axis
#geomTransf('Linear', 1, 0, 1, 0)  # columns
# For beams in X direction: local y-axis along global Z axis
#ops.geomTransf('Linear', 2, 0, 0, 1)  # beams in X direction
# For beams in Y direction: local y-axis along global Z axis
#ops.geomTransf('Linear', 3, 1, 0, 0)  # beams in Y direction

# Create elements
#element_counter = 1

#element('elasticBeamColumn', element_counter, node_i, node_j, A, E, G, J, Iy, Iz, 1)

