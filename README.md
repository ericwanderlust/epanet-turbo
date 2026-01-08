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

## ✨ 项目简介

**EPANET-Turbo** 是基于 EPANET 2.2 的高性能水力计算工具包，专为超大规模管网（10万-40万节点）优化。

### 🚀 性能对比

| 技术栈 | 原版 WNTR | EPANET-Turbo | 提升倍率 |
|--------|-----------|--------------|----------|
| INP 解析 | Pandas 逐行 | **Polars 并行 + mmap** | 🚀 **5-6x** |
| 水力仿真 | EPANET DLL (串行) | **OpenMP 多线程** | ⚡ **1.1-2.2x** |
| 结果提取 | 逐节点循环 | **NumPy 向量化** | 💨 **100x+** |

### 📊 真实基准测试

| 模型规模 | 节点数 | Polars 解析 | WNTR 解析 | 加速比 |
|----------|--------|-------------|-----------|--------|
| 10万节点 | 118,796 | 1.07s | 6.49s | **6.1x** |
| 25万节点 | 280,294 | 2.73s | 16.13s | **5.9x** |
| **40万节点** | 442,525 | 7.14s | 32.80s | **4.6x** |

> 测试环境: Windows 10, Intel i7-12700, 32GB RAM, Python 3.12

---

## 🔧 安装

```bash
pip install epanet-turbo
```

**环境要求**：

- Python 3.10+
- Windows x64 (OpenMP DLL 仅支持 Windows)
- 依赖: `polars`, `numpy`, `pandas`

---

## 🚀 快速入门

```python
from epanet_turbo import InpParser, simulate

# 1. 超快速解析 INP 文件
parser = InpParser("large_network.inp")
print(f"节点数: {parser.num_nodes}, 管道数: {parser.num_links}")

# 2. 运行 OpenMP 并行仿真
pressures, flows = simulate("large_network.inp")
print(f"时间步: {len(pressures)}")

# 3. 向量化访问坐标
x, y = parser.get_node_coordinates("Node_12345")
```

---

## 📡 使用统计

EPANET-Turbo 会收集匿名使用统计（安装次数、版本号、IP），帮助我们改进产品。

**不会收集任何模型数据或敏感个人信息。**

禁用方法：

```bash
set EPANET_TURBO_NO_TELEMETRY=1
```

---

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE)

**附加条款**: 作者保留在发现滥用时撤销使用许可的权利。

---

<a name="english"></a>

<div align="center">

# English Documentation

</div>

## ✨ About

**EPANET-Turbo** is a high-performance hydraulic computation toolkit based on EPANET 2.2, optimized for large-scale water networks (100K-400K nodes).

### Performance Highlights

| Component | Original WNTR | EPANET-Turbo | Speedup |
|-----------|---------------|--------------|---------|
| INP Parsing | Pandas line-by-line | **Polars parallel + mmap** | 🚀 **5-6x** |
| Simulation | EPANET DLL (serial) | **OpenMP multi-threaded** | ⚡ **1.1-2.2x** |
| Result Extraction | Per-node iteration | **NumPy vectorized** | 💨 **100x+** |

---

## 🔧 Installation

```bash
pip install epanet-turbo
```

**Requirements**:

- Python 3.10+
- Windows x64 (OpenMP DLL is Windows-only)
- Dependencies: `polars`, `numpy`, `pandas`

---

## 🚀 Quick Start

```python
from epanet_turbo import InpParser, simulate

# 1. Ultra-fast INP parsing
parser = InpParser("large_network.inp")
print(f"Nodes: {parser.num_nodes}, Links: {parser.num_links}")

# 2. Run OpenMP parallel simulation
pressures, flows = simulate("large_network.inp")

# 3. Vectorized coordinate access
x, y = parser.get_node_coordinates("Node_12345")
```

---

## 📡 Telemetry

EPANET-Turbo collects anonymous usage statistics (install count, version, IP) to improve the product.

**No model data or sensitive personal information is collected.**

To disable:

```bash
set EPANET_TURBO_NO_TELEMETRY=1
```

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

**Additional Terms**: The author reserves the right to revoke license upon abuse detection.

---

<div align="center">

**Made with 🏎️ by ES (Serein) · @Serein93**

</div>
