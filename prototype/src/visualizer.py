import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict
from .entities import Vehicle, BaseStation

class Visualizer:
    """
    Handles the visualization of the simulation state.
    """
    def __init__(self, terrain_size=(2000, 1000)):
        """
        Initializes the visualizer.
        Args:
            terrain_size: A tuple (width, height) for the simulation area.
        """
        self.terrain_size = terrain_size
        plt.ion() # Turn on interactive mode
        self.fig, self.ax = plt.subplots(figsize=(12, 6))

    def update_plot(self, time: float, vehicles: List[Vehicle], base_stations: List[BaseStation], assignments: Dict[int, int]):
        """
        Updates and redraws the plot for the current simulation state.

        Args:
            time: The current simulation time.
            vehicles: List of Vehicle objects.
            base_stations: List of BaseStation objects.
            assignments: A dictionary mapping vehicle_id to assigned base_station_id.
        """
        self.ax.clear()

        # Plot Base Stations
        bs_positions = np.array([bs.position for bs in base_stations])
        self.ax.scatter(bs_positions[:, 0], bs_positions[:, 1], c='red', marker='s', s=100, label='Base Stations')
        for bs in base_stations:
            self.ax.text(bs.position[0], bs.position[1] + 20, f'BS {bs.id}')

        # Plot Vehicles
        vehicle_positions = np.array([v.position for v in vehicles])
        self.ax.scatter(vehicle_positions[:, 0], vehicle_positions[:, 1], c='blue', marker='o', s=50, label='Vehicles')
        for v in vehicles:
            self.ax.text(v.position[0], v.position[1] + 20, f'V {v.id}')

        # Plot Assignments
        for vehicle_id, bs_id in assignments.items():
            vehicle_pos = next((v.position for v in vehicles if v.id == vehicle_id), None)
            bs_pos = next((bs.position for bs in base_stations if bs.id == bs_id), None)
            if vehicle_pos is not None and bs_pos is not None:
                self.ax.plot([vehicle_pos[0], bs_pos[0]], [vehicle_pos[1], bs_pos[1]], 'g--', alpha=0.5)

        # Set plot limits and labels
        self.ax.set_xlim(0, self.terrain_size[0])
        self.ax.set_ylim(0, self.terrain_size[1])
        self.ax.set_title(f'V2X Network Simulation - Time: {time:.1f}s')
        self.ax.set_xlabel('X Position (m)')
        self.ax.set_ylabel('Y Position (m)')
        self.ax.legend()
        self.ax.grid(True)

        plt.draw()
        plt.pause(0.1) # Pause to allow the plot to update

    def close(self):
        """
        Closes the plot window.
        """
        plt.ioff()
        plt.show()
