# 📘 EPANET-Turbo v2.3.0 Developer Manual / 开发者手册

> **High-Performance Water Distribution Network Simulation Engine**
> **高性能供水管网模拟引擎**

---

## ⚡ 1. Why EPANET-Turbo? (核心价值)

Standard EPANET/WNTR workflows suffer from **Single-Threaded Bottlenecks** and **IO Inefficiencies**. EPANET-Turbo solves this.
标准的 EPANET/WNTR 工作流受限于**单线程瓶颈**和**IO 低效**。EPANET-Turbo 彻底解决了这些问题。

### 🚀 Performance Benchmarks (性能指标)

| Metric (指标)          | Standard WNTR / EPANET | **EPANET-Turbo 2.3**  | Improvement (提升)        |
| :--------------------- | :--------------------- | :-------------------------- | :------------------------ |
| **Parsing (IO)** | 45s (Large Network)    | **< 0.8s**            | **50x Faster**      |
| **Simulation**   | Serial (1 Core)        | **Parallel (OpenMP)** | **5x - 10x Faster** | (Windows/Mac/Linux) |
| **Connectivity** | 403s (400k Nodes)      | **Targeted Relaxation** | **142s (2.8x Faster)** | (Windows M7 Optimized) |
| **Data Access**  | Slow Python Objects    | **Zero-Copy Polars**  | **100x Faster**     |

### 💡 Technology Stack (技术原理)

1. **Parallel Computing (并行计算)**:

   * **EN**: Replaced the core hydraulic solver with an **OpenMP-accelerated** kernel. It utilizes all CPU cores for matrix solving.
   * **CN**: 将核心水力求解器替换为 **OpenMP 加速**内核。充分利用 CPU 多核进行矩阵运算。
2. **Polars Data Engine (Polars 数据引擎)**:

   * **EN**: Instead of heavy Pandas objects, we use **Rust-based Polars**. It maps the INP file directly into memory (`mmap`) for instant access without parsing overhead.
   * **CN**: 我们放弃了沉重的 Pandas 对象，转而使用基于 Rust 的 **Polars**。它将 INP 文件直接映射到内存 (`mmap`)，实现零开销即时访问。
3. **Adaptive Relaxation (自适应松弛)** (New in v2.3):

   * **EN**: Smart logic detects oscillation in hydraulic iterations and applies targeted damping. Solves "Long Tail" convergence issues instantly.
   * **CN**: 智能逻辑自动检测水力迭代中的震荡，并应用目标阻尼。瞬间解决“长尾”收敛问题。
4. **Zero-Copy Bridge (零拷贝桥接)**:

   * **EN**: Simulation results are written directly to binary buffers readable by Python, eliminating the expensive "C++ -> Python Object" conversion cost.
   * **CN**: 模拟结果直接写入 Python 可读的二进制缓冲区，消除了昂贵的“C++ 到 Python 对象”的转换开销。

---

## 🏗️ 2. Architecture (架构设计)

We adhere to the **"Three-Layer Architecture"** to balance performance and usability.
我们遵循**“三层架构”**设计，以平衡性能与易用性。

* **Layer 1 (Core)**: C/C++ Engine with OpenMP optimizations (`epanet2_openmp.dll`, `libepanet2.dylib`, `libepanet2.so`).
  * *Role*: Heavy lifting, matrix inversion. Optimized for each platform.
* **Layer 2 (Bridge)**: `engine.py` using CTypes.
  * *Role*: Automated loading and cross-platform binary detection.
* **Layer 3 (API)**: `parser.py` using Polars.
  * *Role*: Provides a user-friendly DataFrame interface (Zero-copy).

---

## 📚 3. Detailed API Reference (详细接口文档)

### 3.0 🚀 Quick Summary / 快速概览

| Function/Class                           | Description (CN)                                              | Description (EN)                                                     |
| :--------------------------------------- | :------------------------------------------------------------ | :------------------------------------------------------------------- |
| **`InpParser(filepath)`**        | **核心类**。读取 INP 文件，提供高性能解析和模拟接口。   | **Core Class**. Reads INP file, provides parsing & simulation. |
| **`simulate(filepath)`**         | **快捷函数**。直接运行模拟并返回结果 (不保留中间对象)。 | **Helper**. Runs sim directly & returns results.               |
| **`InpParser.run_simulation()`** | **全功能模拟**。支持内存常驻、修改参数后重算。          | **Full Simulation**. Supports resident memory & re-runs.       |

### 3.1 Core Class: `InpParser`

This is the main entry point. / 这是主要的入口类。

#### Initialization (初始化)

```python
from epanet_turbo import InpParser

# EN: Loads INP file instantly
# CN: 瞬间加载 INP 文件
model = InpParser("Net1.inp", verbose=True)
```

#### Topological Data (拓扑数据)

Access network elements as high-performance Polars DataFrames.
以高性能 Polars DataFrame 形式访问管网元素。

```python
# 1. Junctions (Nodes) / 节点表
# Columns: id, elevation, demand
df_nodes = model.junctions
print(df_nodes.head())

# 2. Pipes (Links) / 管段表
# Columns: id, node1, node2, length, diameter
df_pipes = model.pipes

# 3. Other Elements / 其他元素
# valves, pumps, tanks, reservoirs
df_valves = model.valves
```

#### Simulation (模拟)

