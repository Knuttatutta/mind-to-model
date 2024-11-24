import json
import plotly.graph_objects as go
import numpy as np

def create_wall_meshes(walls):
    """Create 3D meshes for walls"""
    wall_meshes = []

    for wall in walls:
        # Get the four vertices of the wall
        v1 = wall['vertices'][0]  # bottom-left
        v2 = wall['vertices'][1]  # bottom-right
        v3 = wall['vertices'][2]  # top-right
        v4 = wall['vertices'][3]  # top-left

        # Create vertices array with all 4 points
        vertices = np.array([
            [v1['x'], v1['y'], v1['z']],  # bottom-left
            [v2['x'], v2['y'], v2['z']],  # bottom-right
            [v3['x'], v3['y'], v3['z']],  # top-right
            [v4['x'], v4['y'], v4['z']]   # top-left
        ])

        # Create triangles for the wall face
        # Each rectangular wall face is made up of two triangles
        i = [0, 0]  # First vertex indices
        j = [1, 2]  # Second vertex indices
        k = [2, 3]  # Third vertex indices

        wall_meshes.append(
            go.Mesh3d(
                x=vertices[:, 0],
                y=vertices[:, 1],
                z=vertices[:, 2],
                i=i, j=j, k=k,
                opacity=0.5,
                color='lightgray',
                hoverinfo='text',
                text=f"Wall {wall['id']}",
                flatshading=True,
                lighting=dict(
                    ambient=0.8,
                    diffuse=0.8,
                    facenormalsepsilon=0,
                    roughness=0.5,
                    specular=0.05
                )
            )
        )

    return wall_meshes

def create_floor_meshes(floors):
    """Create 3D meshes for floors"""
    floor_meshes = []

    for floor in floors:
        vertices = floor['vertices']
        x = [v['x'] for v in vertices]
        y = [v['y'] for v in vertices]
        z = [v['z'] for v in vertices]

        # Add first point to close the polygon
        x.append(x[0])
        y.append(y[0])
        z.append(z[0])

        floor_meshes.append(
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                opacity=0.9,
                color='lightblue',
                hoverinfo='text',
                text=f"Floor {floor['id']}"
            )
        )

    return floor_meshes


def create_opening_meshes(openings):
    """Create 3D meshes for openings (doors and windows) using proper triangulation"""
    opening_meshes = []

    for opening in openings:
        vertices = opening['vertices']
        if len(vertices) != 4:
            continue

        # Create vertices array with explicit float dtype
        vertices_array = np.array([
            [float(vertices[0]['x']), float(vertices[0]['y']), float(vertices[0]['z'])],  # bottom-left
            [float(vertices[1]['x']), float(vertices[1]['y']), float(vertices[1]['z'])],  # bottom-right
            [float(vertices[2]['x']), float(vertices[2]['y']), float(vertices[2]['z'])],  # top-right
            [float(vertices[3]['x']), float(vertices[3]['y']), float(vertices[3]['z'])]  # top-left
        ], dtype=np.float64)

        # Calculate normal vector of the opening
        v1 = vertices_array[1] - vertices_array[0]  # bottom edge vector
        v2 = vertices_array[3] - vertices_array[0]  # side edge vector
        normal = np.cross(v1, v2)
        # Normalize the normal vector
        normal_length = np.linalg.norm(normal)
        if normal_length > 0:
            normal = normal / normal_length

        # Offset the opening slightly from the wall (by 0.01 meters)
        offset = 0.01
        vertices_array = vertices_array + (normal * offset)

        # Create both front and back faces
        vertices_with_back = np.vstack([
            vertices_array,  # Front face
            vertices_array - (normal * (2 * offset))  # Back face
        ])

        # Indices for both faces
        i = [0, 0, 4, 4]  # First vertices
        j = [1, 2, 5, 6]  # Second vertices
        k = [2, 3, 6, 7]  # Third vertices

        # Set color and opacity based on opening type
        color = 'red' if opening['type'] == 'door' else 'skyblue'
        opacity = 0.9 if opening['type'] == 'door' else 0.7

        opening_meshes.append(
            go.Mesh3d(
                x=vertices_with_back[:, 0].tolist(),
                y=vertices_with_back[:, 1].tolist(),
                z=vertices_with_back[:, 2].tolist(),
                i=i, j=j, k=k,
                opacity=opacity,
                color=color,
                hoverinfo='text',
                text=f"{opening['type'].capitalize()} {opening['id']}",
                flatshading=True,
                lighting=dict(
                    ambient=0.8,
                    diffuse=0.9,
                    facenormalsepsilon=0,
                    roughness=0.1,
                    specular=0.3
                ),
                showlegend=True,
                name=f"{opening['type'].capitalize()} {opening['id']}"
            )
        )
    return opening_meshes

