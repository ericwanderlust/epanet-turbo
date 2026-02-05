<div align="center">

# 🏎️ EPANET-Turbo v2.8

### 极速水力计算引擎 | High-Performance Hydraulic Engine

[![Version](https://img.shields.io/badge/Version-v2.8.0-blue.svg)](https://github.com/ericwanderlust/epanet-turbo/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%20(Parallel)%20%7C%20Mac%20%7C%20Linux-blueviolet.svg)]()
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🇨🇳 简体中文** | [🇬🇧 English](#english)

*Copyright © 2026 ES (Serein) · Project UID: EPANET-TURBO-ES-2026-SEREIN93*

</div>

---

## 📖 简介 (Introduction)

**EPANET-Turbo** 是专为**超大规模（10万-100万节点）**供水管网模型打造的高性能水力计算引擎。它基于行业标准的 **OWA-EPANET 2.3** 内核进行深度重构，通过引入 **OpenMP 并行计算**、**Rust (Polars) 极速数据层** 以及 **Batch API 批量接口**，解决了传统 EPANET/WNTR 在处理城市级全要素模型时的性能瓶颈。

v2.0 版本标志着 **M6 (全平台原生支持)** 里程碑的完成，正式实现了 **Windows、macOS (Apple Silicon/Intel) 与 Linux** 的全平台统一。

**v2.8 (M8)** 版本引入了 **Rust 高性能绑定**，实现了线程安全的批量数据接口与**零干扰静默运行**模式。

### 🚀 核心价值

- **速度**: 模拟速度提升 **5-10倍** (CPU并行)，数据处理速度提升 **50-100倍** (Polars)。
- **规模**: 轻松承载 **50万节点** 级模型，内存占用通过流式技术控制在常数级 (150MB)。
- **易用**: 100% 兼容标准 INP 文件，Python API 设计简洁直观，无痛替代 WNTR。
- **智能**: 自动识别并适配 **ARM/Rosetta** (Mac Parallels) 环境；内置**自愈 (Self-Healing)** 机制，自动修复依赖损坏。

---

## 🏆 演进之路 (Milestones)

我们始终致力于挑战性能极限。以下是 EPANET-Turbo 的技术演进史：

| 里程碑   | 版本   | 核心成就                                                                                                                              | 状态    |
| :------- | :----- | :------------------------------------------------------------------------------------------------------------------------------------ | :------ |
| **M1**   | v0.1.0 | **OpenMP Genesis**: 首次在 OWA 内核中引入 OpenMP，实现水力求解器 (`hydsolver`) 的多线程并行加速。                                     | ✅ 完成 |
| **M2**   | v1.0.0 | **Polars Integration**: 彻底重构 Python 层，引入 Rust 编写的 Polars 引擎，INP 解析速度提升 10 倍以上。                                | ✅ 完成 |
| **M3**   | v1.1.0 | **Streaming Sink**: 针对长周期仿真 (EPS) 引入 Protocol V1 流式结果存储，解决内存溢出 (OOM) 难题。                                     | ✅ 完成 |
| **M4**   | v1.2.0 | **Open-Once**: 实现内存驻留模式。在滚动预测场景下，消除了 90% 的重复初始化（Open/Close）时间。                                        | ✅ 完成 |
| **M5**   | v1.4.0 | **Unified Matrix**: 升级 CMake 构建系统，支持单次编译同时产出 Serial 与 OpenMP 双版本内核。                                           | ✅ 完成 |
| **M6**   | v2.0.0 | **原生全平台**: Windows / macOS / Linux 全适配                                                                                        | ✅ 完成 |
| **M6-2** | v2.1.0 | **Rules Optimization** *(Windows)*: 规则引擎状态驱动优化，1000规则模型 controls 占比从 11% 降到 0.07%，跳过率 99.93%                  | ✅ 完成 |
| **M6-3** | v2.2.0 | **Parallel Numerical Engine** *(Windows)*: 实现并行水头损失计算与分段锁矩阵组装，加速比提升至 2.6x (16核)，保持 100% 数值确定性       | ✅ 完成 |
| **M7**   | v2.3.0 | **Convergence Optimization** *(Windows)*: **目标自适应松弛**。解决长尾震荡，**2.8倍** 提速大模型求解（40w节点 403s -> 142s）。        | ✅ 完成 |
| **M8**   | v2.8.0 | **Rust Bindings + Silent Mode**: **Rust 高性能绑定**。线程安全批量接口 + 零干扰静默运行，彻底消除控制台噪音。                         | ✅ 完成 |

### 🔮 未来蓝图 (Future Blueprint)

我们不会止步于此。2026 年接下来的计划：

| 里程碑  | 预估版本 | 核心目标                                                                                                                                 | 状态      |
| :------ | :------- | :--------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| **M9**  | v2.9.0   | **NMM/CHOLMOD 优化**: 病态模型正确性修复 + 自动降级策略。                                                                                | 🚧 开发中 |
| **M10** | v3.0.0   | **GPU Empowerment (Outer-loop)**: 针对外层循环（校准/优化/不确定性分析）的 GPU 原生加速。将数万次串行仿真转化为 GPU 上的并行 Tensor 运算。 | 📅 规划中 |
| **M11** | v4.0.0   | **AI Surrogate**: 内置图神经网络 (GNN) 代理模型精度校准，实现"预测-仿真"混合双驱。                                                       | 📅 规划中 |

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

### 4. 🎯 v2.1 新特性: 规则引擎状态驱动优化 *(Windows)*

对于包含大量控制规则 (RULES) 的模型，规则评估可能占据 10-20% 的仿真时间。v2.1 引入了**状态驱动跳过**机制：

- **依赖追踪**: 每条规则在编译时分析其依赖的节点/管段。
- **代际标记**: 液压求解后，仅标记状态发生变化的元素。
- **智能跳过**: 如果规则依赖的元素未变化，直接跳过评估。

**性能对比** (1000条规则模型):

| 指标          | 优化前    | v2.1 优化后    | 提升          |
| :------------ | :-------- | :------------- | :------------ |
| Controls 占比 | 11.24%    | **0.07%**      | **↓ 160x**    |
| 规则评估次数  | 1,440,000 | **1,000**      | **↓ 1440x**   |
| 跳过率        | 0%        | **99.93%**     | -             |

### 5. 🎯 v2.2 新特性: 并行数值计算引擎 (Parallel Numerical Engine) *(Windows)*

针对大规模管网（5万+节点）中耗时最长的计算环节进行了并行重构：

- **并行水头损失 (Parallel Headloss)**: 利用 OpenMP 将数万个管段的水力特性计算分发至多核 CPU。
- **并行矩阵组装 (Parallel Assembly)**:
  - **Phase A (Bucket-Lock)**: 引入分段桶锁技术，解决了多个线程同时更新同一个节点 Aii/F 矩阵时的竞态问题。
  - **数值确定性**: 与完全乱序的归约不同，此方案保证了计算结果的 **Bit-identical** (位一致性)，满足严苛的科学计算审计要求。

### 6. 🎯 v2.3 (M7) 新特性: 目标自适应松弛 (Targeted Adaptive Relaxation) *(Windows)*

针对大流速、低压头等极端水力条件下出现非线性迭代 **"长尾震荡"** (Long-tail Oscillation) 问题，M7 引入了智能松弛策略：

- **震荡检测**: 实时监控误差变化率。当迭代次数 > 10 且误差不降反升时，判定为微观震荡。
- **激进阻尼**: 自动切入 `RelaxFactor = 0.5` 强阻尼模式，迅速打破数值死循环。
- **性能红利**: 将 `40w_fixed` 等高难度模型的平均迭代次数从 5.3 压降至 1.01，整体仿真速度提升 **2.8倍**。

### 7. 🎯 v2.8 (M8) 新特性: Rust 高性能绑定 + 静默模式

**Rust Bindings**: 全新 Rust 后端，解决多线程 GIL 竞争问题：

- **线程安全**: 运行时优先使用 Rust 后端，自动降级到 ctypes。
- **批量接口**: `get_all_pressures()`, `set_node_values()` 减少 Python/C 调用开销。
- **零干扰**: 彻底消除 "Page 1..."、"Balanced after 5 trials..." 等控制台噪音。
- **验证精度**: Max Pressure Error: 2.33e-08, Max Flow Error: 5.03e-06 (与标准 EPANET 完全一致)

> ⚠️ 注意：并行数值引擎与 M7/M8 优化特性目前仅支持 **Windows x64** 平台。macOS/Linux 仍使用单线程高可靠模式运行。

---

## 📊 性能基准 (Benchmarks)

> 测试环境: Intel Core i7-12700 (8P+4E), 32GB DDR4, NVMe SSD, Python 3.12 (Windows 11)

| 场景                            | 原版 WNTR/EPANET | EPANET-Turbo v2.8     | 加速比               |
| :------------------------------ | :--------------- | :-------------------- | :------------------- |
| **INP 加载 (40w节点)**          | 45.20 秒         | **3.82 秒**           | **11.8x** 🚀         |
| **单线程水力求解 (4.7w节点)**   | 44.02 秒         | **42.10 秒**          | **1.0x**             |
| **16核并行水力求解 (4.7w节点)** | 44.02 秒         | **16.65 秒**          | **2.6x** 🚀          |
| **7天长周期仿真 (40w节点)**     | 352.00 秒        | **42.50 秒**          | **8.2x** 🚀          |
| **结果全量提取**                | 内存溢出 (OOM)   | **152 MB (稳定)**     | **∞** (可行性突破)   |

> **注**: "7天长周期仿真" 指的是 8760 个时间步（1周 x 24小时 + 超精细水力步长）的全量模拟与结果回写测试。

---

## 📂 项目结构 (Project Structure)

| 目录/文件               | 说明                                                                                              |
| :---------------------- | :------------------------------------------------------------------------------------------------ |
| **`src/epanet_turbo/`** | **Python 包源码** (Core Package Source)                                                           |
| ├──`dll/`               | **预编译内核**: 包含 `epanet2.dll` (Win), `libepanet2.dylib` (Mac), `libepanet2.so` (Linux)        |
| ├──`engine.py`          | 底层驱动: 负责加载 DLL 并通过 CTypes 调用 C 函数                                                   |
| ├──`parser.py`          | **Polars 解析器**: 极速读取 INP 文件                                                              |
| ├──`streaming.py`       | 流式输出器: 实现 Protocol V2 二进制写出                                                           |
| **`resources/`**        | **资源归档**: 原始二进制库备份与辅助文件                                                          |
| **`include/`**          | **C 头文件**: 包含 `epanet2.h` 等开发所需的 API 定义                                               |
| **`dev_tools/`**        | **开发工具箱**: 构建脚本 (`make_release.py`) 与 CI/CD 工具                                         |
| **`examples/`**         | **开源示例 (Open Source)**: 供用户学习与复制                                                      |
| ├──`quickstart.py`      | 基础功能演示                                                                                      |
| ├──`turbo_adapter.py`   | **WNTR 适配器** (可直接复制到您项目中使用)                                                        |
| ├──`demo_adapter.py`    | WNTR 迁移演示脚本                                                                                 |
| └──`Net3.inp`           | 示例管网文件                                                                                      |
| `pyproject.toml`        | 项目配置文件 (依赖管理、元数据)                                                                   |
| `setup_and_demo.py`     | **一键安装验证脚本**: 自动配置环境并运行测试                                                      |

---

## 🔁 迁移与集成 (Migration & Integration)

### Q1: 我正在使用 OWA-EPANET 2.3，如何迁移？

EPANET-Turbo 与 OWA-EPANET **100% 兼容**。

- **INP 文件**: 无需任何修改。
- **API 接口**: 标准函数（如 `ENopen`, `ENsolveH`）的行为完全一致。
- **性能飞跃**: 要解锁 100 倍以上的加速，请将传统的 Python 循环替换为 Turbo 专有的 **Batch API** (`ENT_set_node_values`)。

### Q2: 我正在使用 WNTR，这是替代品吗？

**它是互补关系，而非替代关系。**

- **WNTR**: 擅长拓扑分析、韧性评估、脆弱性曲线等复杂建模。
- **Turbo**: 擅长**纯粹的计算爆发力**（大规模、高频次仿真）。

**推荐的混合工作流**:

1. 使用 **WNTR** 构建或修改管网结构。
2. 通过 `wn.write_inpfile()` 导出临时 INP。
3. 使用 **EPANET-Turbo** 进行大规模仿真（蒙特卡洛、PDA 等）。
4. 加载二进制结果进行后续分析。

> 💡 参见示例: [demo_adapter.py](examples/demo_adapter.py) (展示如何将 WNTR 与项目集成)

---

## 📚 Documentation (文档)

- **[Developer Guide / 开发者指南](DEVELOPER_GUIDE.md)**:
  - Architecture design, directory structure, and compilation guide.
  - 架构设计、目录结构与编译指南。
- **[Output Format / 输出格式](OUTPUT_FORMAT.md)**:
  - Detailed explanation of the Protocol V2 binary output format.
  - Protocol V2 二进制输出格式的详细说明。
- **[Release Notes / 版本说明](RELEASE_NOTES_v2.8.0.md)**:
  - Change log and new features for v2.8.0.
  - v2.8.0 版本的更新日志与新特性。

---

## 🔧 部署与安装 (Deployment)

EPANET-Turbo 采用 **"全平台二进制分发"** 模式，用户无需安装 C/C++ 编译器即可直接使用。

### 1. 环境要求

- **OS**: Windows 10/11 (x64), Linux (glibc 2.29+), macOS (Apple Silicon/Intel)
- **Python**: 3.10, 3.11, 3.12 (推荐 3.12 以获得最佳性能)
- **核心依赖**:
  - `polars >= 0.20.0` (极速数据处理)
  - `numpy >= 1.20.0` (数值计算)

### 2. 安装步骤 (Installation)

前往 [Github Releases](https://github.com/ericwanderlust/epanet-turbo/releases) 下载最新的发布包 ZIP。

**推荐方式 (一键安装器)**:

```bash
# 在解压后的目录中直接运行，自动创建虚拟环境并验证
python setup_and_demo.py
```

**手动方式 (直接安装 Wheel)**:

```bash
pip install epanet_turbo-2.8.0-py3-none-any.whl
```

### 3. 验证安装 (Verification)

安装完成后，在终端运行 Python 进行测试：

```python
import epanet_turbo
print(f"Version: {epanet_turbo.__version__}")
# 应输出: Version: 2.8.0
```

### 4. Linux 部署特别说明

本项目已内置 `libepanet2.so` (Ubuntu 22.04 编译)。

- **通常情况**: `pip install .` 后会自动识别内置 `.so`，开箱即用。
- **特殊情况**: 如果您的 Linux 系统极老 (如 CentOS 7)，可能会提示 `GLIBC` 版本错误。此时您需要自行编译 OWA-EPANET 并替换 `epanet_turbo/dll/` 下的文件。

---

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

- **遥测 (Telemetry)**: 收集基础系统指纹以进行许可证验证与兼容性分析。
- **知识产权**: 核心算法模块采用 PyArmor 加密保护。
- **免责声明**: 本软件按"原样"提供，开发者不对使用后果承担法律责任。

---

### 🤝 致谢

- **Lee Yau-Wang 皝神**: 感谢大佬提供的核心思路与架构指导！Orz
- **OWA-EPANET 社区**: 感谢开源社区维护的 EPANET 2.3 基线。
- **WNTR 团队**: 感谢 WNTR 提供的优秀 Python 接口设计灵感。

<br>
<br>

`<a name="english"></a>`

---

# 🇺🇸 EPANET-Turbo v2.8 (English Version)

**EPANET-Turbo** is a high-performance hydraulic simulation engine tailored for **Ultra-Large Scale (100k-1M nodes)** water distribution networks. Built upon the **OWA-EPANET 2.3** kernel, it shatters performance bottlenecks through **OpenMP Parallelism**, **Polars Data Engine**, and **Batch APIs**.

v2.0 marks the completion of the **M6: Full Platform Native Support** milestone, officially unifying **Windows, macOS (Apple Silicon/Intel), and Linux**. From Mac Studio to cloud-based Linux clusters, developers now get a consistent, high-performance experience.

**v2.8 (M8)** introduces **Rust High-Performance Bindings**, providing thread-safe batch APIs and **zero-noise silent execution** mode.

### 🚀 Core Values

- **Speed**: **5-10x** faster simulation (OpenMP), **50-100x** faster pre/post-processing (Polars).
- **Scale**: Easily handles **500k+ node** models, keeping memory usage constant (150MB) via streaming.
- **Easy**: 100% compatible with standard INP files, intuitive Python API, drop-in replacement for WNTR.
- **Smart**: Automatically adapts to **ARM/Rosetta** (Mac Parallels); built-in **Self-Healing** mechanism automatically fixes dependency corruption.

---

## 🏆 Milestones & Evolution

| Milestone | Version | Key Achievement                                                                                                                                            | Status  |
| :-------- | :------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------- | :------ |
| **M1**    | v0.1.0  | **OpenMP Genesis**: Introduced multi-threaded parallelism to the OWA core `hydsolver` for the first time.                                                 | ✅ Done |
| **M2**    | v1.0.0  | **Polars Integration**: Completely rebuilt the Python layer with Rust/Polars for 10x faster INP parsing.                                                  | ✅ Done |
| **M3**    | v1.1.0  | **Streaming Sink**: Implemented Protocol V1 streaming IO to solve OOM issues during long-duration EPS runs.                                               | ✅ Done |
| **M4**    | v1.2.0  | **Open-Once**: Memory-resident handles eliminated 90% of initialization overhead for rolling predictions.                                                 | ✅ Done |
| **M5**    | v1.4.0  | **Unified Matrix**: Single CMake system generating both Serial and OpenMP binaries.                                                                       | ✅ Done |
| **M6**    | v2.0.0  | **Native Platforms**: Unification of Windows, macOS (Apple Silicon), and Linux.                                                                           | ✅ Done |
| **M6-2**  | v2.1.0  | **Rules Optimization** *(Windows)*: State-driven rule engine, 99.93% skip rate for 1000-rule models                                                       | ✅ Done |
| **M6-3**  | v2.2.0  | **Parallel Numerical Engine** *(Windows)*: Implemented OpenMP Headloss and Bucket-Lock Assembly. 2.6x speedup (16-core) with 100% bit-identical results.  | ✅ Done |
| **M7**    | v2.3.0  | **Convergence Optimization** *(Windows)*: Targeted Adaptive Relaxation. Solved long-tail oscillation, **2.8x** speedup for large models.                  | ✅ Done |
| **M8**    | v2.8.0  | **Rust Bindings + Silent Mode**: Thread-safe batch interfaces + zero-noise console output.                                                                | ✅ Done |

### 🔮 Future Blueprint

| Milestone | Target | Core Objective                                                                                                                                                        | Status     |
| :-------- | :----- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------- |
| **M9**    | v2.9.0 | **NMM/CHOLMOD Optimization**: Fix correctness bugs on ill-conditioned models + automatic fallback strategy.                                                          | 🏗️ In Dev |
| **M10**   | v3.0.0 | **GPU Empowerment (Outer-loop)**: Accelerating the "Outer-loop" (Calibration, Optimization) directly on GPUs. Transforming 10k serial runs into parallel tensor ops. | 📅 Future  |
| **M11**   | v4.0.0 | **AI Surrogate**: Built-in Graph Neural Network (GNN) calibration and hybrid "Prediction-Simulation" drivers.                                                        | 📅 Future  |

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

### 4. 🎯 v2.2: Parallel Numerical Engine *(Windows)*

Focused on parallelizing the most time-consuming calculation blocks for large-scale networks:

- **Parallel Headloss**: Distributes hydraulic property calculations for 100k+ links across multiple CPU cores.
- **Parallel Assembly (Bucket-Lock)**: Solves Aii/F matrix update contention using a fine-grained locking strategy.
- **Bit-identical**: Unlike chaotic reduction, this approach ensures identical results compared to serial runs, maintaining mathematical precision.

### 5. 🎯 v2.3 (M7): Targeted Adaptive Relaxation *(Windows)*

Addressed the "Long-tail Oscillation" issue common in large-scale models with coupled hydraulics:

- **Oscillation Detection**: Monitors error gradients in real-time. Triggers when iterations > 10 and error diverges.
- **Aggressive Damping**: Automatically applies `RelaxFactor = 0.5` to break numerical cycles instantly.
- **Result**: Reduced average iterations from 5.3 to 1.01 on difficult models, achieving a **2.8x** overall speedup.

### 6. 🎯 v2.8 (M8): Rust Bindings + Silent Mode

Introduced high-performance Rust bindings and zero-noise execution:

- **Thread-Safe**: Rust backend resolves multi-threaded GIL contention issues.
- **Batch APIs**: `get_all_pressures()`, `set_node_values()` minimize Python/C call overhead.
- **Silent Execution**: Eliminates "Page 1...", "Balanced after N trials..." console noise completely.
- **Verified Accuracy**: Max Pressure Error: 2.33e-08, Max Flow Error: 5.03e-06 (identical to standard EPANET)

> ⚠️ **Note**: Parallel numerical optimization features are currently **Windows x64 only**.

---

## 📊 Benchmarks

> Env: Intel i7-12700, 32GB RAM, Windows 11

| Metric                       | Original WNTR | EPANET-Turbo v2.8 | Speedup        |
| :--------------------------- | :------------ | :---------------- | :------------- |
| **Load INP (440k nodes)**    | 45.20 s       | **3.82 s**        | **11.8x** 🚀   |
| **Serial Solve (47k links)** | 44.02 s       | **42.10 s**       | **1.0x**       |
| **Parallel (16-core)**       | 44.02 s       | **16.65 s**       | **2.6x** 🚀    |
| **7-Day EPS Run**            | 352.00 s      | **42.50 s**       | **8.2x** 🚀    |
| **Peak Memory**              | OOM           | **152 MB**        | **Stable**     |

---

## 📂 Project Structure

| Path                  | Description                                                                               |
| :-------------------- | :---------------------------------------------------------------------------------------- |
| **`epanet_turbo/`**   | **Core Package** (Encrypted, Git Tracked)                                                 |
| ├──`dll/`             | **Kernels**: `epanet2.dll` (Win), `libepanet2.dylib` (Mac), `libepanet2.so` (Linux)       |
| ├──`engine.py`        | Driver: Handles DLL loading and CTypes mapping                                            |
| ├──`parser.py`        | **Polars Parser**: Ultra-fast INP reader                                                  |
| ├──`streaming.py`     | Streaming Output: Protocol V2 implementation                                              |
| **`resources/`**      | **Archives**: Legacy binaries & assets                                                    |
| **`include/`**        | **Headers**: Public C API definitions (`epanet2.h`)                                       |
| **`dev_tools/`**      | **Dev Toolkit**: Build scripts (`make_release.py`) & CI utils                             |
| `pyproject.toml`      | Config: Dependencies & Metadata                                                           |

---

## 🔁 Migration & Integration

### Q1: I use OWA-EPANET 2.3. How to migrate?

EPANET-Turbo is **100% compatible** with OWA-EPANET.

- **INP Files**: No changes needed.
- **API**: Standard functions (`ENopen`, `ENsolveH`) behave identically.
- **Performance**: To unlock 100x speedups, replace Python loops with Turbo's **Batch API** (`ENT_set_node_values`).

### Q2: I use WNTR. Is this a replacement?

**It is Complementary, not a Replacement.**

- **WNTR**: Best for Topology Analysis, Resilience, Fragility Curves.
- **Turbo**: Best for **Pure Computational Power**.

**Recommended Hybrid Workflow**:

1. Use **WNTR** to build/modify network structure.
2. Export temporary INP via `wn.write_inpfile()`.
3. Use **EPANET-Turbo** for massive simulations (Monte-Carlo, PDA).
4. Load binary results for analysis.

> 💡 See example: [demo_adapter.py](examples/demo_adapter.py) (WNTR Integration)

---

## 🔧 Deployment & Installation

EPANET-Turbo uses a **Binary Distribution** model. No C/C++ compiler is needed.

### 1. Requirements

- **OS**: Windows x64, Linux (glibc 2.29+), macOS (Apple Silicon/Intel)
- **Python**: 3.10, 3.11, 3.12 (Recommended: 3.12)
- **Dependencies**: `polars >= 0.20.0`, `numpy >= 1.20.0`

### 2. Installation steps

Go to [Github Releases](https://github.com/ericwanderlust/epanet-turbo/releases) and download the release ZIP.

**Recommended (One-click Installer)**:

```bash
python setup_and_demo.py
```

**Manual (Wheel)**:

```bash
pip install epanet_turbo-2.8.0-py3-none-any.whl
```

### 3. Verify Installation

```python
import epanet_turbo
print(f"Version: {epanet_turbo.__version__}")
# Windows: Should print Version: 2.8.0
# Linux: If "OSError: libepanet2.so not found", check LD_LIBRARY_PATH
```

### 4. Linux Note

Includes pre-compiled `libepanet2.so` (Ubuntu 22.04). Most modern distros work out-of-the-box. Legacy distros (CentOS 7) may require manual compilation of OWA-EPANET.

---

## 🛡️ Telemetry & License

- **Telemetry**: Collects basic system identifiers for license verification and compatibility analysis.
- **IP Protection**: Core modules are encrypted via PyArmor.
- **Disclaimer**: Provided "AS IS" without warranty.

---

### 🤝 Acknowledgments

- **Lee Yau-Wang 皝神**: Special thanks for the core architecture and mentorship! Orz
- **OWA-EPANET Community**: For maintaining the robust EPANET 2.3 baseline.
- **WNTR Team**: For the inspiration on Pythonic hydraulic interfaces.

<div align="center">

**Made with 🏎️ by ES (Serein) · @Serein93**

</div>
