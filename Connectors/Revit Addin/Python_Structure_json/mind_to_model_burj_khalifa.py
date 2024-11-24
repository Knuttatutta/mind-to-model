"""
Prompt:

Perform a dynamic structural analysis with a simplified 2D model of the attached building, but should still resemble the actual building, but in 2D.
* Use the same number of levels as in the real building
* Apply a sinusoidal dynamic load at every level of the building
* Make the time steps relatively large so that we see a lot of swaying
* Make sure that the load and analysis are defined as simply as possible to avoid errors.
* Make sure all steps are included like setting the load pattern
* Make sure there no duplicated node tags
* If you use the geomTransf function, don't call it geomTransform
* Use opsvis and matplotlib to animate the sway back and forth of the 2D frame
* Make sure the matplotlib backend TkAgg is enabled
The following code has worked really well in the past to animate:
# Animation
num_frames = len(time_points)
scale_factor = 50  # Adjust this to make displacements visible
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
    ax.set_xlim(- bay_width *2 2 * (num_bays + 1) + 2, bay_width * 2 * (num_bays + 1) + 2)
    ax.set_ylim(-1, story_height * (num_stories + 1))
    ax.set_aspect('equal')
    plt.pause(0.01)
plt.ioff()
plt.show()

Can you also add some additional plotting to get some insight into the analysis?
"""


import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.gridspec import GridSpec
plt.switch_backend('TkAgg')

# [Previous initialization code remains the same up to the analysis part]
# Initialize model
ops.wipe()
ops.model('basic', '-ndm', 2, '-ndf', 3)

# Model parameters
num_stories = 163
story_height = 4.0
num_bays = 1
bay_width = 30.0

# Material properties
E = 32000000
A = 4.0
I = 2.0

# Create nodes
node_tags = {}
for floor in range(num_stories + 1):
    for bay in range(num_bays + 1):
        node_tag = floor * (num_bays + 1) + bay + 1
        x_coord = bay * bay_width
        y_coord = floor * story_height
        ops.node(node_tag, x_coord, y_coord)
        node_tags[(floor, bay)] = node_tag
        if floor == 0:
            ops.fix(node_tag, 1, 1, 1)

# Define geometric transformation
ops.geomTransf('PDelta', 1)

# Create elements (columns and beams)
for floor in range(num_stories):
    for bay in range(num_bays + 1):
        node1 = node_tags[(floor, bay)]
        node2 = node_tags[(floor + 1, bay)]
        element_tag = floor * (num_bays + 1) + bay + 1
        ops.element('elasticBeamColumn', element_tag, node1, node2, A, E, I, 1)

beam_tag_offset = (num_stories + 1) * (num_bays + 1)
for floor in range(1, num_stories + 1):
    for bay in range(num_bays):
        node1 = node_tags[(floor, bay)]
        node2 = node_tags[(floor, bay + 1)]
        element_tag = beam_tag_offset + floor * num_bays + bay + 1
        ops.element('elasticBeamColumn', element_tag, node1, node2, A, E, I, 1)

# Mass
for floor in range(1, num_stories + 1):
    for bay in range(num_bays + 1):
        node_tag = node_tags[(floor, bay)]
        ops.mass(node_tag, 100.0, 100.0, 0.0)

# Analysis parameters
dt = 0.1
duration = 15.0
num_steps = int(duration / dt)
time_points = np.linspace(0, duration, num_steps)

# Create load pattern
ops.timeSeries('Sine', 1, 0.0, duration, 2.0)
ops.pattern('UniformExcitation', 1, 1, '-accel', 1)

# Rayleigh Damping
ops.rayleigh(0.02, 0.0, 0.0, 0.0)

# Analysis settings
ops.wipeAnalysis()
ops.algorithm('Newton')
ops.system('BandGen')
ops.numberer('RCM')
ops.constraints('Plain')
ops.integrator('Newmark', 0.5, 0.25)
ops.analysis('Transient')

# Perform analysis and store results
displacements = {node: [] for node in node_tags.values()}
for t in time_points:
    ops.analyze(1, dt)
    for node in node_tags.values():
        displacements[node].append(ops.nodeDisp(node, 1))

# Create main figure with subplots
fig = plt.figure(figsize=(20, 15))
gs = GridSpec(3, 2, figure=fig)

