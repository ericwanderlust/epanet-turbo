# EPANET-Turbo Developer Guide

Welcome to the EPANET-Turbo development documentation. This guide covers the architecture, build process, testing, and release procedures.

## 🏗️ Architecture Overview

EPANET-Turbo consists of two main layers:

1. **C Extended DLL (`src/epanet_turbo.c`)**
    * **Batch Getters/Setters**: Optimized C functions to handle array data transfer between Python and EPANET memory, minimizing `ctypes` overhead.
    * **Profiling Hooks**: Internal timers (`ent_profile_stats`) injected into `hydsolver.c` to measure `Assemble`, `LinearSolve`, etc.
    * **OpenMP**: Parallelization of hydraulic calculations (enabled via `setup.py` build flags).

2. **Python Wrapper (`epanet_turbo/`)**
    * **`InpParserPolars`**: High-performance INP parser using Polars and Regex.
    * **`ModelContext`**: Manages the DLL lifecycle, implementing the **Open-Once** pattern using `_baseline` snapshots to reset state without reloading the INP.
    * **`StreamingSink`**: Handles low-memory output writing using `numpy.memmap`.

## 🛠️ Environment Setup

### Prerequisites

* **OS**: Windows x64 (Primary support target)
* **Python**: 3.10+
* **Compiler**: Visual Studio 2022 (MSVC) with CMake support.

### Installation for Development

1. Clone the repository.
2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Install in editable mode:

    ```bash
    pip install -e .
    ```

## ⚙️ Building the DLL

The project includes a modified EPANET 2.2 source. To rebuild the DLL with Turbo extensions:

### Using CMake (Recommended)

```bash
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

Copy the generated `epanet2.dll` to `epanet_turbo/dll/`.

## 🧪 Testing & Benchmarking

### 1. CI Regression Benchmark

Use the standardized CI script to valid performance and correctness on large models.

```bash
python Py/benchmark_ci.py --inp Example/gz_clean.inp --json benchmark_result.json
```

* **Output**: JSON file with metrics and checksum.
* **Success Criteria**: Status = "success", consistent Checksum.

### 2. Streaming Validation

To verify the streaming sink on extreme scale models:

```bash
python Py/benchmark_streaming.py
```

*(Note: Requires `Example/40w_fixed.inp` for stress testing)*

## 📦 Release Process

We use **PyArmor** to obfuscate core logic before release.

1. **Run Encryption**:

    ```bash
    cd epanet-turbo
    python build_encrypted.py --encrypt
    ```

    This generates a `dist_encrypted/` directory containing the obfuscated package.

2. **Verify Distribution**:
    Install the generated package in a fresh environment to ensure it works without the source `.py` files.

## 📄 Output Format Specification

For details on the `.npy`/`.json` streaming output format, please refer to:
[OUTPUT_FORMAT.md](OUTPUT_FORMAT.md)
