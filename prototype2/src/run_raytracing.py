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

    # Load the Mitsuba scene
    rt_scene = sn.rt.Scene(xml_file=mitsuba_xml_path)

    # Configure transmitters (Base Stations)
    for bs in scene.base_stations:
        rt_scene.add(sn.rt.Transmitter(name=f"tx_{bs['id']}", position=bs['position']))

    # Configure receivers (Vehicles)
    for v in scene.vehicles:
        rt_scene.add(sn.rt.Receiver(name=f"rx_{v['id']}", position=v['position']))

    # Compute paths
    print("Computing radio wave paths...")
    paths = rt_scene.compute_paths(max_depth=5, num_samples=1e6)

    # Extract path loss
    num_bs = len(scene.base_stations)
    num_vehicles = len(scene.vehicles)
    path_loss_matrix = np.zeros((num_bs, num_vehicles))

    print("Calculating path loss from computed paths...")
    for i, bs in enumerate(scene.base_stations):
        for j, v in enumerate(scene.vehicles):
            # The `cir` method provides channel impulse responses
            # We can get path loss from the sum of squared magnitudes of the taps
            a, _ = paths.cir(tx=f"tx_{bs['id']}", rx=f"rx_{v['id']}")
            # Path gain is the sum of squared magnitudes of the path coefficients
            path_gain = tf.reduce_sum(tf.square(tf.abs(a)), axis=-1).numpy()[0]
            # Path loss in dB
            path_loss_db = -10 * np.log10(path_gain) if path_gain > 0 else np.inf
            path_loss_matrix[i, j] = path_loss_db

    print("Ray-tracing complete.")
    return path_loss_matrix

# Note: This script is not meant to be run directly as it requires a specific environment.
# It will be called from a main execution script.