def create_column_lines(columns):
    """Create 3D cylinders for columns"""
    column_meshes = []

    for col in columns:
        # Get vertices for column
        vertices = col['vertices']
        start = vertices[0]  # First vertex is start
        end = vertices[1]  # Second vertex is end

        # Create cylinder points
        radius = 0.15  # Column radius in meters
        points = 16  # Number of points to create cylinder

        # Create circle points around the column axis
        theta = np.linspace(0, 2 * np.pi, points)

        # Calculate column direction vector
        direction = np.array([end['x'] - start['x'],
                              end['y'] - start['y'],
                              end['z'] - start['z']])
        length = np.linalg.norm(direction)

        # Create points for the cylinder
        x = []
        y = []
        z = []

        # Create circles at start and end
        for t in theta:
            # Create basis vectors perpendicular to column direction
            if abs(direction[2]) < abs(direction[0]):
                u = np.array([direction[2], 0, -direction[0]])
            else:
                u = np.array([-direction[1], direction[0], 0])
            u = u / np.linalg.norm(u)
            v = np.cross(direction, u)
            v = v / np.linalg.norm(v)

            # Create circle points
            circle_point = (u * np.cos(t) + v * np.sin(t)) * radius

            # Add points at start and end of column
            x.extend([start['x'] + circle_point[0], end['x'] + circle_point[0]])
            y.extend([start['y'] + circle_point[1], end['y'] + circle_point[1]])
            z.extend([start['z'] + circle_point[2], end['z'] + circle_point[2]])

        # Create triangles for the cylinder surface
        i = []
        j = []
        k = []

        # Connect the points to form triangles
        for p in range(points - 1):
            # First triangle
            i.extend([2 * p, 2 * p + 2, 2 * p + 1])
            j.extend([2 * p + 2, 2 * p + 3, 2 * p + 1])
            k.extend([2 * p + 1, 2 * p + 3, 2 * p + 3])

            # Second triangle
            i.extend([2 * p, 2 * p + 2, 2 * p])
            j.extend([2 * p + 2, 2 * p + 1, 2 * p + 2])
            k.extend([2 * p + 1, 2 * p + 1, 2 * p + 3])

        # Connect last points to first points
        p = points - 1
        i.extend([2 * p, 0, 2 * p])
        j.extend([0, 2 * p + 1, 0])
        k.extend([2 * p + 1, 2 * p + 1, 1])

        column_meshes.append(
            go.Mesh3d(
                x=x,
                y=y,
                z=z,
                i=i,
                j=j,
                k=k,
                color='darkgray',
                opacity=0.8,
                hoverinfo='text',
                text=f"Column {col['id']}"
            )
        )

    return column_meshes


def create_beam_lines(beams):
    """Create 3D boxes for beams"""
    beam_meshes = []

    for beam in beams:
        # Get vertices for beam
        vertices = beam['vertices']
        start = vertices[0]  # First vertex is start
        end = vertices[1]  # Second vertex is end

        # Beam dimensions
        width = 0.2  # meters
        height = 0.4  # meters

        # Calculate beam direction vector
        direction = np.array([end['x'] - start['x'],
                              end['y'] - start['y'],
                              end['z'] - start['z']])
        length = np.linalg.norm(direction)
        direction = direction / length

        # Create basis vectors for beam cross-section
        if abs(direction[2]) < abs(direction[0]):
            up = np.array([0, 0, 1])
        else:
            up = np.array([1, 0, 0])
        right = np.cross(direction, up)
        right = right / np.linalg.norm(right)
        up = np.cross(right, direction)

        # Create the 8 vertices of the beam
        box_vertices = []
        for dx in [-width / 2, width / 2]:
            for dy in [-height / 2, height / 2]:
                # At start point
                point = np.array([start['x'], start['y'], start['z']])
                point = point + dx * right + dy * up
                box_vertices.append(point)
                # At end point
                point = np.array([end['x'], end['y'], end['z']])
                point = point + dx * right + dy * up
                box_vertices.append(point)

        box_vertices = np.array(box_vertices)

        # Create faces of the beam
        i = [0, 0, 0, 2, 2, 4]  # First vertex of each triangle
        j = [1, 2, 4, 3, 6, 5]  # Second vertex of each triangle
        k = [2, 3, 5, 6, 7, 7]  # Third vertex of each triangle

        beam_meshes.append(
            go.Mesh3d(
                x=box_vertices[:, 0],
                y=box_vertices[:, 1],
                z=box_vertices[:, 2],
                i=i,
                j=j,
                k=k,
                color='brown',
                opacity=0.8,
                hoverinfo='text',
                text=f"Beam {beam['id']}"
            )
        )

    return beam_meshes

def plot_building_geometry(json_file):
    """Plot complete building geometry from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)

    fig = go.Figure()
    components = data['components']

    # Add components in the correct order
    # 1. Floors (bottom)
    if 'floors' in components and components['floors']:
        floor_meshes = create_floor_meshes(components['floors'])
        for mesh in floor_meshes:
            fig.add_trace(mesh)

    # 2. Walls
    if 'walls' in components and components['walls']:
        wall_meshes = create_wall_meshes(components['walls'])
        for mesh in wall_meshes:
            fig.add_trace(mesh)

    # 3. Columns
    if 'columns' in components and components['columns']:
        column_lines = create_column_lines(components['columns'])
        for line in column_lines:
            fig.add_trace(line)

    # 4. Beams
    if 'beams' in components and components['beams']:
        beam_lines = create_beam_lines(components['beams'])
        for line in beam_lines:
            fig.add_trace(line)

    # 5. Openings (on top)
    if 'openings' in components and components['openings']:
        opening_meshes = create_opening_meshes(components['openings'])
        for mesh in opening_meshes:
            fig.add_trace(mesh)

    # Update layout
    fig.update_layout(
        scene=dict(
            aspectmode='data',
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            xaxis_title='X (meters)',
            yaxis_title='Y (meters)',
            zaxis_title='Z (meters)'
        ),
        title=f"Building Geometry Visualization - {data['buildingId']}",
        showlegend=True,
        legend=dict(
            x=0.8,
            y=0.9,
            itemsizing='constant'  # Makes legend items same size
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )

    return fig

def main():
    # Get JSON file path from user
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    json_file = filedialog.askopenfilename(
        title="Select Building Geometry JSON file",
        filetypes=[("JSON files", "*.json")]
    )

    if not json_file:
        print("No file selected. Exiting...")
        return

    # Create visualization
    fig = plot_building_geometry(json_file)

    # Show the plot
    fig.show()

if __name__ == "__main__":
    main()