```python
# EN: Run full simulation
# CN: 运行完整模拟
# Returns: dict of Polars DataFrames (e.g. results['pressure'], results['flow'])
results = model.run_simulation()

# EN: Save binary result to disk (optional)
# CN: 保存二进制结果到磁盘 (可选)
model.run_simulation(output_filename="output.bin")
```

### 3.2 WNTR Adapter (WNTR 加速器)

Designed for users who already have WNTR code but want speed.
专为已有 WNTR 代码但需要提速的用户设计。

```python
from wntr.network.WaterNetworkModel import WaterNetworkModel
from epanet_turbo.examples.turbo_adapter import TurboSimulator

# 1. Load Model (Standard WNTR)
wn = WaterNetworkModel("Net1.inp")

# 2. Simulate using Turbo (Magic Step) 🪄
# EN: Replaces wntr.sim.EpanetSimulator
# CN: 替换 wntr.sim.EpanetSimulator，无需修改其他代码
sim = TurboSimulator(wn) 
results = sim.run_sim()

# 3. Use Results
print(results.node['pressure'])
```

---

## 📋 4. Installation & Setup (安装部署)

### Method A: Automated Script (Recommended / 推荐)

**EN**: Provides **Self-Healing** capabilities for missing Windows Runtimes.
**CN**: 提供针对缺失 Windows 运行库的**自我修复**功能。

1. Place `setup_and_demo.py` next to the `.whl` file (in `dist/`).

   * 将 `setup_and_demo.py` 放在 `.whl` 文件旁边。
2. Run / 运行:

   ```bash
   python setup_and_demo.py
   ```

### Method B: Manual Install (手动安装)

For CI/CD pipelines or advanced users.
适用于流水线或高级用户。

```bash
# 1. Install Dependencies (Include numpy for DLLs)
pip install "polars>=0.20.0" "numpy>=1.24.0" requests

# 2. Install Wheel
pip install dist/epanet_turbo-2.0.0-py3-none-any.whl
```

### 🧱 Prerequisites (环境要求)

* **Windows**: 10/11 x64 + Microsoft Visual C++ Redistributable.
* **macOS**: 12+ (Monterey) on Apple Silicon (ARM64) or Intel (x64).
* **Linux**: x86_64 with GLIBC >= 2.31 (e.g. Ubuntu 20.04+, Debian 11+).
* **Python**: 3.10, 3.11, or 3.12 (64-bit).

---

---

## 🦾 5. Special Case: Reinforcement Learning (RL) Integration

## 🦾 5. 强化学习 (RL) 集成专项指南

When integrating EPANET-Turbo into an RL environment (e.g., Gym/PettingZoo), keep these lessons from "Battle-Hardened" production in mind:
在将 EPANET-Turbo 集成到 RL 环境（如 Gym）时，请务必关注以下来自实际生产环境的经验：

### 5.1 Indexing Differences (索引差异)

* **Problem**: WNTR usually returns an integer-indexed DataFrame, but Turbo returns a **`TimedeltaIndex`**.
* **Fix**: Use position-based indexing (`.iloc[0]`) instead of label-based (`.loc[0]`) to extract specific time steps.
* **CN**: WNTR 默认返回整数索引，而 Turbo 返回 **`TimedeltaIndex`**。请统一使用 `.iloc` 进行位置索引以保证兼容性。

### 5.2 Numerical Stability (数值稳定性)

* **NaN Handling**: Agent exploration might cause extreme pump speeds leading to negative pressures or hydraulic failures (NaN). Use `np.nan_to_num()` before feeding results to the Neural Network.
* **Reward Clamping**: Always clamp your rewards (e.g., `-100` to `+50`) to prevent gradient explosions caused by failed simulations.
* **CN**: 强化学习初期的随机探索可能导致极端的泵速动作，引发负压或仿真失败 (NaN)。在将结果输入神经网络前，务必进行 `NaN` 清洗及奖励值截断 (Clamping)。

### 5.3 Hybrid Drive Mode (混合驱动模式)

* **Design**: Use **WNTR** as the "Model Manager" (to modify pumps/demands and export `.inp`) and **EPANET-Turbo** as the "Execution Engine" (to run bits as fast as possible).
* **CN**: 推荐使用 **WNTR** 作为“模型管理器”（负责拓扑操作、导出 `.inp`），使用 **EPANET-Turbo** 作为“高速执行引擎”。

---

## 🛠️ 6. Troubleshooting (疑难解答)

### Q: How do I see available functions? (如何查看可用函数？)

* **EN**: Since Version 2.0.0, use the built-in `about()` function to inspect the API.
* **CN**: v2.0.0 起，可直接调用 `about()` 函数查看 API 参考信息。

```python
import epanet_turbo as et
et.about()
```

### Q: `ImportError: DLL load failed`?

* **Cause**: Missing VC++ Runtime (C++ standard libraries).
* **Solution**: Use Method A (Script). It borrows the runtime from NumPy. Or install [VC_Redist.x64](https://aka.ms/vs/17/release/vc_redist.x64.exe).

### Q: Why is my `__version__` check failing?

* **Cause**: You might be importing the local folder instead of the installed package.
* **Solution**: Change directory (`cd ..`) out of the source folder before running python.

---

*EPANET-Turbo v2.0.0* | *Powering the Future of Hydraulic Modeling*
