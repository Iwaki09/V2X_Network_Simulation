#!/usr/bin/env python3
"""
Vehicle positioning debug script
"""
import numpy as np

# Vehicle configurations
vehicles_config = [
    {"id": "vehicle_1", "pos": [60, 90], "vel": [6, 0]},     # bs_1に近い位置で東進
    {"id": "vehicle_2", "pos": [180, 160], "vel": [-4, 0]},  # bs_2に近い位置で西進
    {"id": "vehicle_3", "pos": [110, 60], "vel": [0, 5]},    # bs_1とbs_2の間で北進
    {"id": "vehicle_4", "pos": [190, 200], "vel": [0, -4]},  # bs_2に近い位置で南進
]

# Base stations
base_stations = [
    {"id": "bs_1", "pos": [80, 80]},
    {"id": "bs_2", "pos": [220, 180]}
]

# Building
building = {"pos": [150, 120], "size": [50, 30]}

print("=== Vehicle Distance Analysis ===")
print()

for step in [0, 10, 19]:  # Check initial, middle, and final positions
    print(f"Time Step {step}:")
    
    for v_config in vehicles_config:
        # Calculate vehicle position at this step
        time = step * 1.0  # 1 second per step
        x = v_config["pos"][0] + v_config["vel"][0] * time
        y = v_config["pos"][1] + v_config["vel"][1] * time
        
        # Keep within bounds [10, 290] x [10, 290]
        x = max(10, min(290, x))
        y = max(10, min(290, y))
        
        print(f"  {v_config['id']}: [{x:.1f}, {y:.1f}]")
        
        # Calculate distance to each base station
        for bs in base_stations:
            dist = np.sqrt((x - bs["pos"][0])**2 + (y - bs["pos"][1])**2)
            print(f"    Distance to {bs['id']}: {dist:.1f}m")
        
        # Check building occlusion
        building_min_x = building["pos"][0] - building["size"][0]/2
        building_max_x = building["pos"][0] + building["size"][0]/2
        building_min_y = building["pos"][1] - building["size"][1]/2
        building_max_y = building["pos"][1] + building["size"][1]/2
        
        if (building_min_x <= x <= building_max_x and 
            building_min_y <= y <= building_max_y):
            print(f"    ⚠️  Vehicle overlaps with building!")
        
        print()
    
    print("-" * 50)
    print()