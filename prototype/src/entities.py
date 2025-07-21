import numpy as np

class Vehicle:
    """
    Represents a single vehicle in the simulation.
    """
    def __init__(self, vehicle_id: int, position: np.ndarray, velocity: np.ndarray):
        """
        Initializes a Vehicle object.

        Args:
            vehicle_id: Unique identifier for the vehicle.
            position: 2D numpy array representing the vehicle's [x, y] position.
            velocity: 2D numpy array representing the vehicle's [vx, vy] velocity.
        """
        self.id = vehicle_id
        self.position = position
        self.velocity = velocity

    def update_position(self, delta_time: float):
        """
        Updates the vehicle's position based on its velocity.

        Args:
            delta_time: The time step for the update.
        """
        self.position = self.position + self.velocity * delta_time

    def __repr__(self):
        return f"Vehicle(id={self.id}, pos={self.position})"

class BaseStation:
    """
    Represents a single base station in the simulation.
    """
    def __init__(self, bs_id: int, position: np.ndarray, max_capacity: int = 10):
        """
        Initializes a BaseStation object.

        Args:
            bs_id: Unique identifier for the base station.
            position: 2D numpy array representing the base station's [x, y] position.
            max_capacity: The maximum number of vehicles that can connect to this base station.
        """
        self.id = bs_id
        self.position = position
        self.max_capacity = max_capacity

    def __repr__(self):
        return f"BaseStation(id={self.id}, pos={self.position}, cap={self.max_capacity})"
