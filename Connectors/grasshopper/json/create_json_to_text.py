import json

def create_json_file_with_points(json_file_path):
    # Points that are part of a cube
    points = [
        {"x": 0, "y": 0, "z": 0},
        {"x": 1, "y": 0, "z": 0},
        {"x": 1, "y": 1, "z": 0},
        {"x": 0, "y": 1, "z": 0},
    ]

    # Convert points data to JSON and save to file
    with open(json_file_path, 'w') as json_file:
        json.dump(points, json_file, indent=4)

def convert_json_to_text(json_file_path, text_file_path):
    # Read JSON from file
    with open(json_file_path, 'r') as json_file:
        points = json.load(json_file)

    # Create text content
    text_content = []
    for point in points:
        text_content.append(f"({point['x']}, {point['y']}, {point['z']})")

    # Save text content to file
    with open(text_file_path, 'w') as text_file:
        text_file.write("\n".join(text_content))

if __name__ == "__main__":
    # Create JSON file with points
    create_json_file_with_points("points.json")

    # Convert JSON file to text file
    convert_json_to_text("points.json", "points.txt")

    print("Points data has been saved to points.json and points.txt")