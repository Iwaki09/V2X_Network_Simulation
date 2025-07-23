# Prototype 2: Static V2X Network Optimization with Ray-Tracing

## 1. Goal

This prototype aims to build a simulation framework to optimize a **static snapshot** of a V2X network. Unlike `prototype1`, this version incorporates a high-fidelity physical propagation model using **ray-tracing**. The key feature is to treat **vehicles themselves as 3D objects** that can obstruct or reflect radio signals, in addition to static buildings.

The primary objective is to determine the optimal assignment of vehicles to base stations based on link quality data derived from a realistic, static 3D scene.

## 2. Core Concepts

- **Static Simulation**: The simulation does not involve a time dimension. All entities (vehicles, buildings) are stationary.
- **3D Scene Definition**: The environment, including buildings, vehicles, and base stations, is defined as a 3D scene.
- **Ray-Tracing for Link Quality**: The link quality (e.g., path loss) between every vehicle and base station is calculated using a ray-tracing engine. This approach accounts for complex phenomena like reflection, diffraction, and blockage by both buildings and other vehicles.
- **Centralized Optimization**: A central optimizer uses the high-fidelity link quality data to find the globally optimal network configuration (assignments) that maximizes a certain objective (e.g., total throughput).

## 3. Technical Approach & Implementation Plan

### Phase 1: Scene Definition

- **Objective**: Create a programmatic way to define the 3D simulation environment.
- **Tasks**:
    1.  Define a simple JSON format (`scene.json`) to describe the properties (ID, position, size, material) of all objects (buildings, vehicles, base stations).
    2.  Implement a Python parser (`scene_parser.py`) to load this JSON file into memory as Python objects.

### Phase 2: Ray-Tracing Execution

- **Objective**: Convert the defined scene into a format usable by a ray-tracing engine and execute the simulation.
- **Key Technology**: **SIONNA RT** (which uses **Mitsuba 3** internally) is the chosen engine because of its ability to handle complex 3D scenes described in XML.
- **Tasks**:
    1.  Implement a converter (`mitsuba_converter.py`) that translates the Python scene objects into a Mitsuba 3 XML scene file.
    2.  Create a wrapper (`run_raytracing.py`) to invoke SIONNA RT with the generated scene, execute the ray-tracing, and process the results to get path loss values for all links.

### Phase 3: Network Optimization

- **Objective**: Use the ray-tracing results to perform network optimization.
- **Tasks**:
    1.  Adapt the optimizer from `prototype1` (`optimizer.py`). It will take the high-fidelity link quality data as input and determine the best vehicle-to-base station assignments.

### Phase 4: Visualization

- **Objective**: Visualize the scene and the optimization results.
- **Tasks**:
    1.  Implement a visualizer (`visualizer.py`) using `matplotlib` to display a top-down (2D) view of the scene.
    2.  The visualization will show the layout of buildings, vehicles, and base stations, as well as the final optimized connection links.
