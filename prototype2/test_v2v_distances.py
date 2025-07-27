#!/usr/bin/env python3
"""
Test V2V distances and path loss calculations
"""
import numpy as np

# Vehicle initial positions 
vehicles_pos = [
    [60, 90],   # vehicle_1
    [180, 160], # vehicle_2  
    [110, 60],  # vehicle_3
    [190, 200]  # vehicle_4
]

print("=== V2V Distance and Path Loss Analysis ===")
print()

for step in [0, 10, 19]:
    print(f"Time Step {step}:")
    
    # Calculate positions at this step
    positions = []
    for i, pos in enumerate(vehicles_pos):
        if i == 0:  # vehicle_1: vel = [6, 0]
            x = pos[0] + 6 * step
            y = pos[1]
        elif i == 1:  # vehicle_2: vel = [-4, 0]
            x = pos[0] - 4 * step
            y = pos[1]
        elif i == 2:  # vehicle_3: vel = [0, 5]
            x = pos[0]
            y = pos[1] + 5 * step
        elif i == 3:  # vehicle_4: vel = [0, -4]
            x = pos[0]
            y = pos[1] - 4 * step
        
        # Keep within bounds
        x = max(10, min(290, x))
        y = max(10, min(290, y))
        positions.append([x, y])
    
    print(f"  Vehicle positions: {positions}")
    
    # Calculate V2V distances and path loss
    for i in range(4):
        for j in range(4):
            if i != j:
                distance = np.sqrt(
                    (positions[i][0] - positions[j][0])**2 + 
                    (positions[i][1] - positions[j][1])**2
                )
                
                # V2V path loss calculation
                if distance > 1:
                    path_loss_db = 38.77 + 16.7 * np.log10(distance) + 18.2 * np.log10(5.9)
                else:
                    path_loss_db = 40.0
                
                print(f"  vehicle_{i+1} -> vehicle_{j+1}: {distance:.1f}m -> {path_loss_db:.1f}dB")
    
    print()