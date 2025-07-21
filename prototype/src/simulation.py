from typing import List
import numpy as np
from .entities import Vehicle, BaseStation
from .channel import calculate_datarate

class Simulation:
    """
    Manages the state of the simulation, including all entities and their interactions.
    """
    def __init__(self, vehicles: List[Vehicle], base_stations: List[BaseStation]):
        """
        Initializes the simulation environment.

        Args:
            vehicles: A list of Vehicle objects.
            base_stations: A list of BaseStation objects.
        """
        self.vehicles = vehicles
        self.base_stations = base_stations
        self.time = 0.0
        self.datarate_matrix = np.zeros((len(vehicles), len(base_stations)))

    def step(self, delta_time: float):
        """
        Advances the simulation by one time step.

        Args:
            delta_time: The duration of the time step.
        """
        # 1. Update vehicle positions
        for vehicle in self.vehicles:
            vehicle.update_position(delta_time)

        # 2. Update the data rate matrix
        self.update_datarate_matrix()

        # 3. Increment simulation time
        self.time += delta_time

    def update_datarate_matrix(self):
        """
        Recalculates the data rate for every vehicle-base station pair.
        """
        for i, vehicle in enumerate(self.vehicles):
            for j, bs in enumerate(self.base_stations):
                self.datarate_matrix[i, j] = calculate_datarate(vehicle, bs)

    def get_state(self):
        """
        Returns the current state of the simulation.

        Returns:
            A dictionary containing the current time, entities, and data rate matrix.
        """
        return {
            "time": self.time,
            "vehicles": self.vehicles,
            "base_stations": self.base_stations,
            "datarate_matrix": self.datarate_matrix
        }
