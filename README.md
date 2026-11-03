<div align="center">

# 🏎️ EPANET-Turbo v2.8.1-preview.3

### 让水力模拟跑得更快 | Faster hydraulic simulation

[![Version](https://img.shields.io/badge/version-v2.8.1--preview.3-blue)](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.3)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64%20%7C%20Linux%20x64%20%7C%20macOS%20arm64-blueviolet)](#builds)
[![WNTR](https://img.shields.io/badge/WNTR-1.4.0-green)](https://github.com/USEPA/WNTR)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

[🇨🇳 中文](#chinese) | [🇬🇧 English](#english) | [📦 Download](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.3)

</div>

---

<a id="chinese"></a>

## 🇨🇳 中文

**EPANET-Turbo** 面向供水管网水力模拟，提供 EPANET 原生内核优化和 WNTR 结果读取加速。拿你熟悉的 WNTR 工作流，看看同一份模型能跑多快。🚀

**v2.8.1-preview.3** 是技术预览版：分平台提供 EPANET 2.2 兼容内核、2.3.3 内核和可选的 WNTR 1.4.0 快速读取器。

> ⚠️ **旧版 2.3 接口修复**：v2.8.0、v2.8.1-preview.1 和 preview.2 的 `ENT_set_demand_multiplier` 会错误修改相对黏度，而不是需水倍率，并可能返回成功。**preview.3 已修正**。如果用旧接口计算过工况，请重新验证；旧版可调用标准接口 `EN_setoption(project, EN_DEMANDMULT, factor)`。2.2 兼容包不导出该接口。

### ⚡ WNTR 跑得怎么样？

在一份 **46,834 节点 / 48,245 连接、24 小时 / 49 个报告时刻**的济南诊断子网上，Apple M4、macOS arm64、WNTR 1.4.0、Python 3.12、NumPy 2.4.6：

| 配置 | 完整 `run_sim` 中位数 | 相对 WNTR 默认 |
| --- | ---: | ---: |
| WNTR 自带 EPANET 2.2 + 默认读取器 | 1.846 s | 基准 |
| WNTR 自带 EPANET 2.2 + 快速读取器 | 1.054 s | ⬇️ 约 43% |
| Turbo 2.2 兼容内核，4 线程 + 默认读取器 | 1.633 s | ⬇️ 约 12% |
| **Turbo 2.2 兼容内核，4 线程 + 快速读取器** | **1.015 s** | **⬇️ 约 45%** |

每组预热一次，随后轮转交错测量 5 次。计时包含 WNTR 写 INP、原生水力和水质调用、读取完整结果；模型对象只在开始时加载一次，**不包含首次模型加载和 Python 导入**。该模型的水质类型为 `NONE`；本次首次模型加载单次为 0.854 s，单独记录。四组的全部节点和管段结果表、索引和数据类型逐值一致。

🔍 **优化在哪里？**

- 📥 **快速读取**：批量读取标识符、直接构建结果表，避免创建大型临时 MultiIndex。本次默认内核的结果读取中位数从 **0.740 s 降到 0.103 s**。
- ⚙️ **管道系数并行**：网络至少有 10,000 条连接、线程数大于 1 时使用 OpenMP。它对这份模型有帮助，但收益因模型和机器而异。
- 🧩 **2.2 兼容**：为现有 EPANET 2.2 / WNTR 用户单独提供标准 2.2 Toolkit；它不包含 2.3 的 Turbo 专有 bulk API。

主要收益来自**结果读取**，不能全部归因于原生求解器。以上数据只代表这台机器和这份模型，不代表 Windows、Linux 实机或其他网络的加速比。

<a id="builds"></a>

### 📦 选择你的版本 | Choose your build

每个 ZIP 只对应**一种平台、架构和内核**。先选与你现有项目匹配的内核，再选系统：

| 平台 / Platform | EPANET 2.2 兼容 / Compatible | EPANET 2.3.3 | 引擎 / Library |
| --- | --- | --- | --- |
| 🪟 **Windows x64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet22-compat-windows-x64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet23-windows-x64.zip) | `epanet2.dll` |
| 🐧 **Linux x64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet22-compat-linux-x64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet23-linux-x64.zip) | `libepanet2.so` |
| 🍎 **macOS arm64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet22-compat-macos-arm64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.3/epanet-turbo-v2.8.1-preview.3-epanet23-macos-arm64.zip) | `libepanet2.dylib` |

2.2 兼容内核的 `EN_getversion` 返回 `20200`，2.3.3 内核返回 `20303`。`x64` 也叫 `x86_64`；`arm64` 对应 Apple Silicon。没有 Windows ARM64、Linux ARM64 或 Intel Mac 构建。解压后请把引擎与随包的 OpenMP 运行库放在同一目录；ZIP **不是 Python wheel**。

🧪 **验证环境**：macOS 27.0.1 原生运行；Linux x64 在 OrbStack 仿真 Debian 12 / glibc 2.36 上测试；Windows x64 在 OrbStack 的 Wine 中仿真测试。Windows 实机、Linux x64 服务器性能尚未验证。macOS 运行库标注最低版本为 14.0，但尚未在 14.0 实机验证。

### 🐍 和 WNTR 一起用

安装 **WNTR 1.4.0**，将 [turbo_adapter.py](examples/turbo_adapter.py) 和 [fast_wntr_reader.py](examples/fast_wntr_reader.py) 放到项目可导入的位置，然后选择与系统匹配的 **2.2 兼容**库：

```python
import os

# 在线程运行库加载前设置；按机器和模型调整。
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OMP_DYNAMIC", "FALSE")

import wntr
from turbo_adapter import TurboSimulator
from fast_wntr_reader import FastBinFile

network = wntr.network.WaterNetworkModel("network.inp")
simulator = TurboSimulator(network, "/absolute/path/to/libepanet2.so")
simulator.reader = FastBinFile()  # 可选：加速结果读取
results = simulator.run_sim(file_prefix="output/run", version=2.2)

pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

先创建 `output/`；Windows 使用 `.dll`，macOS 使用 `.dylib`。不设置 `simulator.reader` 就使用 WNTR 默认读取器。`FastBinFile` 也可单独用于 WNTR 自带内核：

```python
simulator = wntr.sim.EpanetSimulator(network, reader=FastBinFile())
```

快速读取器目前只验证并接受 **WNTR 1.4.0**。`TurboSimulator` 临时切换进程内的 WNTR Toolkit 类，因此不要与同一进程中的其他 WNTR 仿真并发运行。

### 🧪 自己复测

```bash
python examples/verify_fast_reader.py
python examples/benchmark_wntr.py --inp network.inp --library /absolute/path/to/libepanet2.so --runs 5 --output benchmark.json
```

第一个命令用 Net1/2/3 对照读取结果；第二个命令先比较四组结果，再记录完整 `run_sim` 和各阶段耗时。使用 `--work-dir` 可以指定临时 INP、报告和输出文件的位置。请用自己的模型、机器和实际线程数验收。

### 🛠️ 兼容性与已知边界

- ✅ **2.2 兼容内核**：macOS 和仿真 Linux 的 WNTR 1.4.0 对照中，济南子网 49 个时刻的压力、水头、需水、流量和状态一致；Net2 也核对了节点与管段水质。快速读取器的 Net1/2/3 用例覆盖水龄、化学、溯源、统计和单位转换。
- ⚠️ **统计输出**：本机所测 NumPy 2.4.6 环境中，WNTR 1.4.0 的 `AVERAGED` 统计用例在默认读取器和快速读取器均抛出相同异常。
- 🔧 **2.3 收敛修复**：已修正零设定 TCV 的系数遗漏；三节点回归用例在 macOS、仿真 Linux 和 Wine Windows x64 完成。**这不表示所有 2.3 收敛问题都已解决。**2.3 与 2.2 的直接 Toolkit 阀门状态编码和数值也可能不同。
- 🧮 **CHOLMOD / M9**：当前发行包使用内置线性求解器，关闭 CHOLMOD、外部求解器接管和 M9 融合组装。健康合成网格测试中，CHOLMOD 在约 2 万到 5 万节点间出现候选性能交叉，但结构和初始化耗时影响很大，**不是生产启用阈值**。负压、低于 15 m、警告、非有限值或短 EPS 的模型不能让 CHOLMOD 接管。
- 📂 **源码状态**：公开仓库目前不含与这些原生二进制完全对应的 C 构建源码；Release 标签对应文档和 WNTR 适配代码。各 ZIP 包含运行库许可证及第三方源码来源。

---

<a id="english"></a>

## 🇬🇧 English

**EPANET-Turbo** explores native EPANET optimizations and faster WNTR result loading for water-network simulation. Keep your familiar WNTR workflow and measure the difference on your own models. 🚀

**v2.8.1-preview.3** is a technical preview with separate EPANET 2.2-compatible and 2.3.3-based native engines, plus an optional fast reader for WNTR 1.4.0.

> ⚠️ **Fix for earlier 2.3 releases:** in v2.8.0, v2.8.1-preview.1 and preview.2, `ENT_set_demand_multiplier` changes relative viscosity instead of the demand multiplier and can return success. **This is fixed in preview.3.** Revalidate scenarios that used the affected function; on an earlier build, use the standard `EN_setoption(project, EN_DEMANDMULT, factor)`. The 2.2-compatible build does not export this function.

### ⚡ WNTR benchmark

One Jinan diagnostic network with **46,834 nodes / 48,245 links**, a 24-hour simulation and 49 reporting times, on Apple M4 / macOS arm64 / WNTR 1.4.0 / Python 3.12 / NumPy 2.4.6:

| Configuration | Median full `run_sim` | vs. default WNTR |
| --- | ---: | ---: |
| WNTR EPANET 2.2 + default reader | 1.846 s | Baseline |
| WNTR EPANET 2.2 + fast reader | 1.054 s | ⬇️ about 43% |
| Turbo 2.2-compatible engine, 4 threads + default reader | 1.633 s | ⬇️ about 12% |
| **Turbo 2.2-compatible engine, 4 threads + fast reader** | **1.015 s** | **⬇️ about 45%** |

Each configuration was warmed once and measured in five rotated rounds. Timing includes WNTR INP writing, native hydraulic and quality calls, and reading all results. The model object was loaded once before timing; **initial model loading and Python import are excluded**. This model uses quality type `NONE`; the initial model load was measured once at 0.854 s and recorded separately. All node and link result tables, indices and data types matched exactly across the four configurations.

🔍 **Where does the improvement come from?**

- 📥 **Faster output reading:** IDs are read in batches and result tables are built directly, avoiding a large temporary MultiIndex. With the default engine, median result-reading time fell from **0.740 s to 0.103 s** in this test.
- ⚙️ **Parallel pipe coefficients:** OpenMP is used when the network has at least 10,000 links and more than one thread is requested. Results depend on the network and machine.
- 🧩 **2.2 compatibility:** the separate engine exposes the standard 2.2 Toolkit for existing EPANET 2.2 / WNTR projects; it does not include the Turbo-specific 2.3 bulk API.

Most of this measured gain comes from **result reading**, not the native solver alone. These numbers describe one model on one machine, not a general Windows, Linux or cross-model speed claim.

### 📦 Downloads and architectures

Choose one OS, CPU architecture and engine from the [download table above](#builds): **Windows x64**, **Linux x64**, or **macOS arm64**. The 2.2-compatible core reports `20200` from `EN_getversion`; the 2.3.3 core reports `20303`. `x64` means `x86_64`; macOS arm64 is Apple Silicon. No Windows ARM64, Linux ARM64 or Intel Mac build is provided. Keep each engine beside the bundled OpenMP runtime. These archives are **not Python wheels**.

🧪 **Tested environments:** native macOS 27.0.1; Linux x64 on emulated Debian 12 / glibc 2.36 in OrbStack; Windows x64 through Wine in OrbStack. Real Windows and native Linux x64 server performance have not yet been tested. The bundled macOS runtime declares a minimum of macOS 14.0; that OS version has not been tested on a real machine.

### 🐍 Use with WNTR

Install **WNTR 1.4.0**, place [turbo_adapter.py](examples/turbo_adapter.py) and [fast_wntr_reader.py](examples/fast_wntr_reader.py) on your Python import path, and select the **2.2-compatible** library for your platform:

```python
import os

# Set before the OpenMP runtime is loaded; tune for your machine and model.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OMP_DYNAMIC", "FALSE")

import wntr
from turbo_adapter import TurboSimulator
from fast_wntr_reader import FastBinFile

network = wntr.network.WaterNetworkModel("network.inp")
simulator = TurboSimulator(network, "/absolute/path/to/libepanet2.so")
simulator.reader = FastBinFile()  # Optional: faster output reading
results = simulator.run_sim(file_prefix="output/run", version=2.2)

pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

Create `output/` first; use the `.dll` on Windows and `.dylib` on macOS. Omit the reader assignment to use WNTR's default reader. The fast reader can also be used with WNTR's own engine:

```python
simulator = wntr.sim.EpanetSimulator(network, reader=FastBinFile())
```

The fast reader is currently validated for, and accepts, **WNTR 1.4.0** only. `TurboSimulator` temporarily switches the process-wide WNTR Toolkit class, so do not run other WNTR simulations concurrently in the same process.

### 🧪 Reproduce and test

```bash
python examples/verify_fast_reader.py
python examples/benchmark_wntr.py --inp network.inp --library /absolute/path/to/libepanet2.so --runs 5 --output benchmark.json
```

The first command compares reader outputs on Net1/2/3. The second compares results across all four configurations before timing full `run_sim` and its stages. Set `--work-dir` to choose where temporary INP, report and output files are written. Validate using your own models, hardware and thread count.

### 🛠️ Compatibility and known boundaries

- ✅ **2.2-compatible engine:** WNTR 1.4.0 comparisons on macOS and emulated Linux matched pressure, head, demand, flow and status for all 49 reporting times of the Jinan diagnostic subnetwork; Net2 node and link quality were also checked. Fast-reader cases on Net1/2/3 cover water age, chemical quality, tracing, statistics and unit conversion.
- ⚠️ **Statistics:** in the tested NumPy 2.4.6 environment, the WNTR 1.4.0 `AVERAGED` statistics case raises the same exception with both the default and fast readers.
- 🔧 **2.3 convergence fix:** the missing coefficient for a zero-setting TCV is fixed; the three-node regression ran on macOS, emulated Linux and Wine Windows x64. **This does not mean that every 2.3 convergence problem is solved.** Direct Toolkit valve status codes and results can also differ between 2.2 and 2.3.
- 🧮 **CHOLMOD / M9:** the current packages use the built-in linear solver; CHOLMOD, external solver takeover and M9 fused assembly are disabled. Healthy synthetic grids showed a candidate performance crossover between about 20,000 and 50,000 nodes, but topology and initialization matter; **this is not a production threshold**. Models with negative pressure, pressure below 15 m, warnings, non-finite values or short EPS must not use CHOLMOD takeover.
- 📂 **Source availability:** the public repository does not yet contain the exact C source used for these native binaries. The Release tag points to documentation and WNTR adapter code. Each ZIP includes runtime licenses and third-party source references.

---

<div align="center">

🏎️ **Measure it. Check the results. Then make it faster.**

[📦 Releases](https://github.com/ericwanderlust/epanet-turbo/releases) · [📄 License](LICENSE)

</div>
