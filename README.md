<div align="center">

# 🏎️ EPANET-Turbo

### 极速水力计算引擎 | High-Performance Hydraulic Engine

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Windows x64](https://img.shields.io/badge/Platform-Windows%20x64-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🇨🇳 简体中文** | [🇬🇧 English](#english)

*Copyright © 2026 ES (Serein) · Project UID: EPANET-TURBO-ES-2026-SEREIN93*

</div>

---

## 📚 文档 (Documentation)

- [📖 开发者指南 (Developer Guide)](DEVELOPER_GUIDE.md): 架构说明、编译构建与测试流程。
- [💾 输出格式规范 (Output Format)](OUTPUT_FORMAT.md): Streaming Sink 结果文件结构说明。

---

## 🇨🇳 简体中文版

### ⚡ 性能突破 (Performance Breakthroughs)

EPANET-Turbo v1.1 实现了从“解算效率”到“工程吞吐”的全面进化：

#### 1. 极致吞吐 (High Throughput) - Open-Once 技术

针对大规模调优/滚动预测场景，消除了 90% 的重复初始化开销：

- **gz_clean (4.7万节点)**: 连续 100 次仿真总耗时从 402s 降至 98s (**🚀 4.1x 整体加速**)
- **核心逻辑**: 内存驻留句柄 (Open-Once) + 批量向量化参数设置 (Batch Setter)

#### 2. 极限规模 (Extreme Scale) - Streaming Sink 技术

彻底解决超大规模模型全量结果提取时的内存溢出问题：

- **40w_fixed (44.2万节点)**:
  > **"442k nodes × 673 steps, RSS peak 142MB, 352s end-to-end (7-day EPS)"**
- **核心逻辑**: Memmap 磁盘映射流式入盘 + 批量结果提取 (Batch Getter **50.6x** 加速)

#### 3. 智能优化 (Intelligent Optimization) - v1.2 新特性 🚀

针对含有复杂规则 (Rules) 的大型巡检模型，通过算法裁剪实现零开销：

- **Time-only Rules Skip**: 自动识别仅时间触发的规则。在未到触发时间前，算法直接跳过规则评估。
- **实测表现**: 在典型城市级 EPS 模型中，规则评估次数降低 **99%**，`rules_eval_count` 从数万次降至个位数。
- **深度透视**: 提供 `ENT_get_profile` API，支持对矩阵装配、线性求解、规则评估耗时的纳秒级监控。

---

### 🗺️ 技术蓝图 (Technical Blueprint)

我们将持续在以下维度深挖水力计算的极限：

- **[M3] 冷启动加速**: 引入 ID 索引缓存与 Baseline Snapshot，实现模型的秒级恢复与“热启动”。
- **[M4] 核心对齐**: 同步 OWA-EPANET v2.3.3 最新改进，确保数值计算的一致性与前沿性。
- **[M5] 线程控制**: 提供多轨 DLL 支持 (Serial/OpenMP)，支持在 Python 端动态切换计算引擎。
- **[M6] 跨平台**: 实现 Linux (Ubuntu/CentOS) 与 macOS (M1/M2) 的原生支持。
- **[M7] Rust 加速层**: 利用 Rust 重写 Batch API 与内部调度器，消除 Python - C 桥接的所有残余开销。
- **[M8] GPU 赋能**: 利用 GPU 处理超大规模场景并行 (Scenario-Ensemble) 与水质后处理张量运算。

---

### 🚀 核心指标对比 (v1.1 vs WNTR)

| 维度 | 原版 WNTR | EPANET-Turbo v1.1 | 价值体现 |
|:---|:---|:---|:---|
| **加载速度** | Pandas 逐行 (32s) | **Polars 并行 (7s)** | 节省 80% 等待时间 |
| **批处理通量** | 重复 Open/Close | **Open-Once 驻留** | **4x+** 批处理通量 |
| **提取加速度** | 逐节点循环 (0.07s) | **Batch Getter (1ms)** | **50x+** 极速数据吞吐 |
| **极限仿真内存** | 随步数线性爆表 | **常数级 RSS (142MB)** | 支撑 44k-40w 规模长时仿真 |

> 测试环境: Windows 10, Intel i7-12700, 32GB RAM, Python 3.12

---

### 🔧 安装说明

#### 1. 自动安装 (推荐)

在项目根目录下运行：

```bash
pip install .
```

这将自动安装所有核心依赖项。

#### 2. 手动安装

如果你只需运行脚本，可先安装依赖：

```bash
pip install -r requirements.txt
```

**环境要求**：

- Python 3.10+
- Windows x64 (OpenMP DLL 仅支持 Windows)
- 核心依赖: `polars>=0.20.0`, `numpy>=1.24.0`, `pandas>=2.0.0`

---

### 🚀 快速入门

```python
from epanet_turbo import InpParser, simulate

# 1. 超快速解析 INP 文件
parser = InpParser("network.inp")
print(f"节点: {parser.num_nodes}, 管道: {parser.num_links}")

# 2. 运行 OpenMP 并行仿真
pressures, flows = simulate("network.inp")

# 3. 向量化访问坐标
x, y = parser.get_node_coordinates("Node_123")
```

---

### 🛡️ 安全、合规与统计

#### 📡 使用统计 (Telemetry)

EPANET-Turbo 收集匿名使用统计（安装次数、版本、IP）以改进产品。**不收集任何模型数据或隐私信息。**
禁用：`set EPANET_TURBO_NO_TELEMETRY=1`

#### 🔐 核心保护

- **工业级混淆**: 业务逻辑已通过 PyArmor 加密。
- **许可证验证**: 每次运行会校验授权，作者保留对滥用行为停用授权的权利。

#### ⚖️ 免责声明

1. **风险自担**: 用户对使用产生的任何结果负全责。
2. **非商业保证**: 不保证所有环境下的绝对稳定。
3. **法律依从**: 请确保使用行为符合当地法律。

---

### 🤝 致谢

**EPANET-Turbo** 的诞生离不开以下贡献：

- **Lee Yau-Wang (皝神)**: 特别感谢其在项目初期提供的关键启发、指导与不懈支持。
- **[EPANET](https://github.com/USEPA/EPANET2.2)**: 感谢美国环保署 (EPA) 开发的标准仿真引擎。
- **[WNTR](https://github.com/USEPA/WNTR)**: 本项目旨在作为 WNTR 在超大型管网场景下的极速补充。

---

<br>

<a name="english"></a>

## 🇬🇧 English Version

### ✨ About

**EPANET-Turbo** is a high-performance hydraulic computation toolkit based on EPANET 2.2, optimized for large-scale water networks (100K-400K nodes). It delivers massive speedups via Polars parallel parsing, OpenMP multi-threading, and NumPy vectorized extraction.

### ⚡ Performance Breakthroughs (v1.1)

EPANET-Turbo v1.1 achieves a complete evolution from "solver efficiency" to "engineering throughput":

#### 1. High Throughput - Open-Once Technology

Eliminates 90% of repetitive initialization overhead for large-scale calibration/rolling prediction:

- **gz_clean (47k nodes)**: Total time for 100 consecutive simulations reduced from 402s to 98s (**🚀 4.1x speedup**)
- **Core Logic**: Memory-resident handles (Open-Once) + Batch Vectorized Parameter Setting (Batch Setter)

#### 2. Extreme Scale - Streaming Sink Technology

Solves memory overflow issues when extracting full results for ultra-large models:

- **40w_fixed (442k nodes)**:
  > **"442k nodes × 673 steps, RSS peak 142MB, 352s end-to-end (7-day EPS)"**
- **Core Logic**: Memmap disk-streaming + Batch Result Extraction (Batch Getter **50.6x** speedup)

#### 3. Intelligent Optimization - v1.2 New Features 🚀

Zero-overhead simulation for models with complex rule logic:

- **Time-only Rules Skip**: Automatically detects time-dependent rules and skips evaluation until the next trigger point.
- **Performance**: Achieves **99% reduction** in rule evaluation counts for typical city-scale EPS models.
- **Deep Profiling**: New `ENT_get_profile` API for nanosecond-level monitoring of matrix assembly, linear solving, and rule evaluation.

---

### 🗺️ Technical Blueprint

The roadmap for pushing the boundaries of hydraulic simulation:

- **[M3] Cold Start Acceleration**: ID index caching and baseline snapshots for near-instant model loading.
- **[M4] Upstream Sync**: Alignment with OWA-EPANET v2.3.3 for numerical consistency and latest fixes.
- **[M5] Unified Build Matrix**: Support for both Serial and OpenMP engines with dynamic switching.
- **[M6] Cross-platform**: Native support for Linux (Ubuntu/CentOS) and macOS (ARM/Intel).
- **[M7] Rust Acceleration Layer**: Replacing bridge logic with high-performance Rust kernels.
- **[M8] GPU Empowerment**: Offloading large-scale ensemble analytics and water quality post-processing to GPUs.

---

### 🚀 Core Metrics Comparison (v1.1 vs WNTR)

| Metric | Original WNTR | EPANET-Turbo v1.1 | Value |
|:---|:---|:---|:---|
| **Loading Speed** | Pandas row-by-row (32s) | **Polars Parallel (7s)** | **6x** Fast Preprocessing |
| **Batch Throughput** | Repeated Open/Close | **Open-Once Resident** | **4x+** Prediction Throughput |
| **Data Extraction** | Per-node Iteration (0.07s) | **Batch Getter (1ms)** | **50x+** Fast Data I/O |
| **Peak Memory** | Linear with steps (OOM) | **Constant RSS (142MB)**| Essential for **100k-400k** nodes |

> Environment: Windows 10, Intel i7-12700, 32GB RAM, Python 3.12

---

---

### 🔧 Installation

#### 1. Automatic (Recommended)

Run in project root:

```bash
pip install .
```

#### 2. Manual Dependencies

```bash
pip install -r requirements.txt
```

**Requirements**:

- Python 3.10+
- Windows x64 (OpenMP DLL is Windows-only)
- Deps: `polars>=0.20.0`, `numpy>=1.24.0`, `pandas>=2.0.0`

---

### 🚀 Quick Start

```python
from epanet_turbo import InpParser, simulate

# 1. Ultra-fast parsing
parser = InpParser("network.inp")

# 2. Run parallel simulation
pressures, flows = simulate("network.inp")

# 3. Vectorized access
x, y = parser.get_node_coordinates("Node_123")
```

---

### 🛡️ Compliance & Telemetry

#### 📡 Telemetry

Anonymous usage stats (install count, version, IP) are collected for improvement. **No model data or personal info collected.**
Disable: `set EPANET_TURBO_NO_TELEMETRY=1`

#### 🔐 Protection

- **Obfuscation**: Logic encrypted via PyArmor.
- **Licensing**: Remote license check enforced. Abuse may lead to revocation.

#### ⚖️ Disclaimer

1. **At Own Risk**: User assumes full responsibility for results.
2. **No Warranty**: Stability is not guaranteed for all environments.
3. **Legal**: Ensure compliance with local regulations.

---

### 🤝 Acknowledgments

Special thanks to the following for their contributions:

- **Lee Yau-Wang (皝神)**: For critical inspiration, guidance, and endless support.
- **[EPANET](https://github.com/USEPA/EPANET2.2)**: For the industry-standard simulation engine.
- **[WNTR](https://github.com/USEPA/WNTR)**: This project is a performance-boosted extension for large-scale WNTR scenarios.

---

<div align="center">

**Made with 🏎️ by ES (Serein) · @Serein93**

</div>
