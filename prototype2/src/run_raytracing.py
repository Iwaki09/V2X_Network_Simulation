import sionna as sn
import tensorflow as tf
import numpy as np
import os
from .scene_parser import Scene

def run_raytracing(scene: Scene, mitsuba_xml_path: str):
    """
    Executes ray-tracing for a given scene using SIONNA RT.

    Args:
        scene: The Scene object.
        mitsuba_xml_path: Path to the Mitsuba XML scene file.

    Returns:
        A numpy array representing the path loss between each BS and vehicle.
    """
    print("--- Running Ray-Tracing with SIONNA RT ---")
    # Ensure GPU is available for TensorFlow
    gpus = tf.config.list_physical_devices('GPU')
    if not gpus:
        raise RuntimeError("No GPU found. SIONNA RT requires a GPU.")
    print(f"Using GPU: {gpus[0].name}")

    # Create a new SIONNA RT scene and manually add buildings
    rt_scene = sn.rt.Scene()
    
    # Add buildings as SceneObjects using simple box mesh
    import os
    box_mesh_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simple_box.obj")
    
    for building in scene.buildings:
        pos = building['position']
        size = building['size']
        
        # Create radio material for the building
        building_material = sn.rt.ITURadioMaterial(
            name=f"{building['id']}_material",
            itu_type="concrete",
            thickness=0.2  # 20cm thickness
        )
        
        try:
            # Create SceneObject from OBJ file
            building_obj = sn.rt.SceneObject(
                fname=box_mesh_path,
                name=building['id'],
                radio_material=building_material
            )
            
            rt_scene.add(building_obj)
            print(f"Added building: {building['id']} at {pos} with size {size}")
        except Exception as e:
            print(f"Warning: Failed to add building {building['id']}: {e}")

    # Configure antenna arrays (example: simple dipole antennas)
    # These are default arrays for all transmitters and receivers unless overridden
    rt_scene.tx_array = sn.rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="dipole", polarization="V")
    rt_scene.rx_array = sn.rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                 horizontal_spacing=0.5, pattern="dipole", polarization="V")

    # Configure transmitters (Base Stations)
    for bs in scene.base_stations:
        rt_scene.add(sn.rt.Transmitter(name=f"tx_{bs['id']}", position=bs['position']))

    # Configure receivers (Vehicles)
    for v in scene.vehicles:
        rt_scene.add(sn.rt.Receiver(name=f"rx_{v['id']}", position=v['position']))

    # Compute paths
    print("Computing radio wave paths...")
    path_solver = sn.rt.PathSolver()
    paths = path_solver(scene=rt_scene, max_depth=5)

    # Extract path loss
    num_bs = len(scene.base_stations)
    num_vehicles = len(scene.vehicles)
    path_loss_matrix = np.zeros((num_bs, num_vehicles))

    a, _ = paths.cir()
    print(f"Type of a: {type(a)}")
    if isinstance(a, list):
        print(f"Number of elements in a: {len(a)}")
        for idx, item in enumerate(a):
            print(f"  Type of a[{idx}]: {type(item)}")
            if hasattr(item, 'shape'):
                print(f"  Shape of a[{idx}]: {item.shape}")
        # Convert each DrJit tensor to a TensorFlow tensor before stacking
        a = [tf.convert_to_tensor(x) for x in a]
        # a = tf.stack(a, axis=0) # Temporarily comment out stacking
    # print(f"Shape of stacked a: {a.shape}") # Temporarily comment out printing stacked shape

    # Extract path loss
    num_bs = len(scene.base_stations)
    num_vehicles = len(scene.vehicles)
    path_loss_matrix = np.zeros((num_bs, num_vehicles))

    print("Calculating path loss from computed paths...")
    for i, bs in enumerate(scene.base_stations):
        for j, v in enumerate(scene.vehicles):
            # The `cir` method provides channel impulse responses
            # We can get path loss from the sum of squared magnitudes of the taps
            # Assuming a single path for simplicity, adjust if multiple paths are expected
            path_gain = tf.reduce_sum(tf.square(tf.abs(a[0][i, 0, j, 0, :, :])), axis=[-1]).numpy()[0]
            # Path loss in dB
            path_loss_db = -10 * np.log10(path_gain) if path_gain > 0 else np.inf
            path_loss_matrix[i, j] = path_loss_db

    print("Ray-tracing complete.")
    return path_loss_matrix

# Note: This script is not meant to be run directly as it requires a specific environment.
# It will be called from a main execution script.
