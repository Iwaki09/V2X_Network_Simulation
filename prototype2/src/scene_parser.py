import json
from typing import Dict, List, Any
import os # Import the os module

class Scene:
    """
    A data class to hold all the elements of a simulation scene.
    """
    def __init__(self, scene_data: Dict[str, Any]):
        self.world_size: List[float] = scene_data.get('world_size', [200, 200])
        self.materials: Dict[str, Any] = scene_data.get('materials', {})
        self.buildings: List[Dict[str, Any]] = scene_data.get('buildings', [])
        self.vehicles: List[Dict[str, Any]] = scene_data.get('vehicles', [])
        self.base_stations: List[Dict[str, Any]] = scene_data.get('base_stations', [])

    def __repr__(self):
        return (
            f"Scene(world_size={self.world_size}, "
            f"{len(self.buildings)} buildings, "
            f"{len(self.vehicles)} vehicles, "
            f"{len(self.base_stations)} base stations)"
        )

def load_scene(file_path: str) -> Scene:
    """
    Loads a scene configuration from a JSON file.

    Args:
        file_path: The path to the scene.json file.

    Returns:
        A Scene object containing the parsed data.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    return Scene(data)

# Example usage:
if __name__ == '__main__':
    # This allows testing the parser independently
    # Construct an absolute path to scene.json relative to this script file
    script_dir = os.path.dirname(__file__)
    scene_file = os.path.join(script_dir, '../scene.json')
    scene = load_scene(scene_file)
    print("Scene loaded successfully!")
    print(scene)
    print("\nFirst building:", scene.buildings[0])
    print("First vehicle:", scene.vehicles[0])
    print("First base station:", scene.base_stations[0])
