"""
Prompt:

Perform a dynamic structural analysis with a simplified 3D frame model of the attached building, but should still resemble the actual building, but in 3D.
* Use the same number of levels as in the real building
* Apply a sinusoidal dynamic load at every level of the building
* Make sure that the load and analysis are defined as simply as possible to avoid errors.
* Make sure there no duplicated node tags
* If you use the geomTransf function, don't call it geomTransform
* Enable the tkagg backend for matplotlib
* Really make sure that the aspect ratio of the actual building the image is captured in the model
* Use matplotlib to animate the sway back and forth of the 3D frame
* Separate transformation definitions for columns and beams in each primary direction
* Vectors that define local axes must be perpendicular to element axes
* Use the following time series: ops.timeSeries('Sine', 1, 0.0, 100.0, 2.0)  # 2.0 Hz frequency
* Ensure that the aspect ratio of the plot is equal
* Add mass definition to all nodes using ops.mass()
* Include eigenvalue analysis to compute structure periods
* Also include the load pattern
The following code has worked really well in the past to animate in 2D, so change it to 3D:

import matplotlib
matplotlib.use('tkagg')
# Animation
num_frames = len(time_points)
scale_factor = 1000  # Adjust this to make displacements visible
for frame in range(num_frames):
    ax.clear()
    ax.grid(True)
    ax.set_xlabel('Width (m)')
    ax.set_ylabel('Height (m)')
    ax.set_title(f'Dynamic Response at t = {time_points[frame]:.2f} s')
    # Plot deformed shape
    for floor in range(num_stories):
        for bay in range(num_bays + 1):
            # Draw columns
            node1 = node_tags[(floor, bay)]
            node2 = node_tags[(floor + 1, bay)]
            x1 = bay * bay_width + scale_factor * displacements[node1][frame]
            y1 = floor * story_height
            x2 = bay * bay_width + scale_factor * displacements[node2][frame]
            y2 = (floor + 1) * story_height
            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=2)
    # Draw beams
    for floor in range(1, num_stories + 1):
        for bay in range(num_bays):
            node1 = node_tags[(floor, bay)]
            node2 = node_tags[(floor, bay + 1)]
            x1 = bay * bay_width + scale_factor * displacements[node1][frame]
            y1 = floor * story_height
            x2 = (bay + 1) * bay_width + scale_factor * displacements[node2][frame]
            y2 = floor * story_height
            ax.plot([x1, x2], [y1, y2], 'r-', linewidth=2)
    ax.set_xlim(- bay_width * 10 * (num_bays + 1) + 2, bay_width * 10 * (num_bays + 1) + 2)
    ax.set_ylim(-1, story_height * (num_stories + 1))
    ax.set_aspect('equal')
    plt.pause(0.01)
plt.ioff()
plt.show()

"""


import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib

matplotlib.use('tkagg')

# Model generation
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 6)

# Structure parameters (based on image proportions)
num_stories = 15
num_bays_x = 4
num_bays_y = 3
story_height = 3.5  # meters
bay_width_x = 6.0  # meters
bay_width_y = 6.0  # meters

# Material properties
E = 32000000  # kN/m²
G = E / 2.4  # kN/m²
J = 1.0  # torsional moment of inertia
Iy = 0.4  # moment of inertia about y axis
Iz = 0.4  # moment of inertia about z axis
A = 0.09  # cross-sectional area in m²

# Create nodes and elements
node_tags = {}
for floor in range(num_stories + 1):
    for x in range(num_bays_x + 1):
        for y in range(num_bays_y + 1):
            node_tag = floor * 1000 + x * 100 + y
            node_tags[(floor, x, y)] = node_tag
            ops.node(node_tag, x * bay_width_x, y * bay_width_y, floor * story_height)

            # Add mass to nodes (except ground level)
            if floor > 0:
                ops.mass(node_tag, 100.0, 100.0, 100.0, 1.0, 1.0, 1.0)

# Fix base nodes
for x in range(num_bays_x + 1):
    for y in range(num_bays_y + 1):
        ops.fix(node_tags[(0, x, y)], 1, 1, 1, 1, 1, 1)

# Define geometric transformations
# Columns
ops.geomTransf('Linear', 1, 0, 1, 0)  # x-direction
ops.geomTransf('Linear', 2, 1, 0, 0)  # y-direction

# Beams
ops.geomTransf('Linear', 3, 0, 0, 1)  # x-direction beams
ops.geomTransf('Linear', 4, 0, 0, 1)  # y-direction beams

# Create material
ops.uniaxialMaterial('Elastic', 1, E)

# Create elements
# Columns (element tags 1-4999)
column_tag = 1
for floor in range(num_stories):
    for x in range(num_bays_x + 1):
        for y in range(num_bays_y + 1):
            node1 = node_tags[(floor, x, y)]
            node2 = node_tags[(floor + 1, x, y)]
            ops.element('elasticBeamColumn', column_tag, node1, node2, A, E, G, J, Iy, Iz, 1)
            column_tag += 1

# Beams in x-direction (element tags 5000-9999)
beam_x_tag = 5000
for floor in range(1, num_stories + 1):
    for x in range(num_bays_x):
        for y in range(num_bays_y + 1):
            node1 = node_tags[(floor, x, y)]
            node2 = node_tags[(floor, x + 1, y)]
            ops.element('elasticBeamColumn', beam_x_tag, node1, node2, A, E, G, J, Iy, Iz, 3)
            beam_x_tag += 1

