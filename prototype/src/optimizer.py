from typing import List, Dict
import numpy as np
from .entities import Vehicle, BaseStation

class Optimizer:
    """
    A centralized optimizer that decides the vehicle-to-base station assignments.
    """
    def decide_assignments(self, vehicles: List[Vehicle], base_stations: List[BaseStation], datarate_matrix: np.ndarray) -> Dict[int, int]:
        """
        Assigns each vehicle to a base station to maximize total network throughput.

        This method uses a greedy approach:
        1. Find the best possible connection (highest data rate) for each vehicle.
        2. Iterate through all possible connections in descending order of data rate.
        3. Assign a vehicle to a base station if the base station still has capacity.

        Args:
            vehicles: A list of Vehicle objects.
            base_stations: A list of BaseStation objects.
            datarate_matrix: A 2D numpy array where matrix[i, j] is the data rate
                             between vehicle i and base station j.

        Returns:
            A dictionary mapping vehicle_id to assigned base_station_id.
        """
        num_vehicles = len(vehicles)
        num_base_stations = len(base_stations)

        # Create a list of all possible connections (vehicle_idx, bs_idx, datarate)
        possible_connections = []
        for i in range(num_vehicles):
            for j in range(num_base_stations):
                possible_connections.append((i, j, datarate_matrix[i, j]))

        # Sort connections by data rate in descending order
        possible_connections.sort(key=lambda x: x[2], reverse=True)

        assignments = {}
        bs_load = {bs.id: 0 for bs in base_stations}
        bs_capacity = {bs.id: bs.max_capacity for bs in base_stations}

        for vehicle_idx, bs_idx, _ in possible_connections:
            vehicle_id = vehicles[vehicle_idx].id
            bs_id = base_stations[bs_idx].id

            # If vehicle is not yet assigned and the BS has capacity
            if vehicle_id not in assignments and bs_load[bs_id] < bs_capacity[bs_id]:
                assignments[vehicle_id] = bs_id
                bs_load[bs_id] += 1

        return assignments
