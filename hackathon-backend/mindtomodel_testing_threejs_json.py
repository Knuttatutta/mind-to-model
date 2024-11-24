import numpy as np
import json


def generate_building_data():
    # Building dimensions
    width = 4
    depth = 3
    height = 5
    level_height = 1

    # Main building vertices
    vertices = np.array([
        # Base points
        [0, 0, 0],
        [width, 0, 0],
        [width, depth, 0],
        [0, depth, 0],
        # Top points
        [0, 0, height],
        [width, 0, height],
        [width, depth, height],
        [0, depth, height],
    ]).tolist()

    # Define faces (indices for triangles)
    faces = [
        # Bottom
        [0, 1, 2],
        [0, 2, 3],
        # Top
        [4, 6, 5],
        [4, 7, 6],
        # Front
        [0, 5, 1],
        [0, 4, 5],
        # Right
        [1, 5, 6],
        [1, 6, 2],
        # Back
        [2, 6, 7],
        [2, 7, 3],
        # Left
        [3, 7, 4],
        [3, 4, 0]
    ]

    # Generate balcony data
    balconies = []
    for floor in range(1, height):
        balcony_depth = 0.5
        balcony_verts = [
            [0, -balcony_depth, floor],
            [width, -balcony_depth, floor],
            [width, 0, floor],
            [0, 0, floor]
        ]
        base_idx = len(vertices)
        vertices.extend(balcony_verts)
        balconies.extend([
            [base_idx, base_idx + 1, base_idx + 2],
            [base_idx, base_idx + 2, base_idx + 3]
        ])

    # Generate rooftop structure
    roof_inset = 0.5
    roof_height = 0.8
    roof_vertices = [
        [roof_inset, roof_inset, height],
        [width - roof_inset, roof_inset, height],
        [width - roof_inset, depth - roof_inset, height],
        [roof_inset, depth - roof_inset, height],
        [roof_inset, roof_inset, height + roof_height],
        [width - roof_inset, roof_inset, height + roof_height],
        [width - roof_inset, depth - roof_inset, height + roof_height],
        [roof_inset, depth - roof_inset, height + roof_height],
    ]

    base_idx = len(vertices)
    vertices.extend(roof_vertices)

    roof_faces = [
        # Bottom
        [base_idx, base_idx + 1, base_idx + 2],
        [base_idx, base_idx + 2, base_idx + 3],
        # Top
        [base_idx + 4, base_idx + 6, base_idx + 5],
        [base_idx + 4, base_idx + 7, base_idx + 6],
        # Front
        [base_idx, base_idx + 5, base_idx + 1],
        [base_idx, base_idx + 4, base_idx + 5],
        # Right
        [base_idx + 1, base_idx + 5, base_idx + 6],
        [base_idx + 1, base_idx + 6, base_idx + 2],
        # Back
        [base_idx + 2, base_idx + 6, base_idx + 7],
        [base_idx + 2, base_idx + 7, base_idx + 3],
        # Left
        [base_idx + 3, base_idx + 7, base_idx + 4],
        [base_idx + 3, base_idx + 4, base_idx + 0],
    ]

    # Combine all faces
    faces.extend(balconies)
    faces.extend(roof_faces)

    return {
        "vertices": vertices,
        "faces": faces,
        "dimensions": {
            "width": width,
            "depth": depth,
            "height": height
        }
    }


# Generate and save the data
building_data = generate_building_data()
with open('building_data.json', 'w') as f:
    json.dump(building_data, f)

print("Building data generated and saved to building_data.json")