# Beams in y-direction (element tags 10000-14999)
beam_y_tag = 10000
for floor in range(1, num_stories + 1):
    for x in range(num_bays_x + 1):
        for y in range(num_bays_y):
            node1 = node_tags[(floor, x, y)]
            node2 = node_tags[(floor, x, y + 1)]
            ops.element('elasticBeamColumn', beam_y_tag, node1, node2, A, E, G, J, Iy, Iz, 4)
            beam_y_tag += 1

# Eigenvalue analysis
num_modes = 3
eigenValues = ops.eigen(num_modes)
periods = [2 * np.pi / np.sqrt(omega) for omega in eigenValues]
print(f"Structure periods: {periods}")

# Dynamic analysis parameters
dt = 0.1
duration = 5.0
time_points = np.arange(0, duration + dt, dt)
num_steps = len(time_points)

# Create time series
ops.timeSeries('Sine', 1, 0.0, 100.0, 2.0)  # 2.0 Hz frequency

# Create load pattern
ops.pattern('UniformExcitation', 1, 1, '-accel', 1)

# Analysis configuration
ops.wipeAnalysis()
ops.algorithm('Newton')
ops.integrator('Newmark', 0.5, 0.25)
ops.analysis('Transient')
ops.system('BandGeneral')
ops.numberer('RCM')
ops.constraints('Plain')

# Store initial node coordinates
node_coords = {}
for floor in range(num_stories + 1):
    for x in range(num_bays_x + 1):
        for y in range(num_bays_y + 1):
            node_tag = node_tags[(floor, x, y)]
            node_coords[node_tag] = ops.nodeCoord(node_tag)

# Run analysis and store displacements
displacements = {}
for node_tag in node_tags.values():
    displacements[node_tag] = []

for t in time_points:
    ops.analyze(1, dt)
    for node_tag in node_tags.values():
        displacements[node_tag].append(ops.nodeDisp(node_tag))

# Add these imports at the top of the file
import matplotlib.animation as animation

# Replace the animation section with this (everything after "# Animation"):
# Animation
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
scale_factor = 10  # Adjust this to make displacements visible


def update(frame):
    ax.clear()
    ax.grid(True)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title(f'Dynamic Response at t = {time_points[frame]:.2f} s')

    # Plot deformed shape
    # Columns
    for floor in range(num_stories):
        for x in range(num_bays_x + 1):
            for y in range(num_bays_y + 1):
                node1 = node_tags[(floor, x, y)]
                node2 = node_tags[(floor + 1, x, y)]

                # Get original coordinates and add displacements
                x1, y1, z1 = node_coords[node1]
                x2, y2, z2 = node_coords[node2]

                dx1, dy1, dz1 = displacements[node1][frame][:3]
                dx2, dy2, dz2 = displacements[node2][frame][:3]

                ax.plot([x1 + scale_factor * dx1, x2 + scale_factor * dx2],
                        [y1 + scale_factor * dy1, y2 + scale_factor * dy2],
                        [z1 + scale_factor * dz1, z2 + scale_factor * dz2], 'b-', linewidth=2)

    # Beams in X direction
    for floor in range(1, num_stories + 1):
        for x in range(num_bays_x):
            for y in range(num_bays_y + 1):
                node1 = node_tags[(floor, x, y)]
                node2 = node_tags[(floor, x + 1, y)]

                x1, y1, z1 = node_coords[node1]
                x2, y2, z2 = node_coords[node2]

                dx1, dy1, dz1 = displacements[node1][frame][:3]
                dx2, dy2, dz2 = displacements[node2][frame][:3]

                ax.plot([x1 + scale_factor * dx1, x2 + scale_factor * dx2],
                        [y1 + scale_factor * dy1, y2 + scale_factor * dy2],
                        [z1 + scale_factor * dz1, z2 + scale_factor * dz2], 'r-', linewidth=2)

    # Beams in Y direction
    for floor in range(1, num_stories + 1):
        for x in range(num_bays_x + 1):
            for y in range(num_bays_y):
                node1 = node_tags[(floor, x, y)]
                node2 = node_tags[(floor, x, y + 1)]

                x1, y1, z1 = node_coords[node1]
                x2, y2, z2 = node_coords[node2]

                dx1, dy1, dz1 = displacements[node1][frame][:3]
                dx2, dy2, dz2 = displacements[node2][frame][:3]

                ax.plot([x1 + scale_factor * dx1, x2 + scale_factor * dx2],
                        [y1 + scale_factor * dy1, y2 + scale_factor * dy2],
                        [z1 + scale_factor * dz1, z2 + scale_factor * dz2], 'g-', linewidth=2)

    # Set axis limits
    ax.set_xlim(-5, bay_width_x * (num_bays_x + 1) + 5)
    ax.set_ylim(-5, bay_width_y * (num_bays_y + 1) + 5)
    ax.set_zlim(-1, story_height * (num_stories + 1))

    # Set equal aspect ratio
    ax.set_box_aspect([1, 1, 1])

    # Set viewing angle
    ax.view_init(elev=20, azim=45)  # You can adjust these angles

    return ax,


# Create animation
anim = animation.FuncAnimation(fig, update, frames=len(time_points),
                               interval=20, blit=False)

# Save animation
print("Saving animation... This might take a few minutes...")

# Save as MP4
# anim.save('building_dynamic.mp4', writer='ffmpeg', fps=30)

# Save as GIF (optional)
# anim.save('building_dynamic.gif', writer='pillow', fps=30)

plt.show()