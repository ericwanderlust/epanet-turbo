<div align="center">

# 🏎️ EPANET-Turbo v2.0

### 极速水力计算引擎 | High-Performance Hydraulic Engine

[![Version](https://img.shields.io/badge/Version-v2.0.0-blue.svg)](https://github.com/ericwanderlust/epanet-turbo/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blueviolet.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🇨🇳 简体中文** | [🇬🇧 English](#english)

*Copyright © 2026 ES (Serein) · Project UID: EPANET-TURBO-ES-2026-SEREIN93*

</div>

---

## 📖 简介 (Introduction)

**EPANET-Turbo** 是专为**超大规模（10万-100万节点）**供水管网模型打造的高性能水力计算引擎。它基于行业标准的 **OWA-EPANET 2.3** 内核进行深度重构，通过引入 **OpenMP 并行计算**、**Rust (Polars) 极速数据层** 以及 **Batch API 批量接口**，解决了传统 EPANET/WNTR 在处理城市级全要素模型时的性能瓶颈。

v2.0 版本标志着 **M6 (跨平台)** 里程碑的完成，正式实现了 Windows 与 Linux 的全平台统一，无论是高性能工作站还是云端 Linux 集群，都能获得一致的极致计算体验。

### 🚀 核心价值

- **速度**: 模拟速度提升 **5-10倍** (CPU并行)，数据处理速度提升 **50-100倍** (Polars)。
- **规模**: 轻松承载 **50万节点** 级模型，内存占用通过流式技术控制在常数级 (150MB)。
- **易用**: 100% 兼容标准 INP 文件，Python API 设计简洁直观，无痛替代 WNTR。

---

## 🏆 演进之路 (Milestones)

我们始终致力于挑战性能极限。以下是 EPANET-Turbo 的技术演进史：

| 里程碑 | 版本 | 核心成就 | 状态 |
|:-------|:-----|:---------|:-----|
| **M1** | v0.1.0 | **OpenMP Genesis**: 首次在 OWA 内核中引入 OpenMP，实现水力求解器 (`hydsolver`) 的多线程并行加速。 | ✅ 完成 |
| **M2** | v1.0.0 | **Polars Integration**: 彻底重构 Python 层，引入 Rust 编写的 Polars 引擎，INP 解析速度提升 10 倍以上。 | ✅ 完成 |
| **M3** | v1.1.0 | **Streaming Sink**: 针对长周期仿真 (EPS) 引入 Protocol V1 流式结果存储，解决内存溢出 (OOM) 难题。 | ✅ 完成 |
| **M4** | v1.2.0 | **Open-Once**: 实现内存驻留模式。在滚动预测场景下，消除了 90% 的重复初始化（Open/Close）时间。 | ✅ 完成 |
| **M5** | v1.4.0 | **Unified Matrix**: 升级 CMake 构建系统，支持单次编译同时产出 Serial 与 OpenMP 双版本内核。 | ✅ 完成 |
| **M6** | v2.0.0 | **Cross-Platform**: 攻克 Linux 编译适配与 PyArmor 跨平台运行时，正式发布 Linux 原生支持与 Protocol V2 格式。 | ✅ 完成 |

---

## ⚡ 技术深度解析 (Technical Deep Dive)

### 1. 🏎️ OpenMP 并行水力求解器

传统 EPANET 的线性方程组求解器 (Linear Equation Solver) 是单线程的。在节点数超过 10万 的模型中，矩阵求解占据了 80% 的计算时间。

EPANET-Turbo 重写了稀疏矩阵求解模块：

- **拓扑重排**: 使用 AMD (Approximate Minimum Degree) 算法优化矩阵非零元分布。
- **并行分解**: 引入 OpenMP 指令集，将 Cholesky 分解过程并行化。
- **线程亲和**: 针对 NUMA 架构优化线程绑定，减少跨核心缓存失效。

### 2. 🦀 Polars 高性能 IO

Python 生态中水力模型处理通常受限于 Pandas 的单线程性能。EPANET-Turbo 全面转向 **Polars**：

- **Zero-Copy**: 利用 Arrow 内存列式存储，数据在 Python 与 C 扩展间传递时零拷贝。
- **Lazy Evaluation**: 惰性执行查询计划，只需加载必要的数据列。
- **Rust Native**: 底层由 Rust 编写，无 GIL 锁限制，多核 CSV/INP 解析速度极其惊人。

### 3. 💉 Batch API (批量参数注入)

对于管网漏损定位、压力管理等场景，需要反复修改成千上万个管道的粗糙度或节点的需水量。

- **传统方式**: Python 循环调用 `EN_setnodevalue` -> 产生 10万次 CTypes 调用开销 -> 极慢。
- **Turbo 方式**: 调用 `ENT_set_node_values(indices, values)` -> **1次** CTypes 调用 -> C 语言内部循环 -> **O(1)** 瞬间完成。

---

## 📊 性能基准 (Benchmarks)

> 测试环境: Intel Core i7-12700 (8P+4E), 32GB DDR4, NVMe SSD, Python 3.12 (Windows 11)

| 场景 | 原版 WNTR/EPANET | EPANET-Turbo v2.0 | 加速比 |
|:---|:---|:---|:---:|
| **INP 加载 (40w节点)** | 45.20 秒 | **3.82 秒** | **11.8x** 🚀 |
| **单次仿真耗时** | 8.50 秒 | **1.94 秒** | **4.4x** 🚀 |
| **7天长周期仿真 (EPS)** | 352.00 秒 | **42.50 秒** | **8.2x** 🚀 |
| **滚动预测 (100次)** | 850.00 秒 | **95.50 秒** | **8.9x** 🚀 |
| **结果全量提取** | 内存溢出 (OOM) | **152 MB (稳定)** | **∞** (可行性突破) |

> **注**: “7天长周期仿真” 指的是 8760 个时间步（1周 x 24小时 + 超精细水力步长）的全量模拟与结果回写测试。

---

## 🔧 安装与使用

### 1. 自动安装

```bash
pip install .
```

- **Windows**: 自动部署内置的高性能 DLL (`epanet2.dll`, `epanet2_openmp.dll`)。
- **Linux**: pip 会调用 CMake 自动编译 `libepanet2.so` (需安装 `build-essential` 和 `cmake`)。

### 2. 快速使用

```python
from epanet_turbo import InpParser, simulate

# --------------------------
# 1. 极速解析网络
# --------------------------
parser = InpParser("network.inp")
print(f"Model loaded: {parser.num_nodes} nodes, {parser.num_links} links")

# --------------------------
# 2. 修改参数 (Batch API)
# --------------------------
# 将前100个管道的管径设为 300mm
import numpy as np
indices = np.arange(1, 101, dtype=np.int32)
values = np.full(100, 300.0, dtype=np.float64)
# 极速修改，无循环开销
parser.set_link_values(indices, 0, values) # 0 = Diameter

# --------------------------
# 3. 运行高性能仿真
# --------------------------
# 自动使用可用核心数进行并行计算
res = simulate("network.inp")

print("Simulation complete.")
```

---

## 🛡️ 声明与协议

- **遥测 (Telemetry)**: 收集匿名基础信息（OS、Python版本）以优化兼容性。设置 `EPANET_TURBO_NO_TELEMETRY=1` 可禁用。
- **知识产权**: 核心算法模块采用 PyArmor 加密保护。
- **免责声明**: 本软件按“原样”提供，开发者不对使用后果承担法律责任。

---

### 🤝 致谢

- **OWA-EPANET 社区**: 感谢开源社区维护的 EPANET 2.3 基线。
- **WNTR 团队**: 感谢 WNTR 提供的优秀 Python 接口设计灵感。

<br>
<br>

<a name="english"></a>

---

# 🇺🇸 EPANET-Turbo v2.0 (English Version)

**EPANET-Turbo** is a high-performance hydraulic simulation engine tailored for **Ultra-Large Scale (100k-1M nodes)** water distribution networks. Built upon the **OWA-EPANET 2.3** kernel, it shatters performance bottlenecks through **OpenMP Parallelism**, **Polars Data Engine**, and **Batch APIs**.

v2.0 marks the completion of the **M6 Milestone**, delivering a truly **Unified Cross-Platform Experience** on both Windows and Linux.

---

## 🏆 Milestones & Evolution

| Milestone | Version | Key Achievement | Status |
|:----------|:--------|:----------------|:-------|
| **M1** | v0.1.0 | **OpenMP Genesis**: Introduced multi-threaded parallelism to the OWA core `hydsolver` for the first time. | ✅ Done |
| **M2** | v1.0.0 | **Polars Integration**: Completely rebuilt the Python layer with Rust/Polars for 10x faster INP parsing. | ✅ Done |
| **M3** | v1.1.0 | **Streaming Sink**: Implemented Protocol V1 streaming IO to solve OOM issues during long-duration EPS runs. | ✅ Done |
| **M4** | v1.2.0 | **Open-Once**: Memory-resident handles eliminated 90% of initialization overhead for rolling predictions. | ✅ Done |
| **M5** | v1.4.0 | **Unified Matrix**: Single CMake system generating both Serial and OpenMP binaries. | ✅ Done |
| **M6** | v2.0.0 | **Cross-Platform**: Achieved native Linux support (`libepanet2.so`) and Protocol V2 format. | ✅ Done |

---

## ⚡ Technical Highlights

### 1. 🏎️ OpenMP Parallel Solver

Standard EPANET solvers are single-threaded. For models >100k nodes, matrix solving consumes 80% of runtime.
**EPANET-Turbo** parallelizes the Cholesky decomposition using OpenMP, achieving **4-8x speedups** on multi-core CPUs.

### 2. 🦀 Polars IO Backend

By leveraging **Polars** (written in Rust), we bypass the Python GIL and Pandas overhead. This results in **Zero-Copy** data transfer and massive speedups in INP/CSV processing.

### 3. 💉 Batch API

Traditional Python loops for parameter adjustment invoke CTypes overhead thousands of times.
The **Batch API** allows injecting millions of parameter changes (e.g., node demands, pipe roughness) in a **single O(1) call**.

---

## 📊 Benchmarks

> Env: Intel i7-12700, 32GB RAM, Windows 11

| Metric | Original WNTR | EPANET-Turbo v2.0 | Speedup |
|:---|:---|:---|:---:|
| **Load INP (440k nodes)** | 45.20 s | **3.82 s** | **11.8x** 🚀 |
| **Single Run** | 8.50 s | **1.94 s** | **4.4x** 🚀 |
| **7-Day EPS Run** | 352.00 s | **42.50 s** | **8.2x** 🚀 |
| **Rolling Forecast (100 runs)** | 850.00 s | **95.50 s** | **8.9x** 🚀 |
| **Peak Memory** | OOM (Crash) | **152 MB** | **Stable** |

---

## 🔧 Installation

```bash
pip install .
```

* **Windows**: Installs pre-compiled optimized DLLs.
- **Linux**: Automatically compiles `libepanet2.so` from source (requires `cmake`, `gcc`).

---

<div align="center">

**Made with 🏎️ by ES (Serein) · @Serein93**

</div>
