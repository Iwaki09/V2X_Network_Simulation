import numpy as np
from .entities import Vehicle, BaseStation

def calculate_datarate(vehicle: Vehicle, base_station: BaseStation, p0: float = -30, alpha: float = 2.0) -> float:
    """
    Calculates the estimated data rate between a vehicle and a base station.

    This function uses a simple log-distance path loss model.
    Data Rate is modeled as being inversely proportional to the distance squared.

    Args:
        vehicle: The Vehicle object.
        base_station: The BaseStation object.
        p0: The received power at a reference distance of 1 meter (in dBm).
        alpha: The path loss exponent.

    Returns:
        The estimated data rate in Mbps. Returns 0 if distance is extremely small to avoid infinity.
    """
    distance = np.linalg.norm(vehicle.position - base_station.position)

    if distance < 1e-6:
        return np.inf # Or a very large number to signify very high datarate

    # Path Loss in dB
    path_loss_db = -10 * alpha * np.log10(distance)

    # Received Power in dBm
    received_power_dbm = p0 + path_loss_db

    # A simple linear mapping from received power (dBm) to data rate (Mbps)
    # This is a major simplification. In reality, this is a complex function (e.g., Shannon-Hartley theorem).
    # For this prototype, let's assume a simple linear relationship:
    # e.g., -50 dBm -> 100 Mbps, -90 dBm -> 1 Mbps
    # We can model this as: datarate = k * (received_power_dbm - noise_floor)
    noise_floor_dbm = -95
    if received_power_dbm < noise_floor_dbm:
        return 0.0
    
    # Simple linear scaling for the prototype
    datarate = max(0, (received_power_dbm - noise_floor_dbm) * 2) # Scale factor of 2 is arbitrary

    return datarate