# Set default larger font sizes for better readability
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# Subplot for building animation
ax_building = fig.add_subplot(gs[:, 0])
scale_factor = 50

# Create other subplots
ax_time_history = fig.add_subplot(gs[0, 1])
ax_drift = fig.add_subplot(gs[1, 1])
ax_envelope = fig.add_subplot(gs[2, 1])

# Process data for additional plots
top_floor_node = node_tags[(num_stories, 0)]
top_floor_disp = np.array(displacements[top_floor_node])

# Calculate story drifts
story_drifts = {}
for floor in range(1, num_stories + 1):
    node_bottom = node_tags[(floor-1, 0)]
    node_top = node_tags[(floor, 0)]
    drift = np.array(displacements[node_top]) - np.array(displacements[node_bottom])
    story_drifts[floor] = drift / story_height * 100  # Convert to percentage

# Calculate maximum displacement envelope
max_disps = []
for floor in range(num_stories + 1):
    node = node_tags[(floor, 0)]
    max_disp = max(abs(np.array(displacements[node])))
    max_disps.append(max_disp)

def animate(frame):
    # Clear building animation
    ax_building.clear()
    ax_building.grid(True, linestyle='--', alpha=0.7)
    ax_building.set_xlabel('Width (m)')
    ax_building.set_ylabel('Height (m)')
    ax_building.set_title('Building Dynamic Response')

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
            ax_building.plot([x1, x2], [y1, y2], 'b-', linewidth=1)

    # Draw beams
    for floor in range(1, num_stories + 1):
        for bay in range(num_bays):
            node1 = node_tags[(floor, bay)]
            node2 = node_tags[(floor, bay + 1)]
            x1 = bay * bay_width + scale_factor * displacements[node1][frame]
            y1 = floor * story_height
            x2 = (bay + 1) * bay_width + scale_factor * displacements[node2][frame]
            y2 = floor * story_height
            ax_building.plot([x1, x2], [y1, y2], 'r-', linewidth=1)

    ax_building.set_xlim(-bay_width * 2, bay_width * 3)
    ax_building.set_ylim(-1, story_height * (num_stories + 1))
    ax_building.set_aspect('equal')

    # Update time history plot
    ax_time_history.clear()
    ax_time_history.plot(time_points[:frame+1], top_floor_disp[:frame+1], 'b-', linewidth=2, label='Top Floor')
    ax_time_history.set_xlabel('Time (s)')
    ax_time_history.set_ylabel('Displacement (m)')
    ax_time_history.set_title('Top Floor Displacement Time History')
    ax_time_history.grid(True, linestyle='--', alpha=0.7)
    ax_time_history.legend()

    # Update story drift plot
    ax_drift.clear()
    selected_floors = [1, num_stories//4, num_stories//2, num_stories]  # Selected floors for clarity
    colors = ['b', 'g', 'r', 'purple']  # Different colors for each floor
    for floor, color in zip(selected_floors, colors):
        ax_drift.plot(time_points[:frame+1], story_drifts[floor][:frame+1],
                     color=color, linewidth=2, label=f'Floor {floor}')
    ax_drift.set_xlabel('Time (s)')
    ax_drift.set_ylabel('Story Drift (%)')
    ax_drift.set_title('Story Drift Time History')
    ax_drift.grid(True, linestyle='--', alpha=0.7)
    ax_drift.legend()

    # Update max displacement envelope
    ax_envelope.clear()
    floors = np.arange(num_stories + 1)
    ax_envelope.plot(max_disps, floors, 'r-', linewidth=2, label='Maximum')
    if frame > 0:
        current_disps = [abs(displacements[node_tags[(floor, 0)]][frame]) for floor in floors]
        ax_envelope.plot(current_disps, floors, 'b--', linewidth=2, label='Current', alpha=0.7)
    ax_envelope.set_xlabel('Maximum Displacement (m)')
    ax_envelope.set_ylabel('Floor')
    ax_envelope.set_title('Displacement Envelope')
    ax_envelope.grid(True, linestyle='--', alpha=0.7)
    ax_envelope.legend()

    # Adjust layout
    plt.tight_layout()
    return ax_building, ax_time_history, ax_drift, ax_envelope

# Create animation
anim = FuncAnimation(fig, animate, frames=len(time_points), interval=50, blit=False)

# Save animation
writer = PillowWriter(fps=20)
anim.save('building_analysis.gif', writer=writer)

plt.show()