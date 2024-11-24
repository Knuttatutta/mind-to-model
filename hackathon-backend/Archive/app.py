# # # Rendering a Cube approach 1
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# # Define the cube's vertices and faces
# vertices = [
#     [0, 0, 0],
#     [1, 0, 0],
#     [1, 1, 0],
#     [0, 1, 0],
#     [0, 0, 1],
#     [1, 0, 1],
#     [1, 1, 1],
#     [0, 1, 1]
# ]

# faces = [
#     [0, 1, 2, 3],  # Bottom
#     [4, 5, 6, 7],  # Top
#     [0, 1, 5, 4],  # Front
#     [1, 2, 6, 5],  # Right
#     [2, 3, 7, 6],  # Back
#     [3, 0, 4, 7]   # Left
# ]

# # Create a 3D plot
# fig = plt.figure()
# ax = fig.add_subplot(111, projection='3d')

# # Plot each face
# for face in faces:
#     square = [vertices[i] for i in face]
#     ax.add_collection3d(Poly3DCollection([square], alpha=0.5, edgecolor='r'))

# # Set the plot limits
# ax.set_xlim([0, 1])
# ax.set_ylim([0, 1])
# ax.set_zlim([0, 1])

# # Labels and show
# ax.set_xlabel('X')
# ax.set_ylabel('Y')
# ax.set_zlabel('Z')
# plt.show()


# # # Rendering a Cube approach 2
import pyvista as pv

# Vertices and faces for a PyVista mesh
vertices = [
    [0, 0, 0],
    [1, 0, 0],
    [1, 1, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 0, 1],
    [1, 1, 1],
    [0, 1, 1]
]

faces = [
    [4, 0, 1, 2, 3],  # Bottom
    [4, 4, 5, 6, 7],  # Top
    [4, 0, 1, 5, 4],  # Front
    [4, 1, 2, 6, 5],  # Right
    [4, 2, 3, 7, 6],  # Back
    [4, 3, 0, 4, 7]   # Left
]

# Convert to PyVista mesh format
faces = [item for sublist in faces for item in sublist]  # Flatten list
cube = pv.PolyData(vertices, faces)

# Plot the cube
plotter = pv.Plotter()
plotter.add_mesh(cube, color="cyan", show_edges=True)
plotter.show()
