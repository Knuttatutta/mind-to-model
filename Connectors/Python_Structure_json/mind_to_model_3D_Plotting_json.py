import json
import numpy as np
import math
from openseespy.opensees import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib
matplotlib.use('tkAgg')

# Load JSON file
with open('building_geometry.json', 'r') as f:
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

# Convert nodes to a list for easier handling
nodes = list(nodes)

# Initialize a list to store member elements (edges)
member_elements = []

# Create member elements for walls
for wall in data["components"]["walls"]:
    vertices = wall["vertices"]
    for i in range(len(vertices)):
        current_vertex = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = (vertices[(i + 1) % len(vertices)]["x"], vertices[(i + 1) % len(vertices)]["y"],
                       vertices[(i + 1) % len(vertices)]["z"])
        member_elements.append((current_vertex, next_vertex))

# Create member elements for floors
for floor in data["components"]["floors"]:
    vertices = floor["vertices"]
    for i in range(len(vertices)):
        current_vertex = (vertices[i]["x"], vertices[i]["y"], vertices[i]["z"])
        next_vertex = (vertices[(i + 1) % len(vertices)]["x"], vertices[(i + 1) % len(vertices)]["y"],
                       vertices[(i + 1) % len(vertices)]["z"])
        member_elements.append((current_vertex, next_vertex))

# Find bottom nodes
def find_bottom_nodes(nodes):
    min_z = min([node[2] for node in nodes])
    bottom_nodes = [node for node in nodes if node[2] == min_z]
    return bottom_nodes

# Get bottom nodes and non-bottom nodes
bottom_nodes = find_bottom_nodes(nodes)
non_bottom_nodes = [node for node in nodes if node not in bottom_nodes]

# Create a 3D plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Plot non-bottom nodes as red dots
if non_bottom_nodes:  # Check if there are any non-bottom nodes
    x_nodes = [node[0] for node in non_bottom_nodes]
    y_nodes = [node[1] for node in non_bottom_nodes]
    z_nodes = [node[2] for node in non_bottom_nodes]
    ax.scatter(x_nodes, y_nodes, z_nodes, color='r', s=50, label='Nodes')

# Plot bottom nodes as green dots
bottom_x = [node[0] for node in bottom_nodes]
bottom_y = [node[1] for node in bottom_nodes]
bottom_z = [node[2] for node in bottom_nodes]
ax.scatter(bottom_x, bottom_y, bottom_z, color='g', s=100, label='Fixed Support Nodes')

# Plot member elements (edges) as lines connecting the nodes
for member in member_elements:
    x_line = [member[0][0], member[1][0]]
    y_line = [member[0][1], member[1][1]]
    z_line = [member[0][2], member[1][2]]
    ax.plot(x_line, y_line, z_line, color='b', marker='o')

# Labels and title
ax.set_xlabel('X [m]',fontsize=20, labelpad=20)
ax.set_ylabel('Y [m]',fontsize=20, labelpad=20)
ax.set_zlabel('Z [m]',fontsize=20, labelpad=20)
ax.set_title('3D Structural Frame',fontsize=24)

# Increase the font size for tick labels
# Increase the font size for tick labels and move them outward using the `pad` parameter
ax.tick_params(axis='x', which='major', labelsize=20, pad=10)  # Move x-axis tick labels outward
ax.tick_params(axis='y', which='major', labelsize=20, pad=10)  # Move y-axis tick labels outward
ax.tick_params(axis='z', which='major', labelsize=20, pad=10)  # Move z-axis tick labels outward


#ax.tick_params(axis='both', which='major', labelsize=20)  # Major ticks
#ax.tick_params(axis='both', which='minor', labelsize=20)  # Minor ticks

# Add legend with increased font size
#ax.legend(fontsize=20)  # Set fontsize directly in the legend function

# Add legend with increased font size and reposition it to the top-right corner
ax.legend(fontsize=20, loc='upper right', bbox_to_anchor=(1.3, 1))

# Adjust margins to move the plot inward and make space for larger labels
plt.subplots_adjust(left=0.2, right=0.8, top=0.9, bottom=0.2)

# Add legend
#ax.legend()

# Ensure layout is not clipped
plt.tight_layout()

# Save the figure
file_path = "./3D_plot1.png"
plt.savefig(file_path, format='png', dpi=300)

print(f"Plot saved as: {file_path}")