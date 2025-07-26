# Migration and Context Backup for Prototype 2

This file summarizes the context of our discussion regarding the development of `prototype2`.

## 1. Project Goal

The objective of `prototype2` is to create a simulation framework for optimizing a **static snapshot** of a V2X network. The key requirement is to incorporate a high-fidelity physical model by using **ray-tracing**. 

A critical feature is to treat **vehicles themselves as 3D objects** that obstruct and reflect radio signals, moving beyond the simplified models of `prototype1`.

## 2. Core Technical Decision

- **Problem**: How to implement ray-tracing that recognizes vehicles as 3D objects.
- **Chosen Solution**: Utilize **SIONNA RT**, which leverages the **Mitsuba 3** rendering engine. This allows us to define a complete 3D scene (including buildings and vehicles as geometric shapes like cubes) in an XML file and accurately calculate radio propagation paths, including blockage and reflections from all objects.

## 3. Hardware Dependency & Environment Check

- **Critical Requirement**: SIONNA RT **requires an NVIDIA GPU and the CUDA toolkit**. It cannot run on Apple Silicon (like the M2 chip) or other non-NVIDIA GPUs.

- **Current Status**:
    1.  We confirmed that the **MacBook Air (Apple M2)** is **not compatible** due to the lack of an NVIDIA GPU.
    2.  We identified a **DELL XPS (Ubuntu)** machine as a potential development environment.
    3.  The next step is to **verify if the DELL XPS has an NVIDIA GPU**. The agreed-upon method is to run the `nvidia-smi` command in the Ubuntu terminal.

## 4. Next Steps (On the New Machine)

1.  Open a terminal on the DELL XPS (Ubuntu).
2.  Run the `nvidia-smi` command.
3.  Share the output with me.
    - If the command succeeds and shows an NVIDIA GPU, we will proceed with the original plan to install SIONNA RT in a virtual environment.
    - If the command fails, we will revert to the proposed alternative plan: a CPU-based 3D ray-casting model for blockage detection.

## 5. Implementation & Troubleshooting (Post-Migration)

- **GPU Confirmed**: Successfully ran `nvidia-smi` and confirmed the presence of an NVIDIA GeForce RTX 4070.
- **Environment Setup**: Created a Python virtual environment (`.venv`) and installed `sionna` and its dependencies using `pip`.
- **Core Logic Implemented**:
    - Created `main.py` to orchestrate the simulation.
    - The script successfully loads `scene.json`, converts it to a Mitsuba XML file (`generated_scene.xml`).
- **Execution Error**:
    - Running `main.py` fails with `RuntimeError: No GPU found. SIONNA RT requires a GPU.`.
    - This indicates that TensorFlow, a dependency of Sionna, cannot locate the necessary CUDA libraries.
- **Troubleshooting Steps Taken**:
    - Checked `LD_LIBRARY_PATH`, which was empty.
    - Attempted to run the script with `LD_LIBRARY_PATH` set to the standard `/usr/local/cuda/lib64`, but the error persisted.
    - Searched for the CUDA compiler (`nvcc`) using `which nvcc`, but it was not found in the system's PATH.

## 6. Current Status & Next Steps (After Reboot)

- **Problem**: The exact installation path of the CUDA toolkit is unknown. The environment is not configured correctly for TensorFlow to leverage the GPU.
- **Next Action**: After rebooting, the immediate next step is to locate the CUDA installation directory. Once found, we must update the environment variables (`PATH` and `LD_LIBRARY_PATH`) to point to the correct directories, allowing the simulation to run.
