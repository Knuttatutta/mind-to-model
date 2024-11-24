import json

def split_building_json(building_json_path):
    # Read the building JSON file
    with open(building_json_path, 'r') as file:
        building_data = json.load(file)

    # Extract walls and floors data
    walls_data = building_data.get("components", {}).get("walls", [])
    floors_data = building_data.get("components", {}).get("floors", [])

    # Convert lists to dictionaries with ids as keys
    walls_dict = {wall["id"]: wall for wall in walls_data}
    floors_dict = {floor["id"]: floor for floor in floors_data}

    # Save walls data to walls.json
    with open("walls.json", 'w') as walls_file:
        json.dump(walls_dict, walls_file, indent=4)

    # Save floors data to floors.json
    with open("floors.json", 'w') as floors_file:
        json.dump(floors_dict, floors_file, indent=4)

if __name__ == "__main__":
    # Split building.json into walls.json and floors.json
    split_building_json("building.json")

    print("Walls data has been saved to walls.json")
    print("Floors data has been saved to floors.json")