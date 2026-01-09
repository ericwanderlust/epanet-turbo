# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-01-09 - Performance & Controls Milestone

### 🏎️ Performance Optimizations (M2)

- **M2-1 Time-only Rules Skip**: Added optimization to skip evaluation of rules that only depend on time until their next trigger point. Achieved **99% skip ratio** on time-based models.
- **M2-0 Profiling Decomposition**: Separated rules evaluation and simple controls evaluation in the profiling report for better bottleneck analysis.
- **Improved Profiling API**: Added `ENT_get_profile` and `ENT_debug_rule_info` to the core DLL for deep inspection.

### 🛠️ Engineering & Stability

- Refined DLL export macros for consistent cross-platform symbol visibility.
- Fixed header inclusion order enforcement to prevent build errors.
- Cleaned up temporary build artifacts and unnecessary repository files.

### 🛡️ Security & Packaging

- Refreshed PyArmor encryption for core modules.
- Updated documentation with M5 OpenMP and M8 GPU strategy.

## [1.1.2] - 2026-01-09

### 🛡️ Engineering & Stability (Build Green)

- **Header Inclusion Contract**: Enforced `types.h` -> `funcs.h` order using `#error` mechanism to prevent build cascading failures.
- **Build Stabilization**: Fixed `rules.c` syntax errors and header order in 18 source files.
- **DLL Production**: Standard `epanet2.dll` is now stably reproducible via CMake.

## [1.1.0] - 2026-01-09

### 🚀 Major Features

- **Open-Once Architecture**: Eliminates 90% overhead in repetitive simulations. 4.1x speedup for optimization tasks.
- **Streaming Sink**: Memmap-based output support for extreme scale models (440k+ nodes). RSS peak < 250MB.
- **Batch Data APIs**: Vectorized `get_all_node_values`/`set_node_values` achieving 50x IO speedup.

### ⚡ Improvements

- **Polars Parser**: Replaced Pandas for 6x faster INP loading.
- **Documentation**: Added `DEVELOPER_GUIDE.md` and `OUTPUT_FORMAT.md`.
- **Packaging**: Industrial-grade PyArmor encryption for core logic.

### 🧪 Benchmarks

- Verified on **442k node** network: 7-day EPS simulation in **352s** with **142MB RSS**.

## [0.1.0] - 2026-01-08

### 🚀 Initial Release

#### Features

- **Polars INP Parser**: 5-6x faster than WNTR for large networks (100K-400K nodes)
- **OpenMP DLL Integration**: Multi-threaded hydraulic simulation
- **NumPy Vectorization**: 100x faster result extraction
- **WNTR Compatibility**: Drop-in replacement API

#### Security

- License verification system
- Remote blocklist support
- Device fingerprint tracking
- Telegram usage notifications

#### Documentation

- Bilingual README (中文/English)
- MIT License with additional terms
- Quick start examples

---

*Made with 🏎️ by ES (Serein)*
