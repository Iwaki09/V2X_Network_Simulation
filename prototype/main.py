import numpy as np
import json
from src.entities import Vehicle, BaseStation
from src.simulation import Simulation
from src.optimizer import Optimizer

def main():
    """
    Main function to run the V2X network simulation and export the log to a JSON file.
    """
    # --- Simulation Setup ---
    print("Initializing simulation for data export...")

    base_stations = [
        BaseStation(bs_id=0, position=np.array([500, 500]), max_capacity=2),
        BaseStation(bs_id=1, position=np.array([1500, 500]), max_capacity=2)
    ]

    vehicles = [
        Vehicle(vehicle_id=0, position=np.array([100, 450]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=1, position=np.array([200, 550]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=2, position=np.array([800, 480]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=3, position=np.array([1800, 520]), velocity=np.array([-80, 0]))
    ]

    sim = Simulation(vehicles, base_stations)
    optimizer = Optimizer()

    # --- Run Simulation and Collect Logs ---
    simulation_log = []
    time_steps = 50 # Increase steps for a longer animation
    delta_time = 0.5

    print(f"Running simulation for {time_steps} steps to generate log...")

    # Add initial state
    initial_state = sim.get_state()
    initial_assignments = optimizer.decide_assignments(
        initial_state['vehicles'], initial_state['base_stations'], initial_state['datarate_matrix']
    )
    simulation_log.append({
        "time": initial_state['time'],
        "vehicles": [{ "id": v.id, "position": v.position.tolist() } for v in initial_state['vehicles']],
        "base_stations": [{ "id": bs.id, "position": bs.position.tolist() } for bs in initial_state['base_stations']],
        "assignments": initial_assignments
    })

    for step in range(time_steps):
        sim.step(delta_time)
        state = sim.get_state()
        assignments = optimizer.decide_assignments(
            state['vehicles'], state['base_stations'], state['datarate_matrix']
        )
        
        # Convert numpy arrays to lists for JSON serialization
        log_entry = {
            "time": state['time'],
            "vehicles": [{ "id": v.id, "position": v.position.tolist() } for v in state['vehicles']],
            "base_stations": [{ "id": bs.id, "position": bs.position.tolist() } for bs in state['base_stations']],
            "assignments": assignments
        }
        simulation_log.append(log_entry)

    # --- Export to JSON ---
    output_path = "prototype/simulation_log.json"
    print(f"Simulation finished. Exporting log to {output_path}...")

    with open(output_path, 'w') as f:
        json.dump(simulation_log, f, indent=2)

    print("Export complete.")

if __name__ == "__main__":
    main()
