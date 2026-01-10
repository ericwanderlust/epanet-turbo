# EPANET-Turbo Developer Guide

Welcome to the EPANET-Turbo developer documentation. This guide details the project architecture, build system, and workflow for contributors.

---

## 1. Project Architecture (架构概览)

The project consists of three main layers, designed for maximum performance and separation of concerns.

### Layer 1: The Core Engine (C Layer)

* **Base**: OWA-EPANET 2.3.3 (Community Edition).
* **Extensions**: See `src/epanet_turbo.c`.
  * **Batch API**: `ENT_set_node_values`, `ENT_set_link_values` for bulk parameter modification.
  * **Engine Identity**: `ENT_engine_id` to identify Serial vs OpenMP kernels.
* **Optimizations**:
  * `hydsolver.c`: OpenMP pragmas added to main solver loops.
  * `smatrix.c`: Parallelized matrix assembly.

### Layer 2: The Interface (Python CTypes)

* **Location**: `epanet_turbo/engine.py` (Encrypted in distribution).
* **Role**:
  * Loads the appropriate DLL/SO (`epanet2_openmp` preferred).
  * Maps C functions to Python methods.
  * Handles memory buffer conversions (Numpy <-> C Pointers).

### Layer 3: The High-Level API (Python Polars)

* **Location**: `epanet_turbo/parser.py`, `epanet_turbo/streaming.py`.
* **Role**:
  * **InpParser**: Reads INP files into Polars DataFrames using Rust optimizations.
  * **StreamingReporter**: Implements **Protocol V2** (see `OUTPUT_FORMAT.md`) for zero-copy binary results writing.

---

## 2. Unified Build Matrix (统一构建矩阵)

We use **CMake** to manage the complexity of building multiple targets (Serial vs Parallel) across multiple platforms (Windows vs Linux).

### CMake Logic

The `CMakeLists.txt` defines two primary targets:

* **`epanet2`**: The standard serial engine.
  * Defines: `EPNT_SERIAL=1`
* **`epanet2_openmp`**: The enhanced parallel engine.
  * Defines: `EPNT_OPENMP=1`
  * Links: `OpenMP::OpenMP_C`

### Building on Windows (Visual Studio)

Prerequisites: Visual Studio 2022 (or 2019) with C++ CMake tools.

```powershell
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

Artifacts: `build/Release/epanet2.dll`, `build/Release/epanet2_openmp.dll`.

### Building on Linux (GCC/Make)

Prerequisites: `build-essential`, `cmake`, `libomp-dev`.

```bash
mkdir build
cd build
cmake ..
make -j4
```

Artifacts: `build/libepanet2.so`, `build/libepanet2_openmp.so`.

---

## 3. Encryption & IP Protection (加密与保护)

EPANET-Turbo follows an **"Open Core, Protected Logic"** philosophy.

* **Open Source**: The C engine (OWA based) is visible in `src/`.
* **Protected**: The high-level Python logic and specific Turbo optimizations are distributed as encrypted bytecode.

### Build Flow

1. **Source**: The C source (`src/`) and Python source (`epanet_turbo/`) are kept in `private_src/` for security.
2. **Encrypt & Compile**: Run `python build_encrypted.py` (internal tool).
    * Compiles C code to DLLs/SOs.
    * Obfuscates Python code using PyArmor.
3. **Distribute**: The public repository contains only:
    * `epanet_turbo/` (Encrypted Python + Pre-compiled DLLs).
    * `include/` (Public headers).

> **Note**: This repository operates in **Binary Distribution Mode**. Linux users require a pre-compiled `libepanet2.so` in `epanet_turbo/dll/` or system path.

---

## 4. Verification Protocols (验证协议)

### 4.1 Build Matrix Verification

Run the dedicated verification script to check DLL symbols and engine IDs:

```bash
python verify_build_matrix.py
```

### 4.2 Linux Verification (Colab)

Use `colab_linux_m5.ipynb` to verify the full install-build-run cycle on a fresh Linux environment (Simulating a production server).

---

## 5. Coding Standards

* **C Code**: Follows K&R style (Legacy OWA style + Modern C99).
* **Python**: Type-hinted (Python 3.10+), snake_case, using `ruff` for linting.
* **Streaming Format**: Adhere to `Protocol V2` spec in `OUTPUT_FORMAT.md`.
* **Commits**: Use Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `perf:`).

---

*Verified for v2.0.0 Release*
