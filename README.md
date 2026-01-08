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

## 🇨🇳 简体中文版

### ✨ 项目简介

**EPANET-Turbo** 是基于 EPANET 2.2 的高性能水力计算工具包，专为超大规模管网（10万-40万节点）优化。它通过 Polars 并行解析、OpenMP 多线程仿真及 NumPy 向量化数据提取，显著提升了处理效率。

### 🚀 性能对比

| 技术栈 | 原版 WNTR | EPANET-Turbo | 提升倍率 |
|--------|-----------|--------------|----------|
| **INP 解析** | Pandas 逐行 | **Polars 并行 + mmap** | 🚀 **5-6x** |
| **水力仿真** | EPANET DLL (串行) | **OpenMP 多线程** | ⚡ **1.1-2.2x** |
| **结果提取** | 逐节点循环 | **NumPy 向量化** | 💨 **100x+** |

### 📊 真实基准测试

| 模型规模 | 节点数 | Polars 解析 | WNTR 解析 | 加速比 |
|----------|--------|-------------|-----------|--------|
| 10万节点 | 118,796 | 1.07s | 6.49s | **6.1x** |
| 25万节点 | 280,294 | 2.73s | 16.13s | **5.9x** |
| **40万节点** | 442,525 | 7.14s | 32.80s | **4.6x** |

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

### 🚀 Performance Highlights

| Stack | Original WNTR | EPANET-Turbo | Speedup |
|-------|---------------|--------------|---------|
| **INP Parsing** | Pandas line-by-line | **Polars parallel + mmap** | 🚀 **5-6x** |
| **Simulation** | EPANET DLL (serial) | **OpenMP multi-threaded** | ⚡ **1.1-2.2x** |
| **Extraction** | Per-node iteration | **NumPy vectorized** | 💨 **100x+** |

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
