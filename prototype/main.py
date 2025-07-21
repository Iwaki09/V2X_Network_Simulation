import numpy as np
import time
from src.entities import Vehicle, BaseStation
from src.simulation import Simulation
from src.optimizer import Optimizer
from src.visualizer import Visualizer

def main():
    """
    Main function to run the V2X network simulation prototype.
    """
    # --- Simulation Setup ---
    print("Initializing simulation...")

    # Create Base Stations
    base_stations = [
        BaseStation(bs_id=0, position=np.array([500, 500]), max_capacity=2),
        BaseStation(bs_id=1, position=np.array([1500, 500]), max_capacity=2)
    ]

    # Create Vehicles
    vehicles = [
        Vehicle(vehicle_id=0, position=np.array([100, 450]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=1, position=np.array([200, 550]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=2, position=np.array([800, 480]), velocity=np.array([80, 0])),
        Vehicle(vehicle_id=3, position=np.array([1800, 520]), velocity=np.array([-80, 0])) # Moving towards the other BS
    ]

    # Create Simulation Environment, Optimizer, and Visualizer
    sim = Simulation(vehicles, base_stations)
    optimizer = Optimizer()
    visualizer = Visualizer()

    # --- Run Simulation ---
    time_steps = 20
    delta_time = 1.0 # seconds

    print(f"Running simulation for {time_steps} steps with visualization.")

    try:
        for step in range(time_steps):
            sim.step(delta_time)
            state = sim.get_state()

            # Decide assignments using the optimizer
            assignments = optimizer.decide_assignments(
                state['vehicles'], state['base_stations'], state['datarate_matrix']
            )

            # Update the visualization
            visualizer.update_plot(
                state['time'], state['vehicles'], state['base_stations'], assignments
            )

            print(f"--- Time Step {step+1} (Time: {state['time']:.1f}s) ---")
            print("Assignments (Vehicle ID -> BS ID):", assignments)
            
            # A short pause to make the visualization smoother
            time.sleep(0.5)

    except Exception as e:
        print(f"An error occurred during simulation: {e}")
    finally:
        print("\nSimulation finished. Closing plot.")
        visualizer.close()


if __name__ == "__main__":
    main()
