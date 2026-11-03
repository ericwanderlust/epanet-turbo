<div align="center">

# 🏎️ EPANET-Turbo v2.8.1-preview.6

### 让水力模拟跑得更快 | Faster hydraulic simulation

[![Version](https://img.shields.io/badge/version-v2.8.1--preview.6-blue)](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.6)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64%20%7C%20Linux%20x64%20%7C%20macOS%20arm64-blueviolet)](#builds)
[![WNTR](https://img.shields.io/badge/WNTR-1.4.0-green)](https://github.com/USEPA/WNTR)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

[🇨🇳 中文](#chinese) | [🇬🇧 English](#english) | [📦 Download](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.6)

</div>

---

<a id="chinese"></a>

## 🇨🇳 中文

**EPANET-Turbo** 面向供水管网水力模拟，提供 EPANET 原生内核优化和 WNTR 结果读取加速。拿你熟悉的 WNTR 工作流，看看同一份模型能跑多快。🚀

**v2.8.1-preview.6** 是技术预览版：分平台提供 EPANET 2.2 兼容内核、2.3.3 内核和可选的 PyArmor 保护 WNTR 1.4.0 快速读取器，以及 2.2 / 2.3 自动识别的批量接口。

> ⚠️ **旧版 2.3 接口修复**：v2.8.0、v2.8.1-preview.1 和 preview.2 的 `ENT_set_demand_multiplier` 会错误修改相对黏度，而不是需水倍率，并可能返回成功。**preview.3 起已修正**。如果用旧接口计算过工况，请重新验证；旧版可调用标准接口 `EN_setoption(project, EN_DEMANDMULT, factor)`。新的 `BulkAPI` 对所有内核都使用标准接口，避开这个旧版问题。

> 📦 **历史分发说明**：preview.3 的 WNTR 示例脚本是明文；preview.4 的 2.2 ZIP 改为 PyArmor 保护。已公开的旧副本不受新打包影响。

### ⚡ WNTR 跑得怎么样？

在一份 **46,834 节点 / 48,245 连接、24 小时 / 49 个报告时刻**的济南诊断子网上，Apple M4、macOS arm64、WNTR 1.4.0、Python 3.12、NumPy 2.4.6。该子网从原模型按原有关闭边界提取；所测时刻没有负压，最低压力约 1.89 m，但仍有低于 15 m 的节点时刻：

| 配置 | 完整 `run_sim` 中位数 | 相对 WNTR 默认 |
| --- | ---: | ---: |
| WNTR 自带 EPANET 2.2 + 默认读取器 | 1.896 s | 基准 |
| WNTR 自带 EPANET 2.2 + 快速读取器 | 1.199 s | ⬇️ 约 37% |
| Turbo 2.2 兼容内核，4 线程 + 默认读取器 | 2.066 s | ⬆️ 约 9% |
| **Turbo 2.2 兼容内核，4 线程 + 快速读取器** | **1.230 s** | **⬇️ 约 35%** |

使用本次 PyArmor 加密分发脚本，每组预热一次，随后轮转交错测量 5 次。计时包含 WNTR 写 INP、原生水力和水质调用、读取完整结果；模型对象只在开始时加载一次，**不包含首次模型加载和 Python 导入**。该模型的水质类型为 `NONE`；首次模型加载单次为 1.306 s，单独记录。同一内核下，默认与快速读取器的全部结果表逐值一致；两种内核的压力、水头、需水、流量和状态一致，水头损失与摩阻系数因精度修复而不同。

🔍 **优化在哪里？**

- 📥 **快速读取**：批量读取标识符、直接构建结果表，避免创建大型临时 MultiIndex。本次默认内核的结果读取中位数从 **0.908 s 降到 0.122 s**，约快 7.5 倍。
- ⚙️ **管道系数并行**：网络至少有 10,000 条连接、线程数大于 1 时使用 OpenMP。实际收益因模型和机器而异，本次济南测试未显示单独更换内核的端到端收益。
- 🧩 **2.2 兼容**：为现有 EPANET 2.2 / WNTR 用户提供 2.2 Toolkit 和原生批量读写；同一 Python 接口也可用于 2.3。

主要收益来自**结果读取**，不能全部归因于原生求解器。本轮仅换读取器为 1.199 s、两项组合为 1.230 s，不能据此认定内核带来了额外端到端收益。以上数据只代表这台机器和这份模型，不代表 Windows、Linux 实机或其他网络的加速比。

### 🧰 2.2 / 2.3 批量接口：一次处理整网

需要反复校核、批量修改节点需水或管段粗糙系数？两个版本的 Turbo 内核都提供 `ENT_set_node_values` / `ENT_set_link_values` 批量设置，以及 `EN_get_all_pressures` / `EN_get_all_flows` 批量读取。它们把 Python 与原生库的逐项调用合并为数组调用；一个打开的模型也可以连续运行多个需水倍率工况。

同一济南子网的 **Turbo 2.2**，与同一内核的 WNTR Toolkit 式逐项调用比较，预热后交错测量 5 次，取中位数：

| 操作 | 逐项调用 | 原生批量调用 | 接口阶段倍数 |
| --- | ---: | ---: | ---: |
| 读取 46,834 个节点压力 | 12.532 ms | 0.147 ms | 约 85× |
| 读取 48,245 个连接流量 | 12.632 ms | 0.091 ms | 约 139× |
| 设置 46,828 个节点基本需水 | 14.639 ms | 1.380 ms | 约 10.6× |

读取逐值一致，设置含列表转 NumPy 的时间；26,323 个值实际发生变化，读回和还原通过。原生批量数组提前准备时设置为 0.139 ms。该测试直接测原生批量接口，不包含 `BulkAPI` 的输入校验、模型打开或求解。

在同一济南子网、Apple M4 / macOS arm64 / WNTR 1.4.0 / Turbo 2.3.3 下，比较同一个 2.3 内核上的 WNTR Toolkit 式逐点调用与 Turbo 批量调用，读取先预热，各项交错测量 5 次，取单次接口阶段中位数：

| 操作 | 逐点调用 | 批量调用 | 接口阶段倍数 |
| --- | ---: | ---: | ---: |
| 读取 46,834 个节点压力 | 12.34 ms | 0.110 ms | 约 112× |
| 读取 48,245 个连接流量 | 12.86 ms | 0.095 ms | 约 136× |
| 设置 46,828 个节点基本需水 | 14.43 ms | 1.33 ms | 约 10.8× |

读取结果逐值一致；设置包含从 Python 列表转换成 NumPy 数组的时间，26,323 项实际发生变化，读回和还原通过。若索引与数值数组提前准备并复用，本次设置接口中位数为 0.109 ms。**以上不包含打开模型或水力求解，不能当作完整仿真的加速倍数**，也不意味着 WNTR 正式支持直接替换成 2.3 内核。[EPANET 2.3 本身也提供全网批量读取](https://github.com/OpenWaterAnalytics/EPANET/blob/v2.3.3/include/epanet2_2.h)；这里比较的是 WNTR 式逐点调用，不是与 2.3 原生批量读取比较。

同一模型的 0.9 / 1.0 / 1.1 / 0.9 四次完整水力时序，复用 2.3 内核打开的模型为 1.487 s、每次重新打开为 1.682 s，约 1.13×；这是单轮结果，统计模型打开、求解与压力摘要，不包含其他业务 I/O，四组冷热压力摘要一致。

🔍 **自动识别怎么用？** 下载对应平台的 2.2 或 2.3 包，将匹配 Python 版本的 `python/cp311` 或 `python/cp312` 加入 `PYTHONPATH`。对已经打开模型的 WNTR Toolkit 对象：

```python
from turbo_bulk import BulkAPI

bulk = BulkAPI.from_wntr(toolkit)  # toolkit 已 ENopen；按需先运行 ENopenH / ENinitH / ENrunH
print(bulk.version, bulk.capabilities)
pressure = bulk.node_values()      # 已运行水力步；默认 EN_PRESSURE
flow = bulk.link_values()          # 已运行水力步；默认 EN_FLOW
bulk.set_node_values(1, [2, 3], [12.0, 9.0])  # EN_BASEDEMAND，索引从 1 开始
bulk.set_demand_multiplier(0.9)    # 标准 EN_DEMANDMULT
```

`BulkAPI(library, project)` 也可附着到已打开的原生项目。它读取实际库版本并逐项探测能力：Turbo 2.2 / 2.3 优先调用原生批量；没有 Turbo 符号时使用 EPANET 2.3 原生批量读取或逐项回退。检查 `capabilities` 即可确认路径；逐项回退保证兼容，但没有原生批量加速。识别对象是**实际载入的库，不是 INP 文件**；请仍按已有项目选择 2.2 或 2.3。普通 WNTR `run_sim` 不会自动变成批量工作流。

[完整批量与多工况示例](examples/bulk_auto_demo.py) 自动选择当前平台库，适用于两个包：

```bash
python examples/bulk_auto_demo.py --bundle /path/to/unpacked --inp examples/Net2.inp --node 2 --node 3 --pipe 1 --node-factor 1.01 --pipe-factor 1.01 --factors 0.9 1.0 1.1 0.9
```

示例只修改内存中的项目，不写回原始 INP。Toolkit 结果使用模型原生单位，WNTR 结果使用 SI 单位。批量写入在首个错误处停止，此前成功的值可能已写入，请按业务需要检查或还原。

<a id="builds"></a>

### 📦 选择你的版本 | Choose your build

每个 ZIP 只对应**一种平台、架构和内核**。先选与你现有项目匹配的内核，再选系统：

| 平台 / Platform | EPANET 2.2 兼容 / Compatible | EPANET 2.3.3 | 引擎 / Library |
| --- | --- | --- | --- |
| 🪟 **Windows x64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet22-compat-encrypted-windows-x64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet23-windows-x64.zip) | `epanet2.dll` |
| 🐧 **Linux x64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet22-compat-encrypted-linux-x64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet23-linux-x64.zip) | `libepanet2.so` |
| 🍎 **macOS arm64** | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet22-compat-encrypted-macos-arm64.zip) | [📥 Download](https://github.com/ericwanderlust/epanet-turbo/releases/download/v2.8.1-preview.6/epanet-turbo-v2.8.1-preview.6-epanet23-macos-arm64.zip) | `libepanet2.dylib` |

2.2 兼容内核的 `EN_getversion` 返回 `20200`，2.3.3 内核返回 `20303`。`x64` 也叫 `x86_64`；`arm64` 对应 Apple Silicon。没有 Windows ARM64、Linux ARM64 或 Intel Mac 构建。解压后请把引擎与随包的 OpenMP 运行库放在同一目录；ZIP **不是 Python wheel**。两个 ZIP 的引擎都位于 `native/<platform>/`；2.3 包还保留根目录原生库以兼容旧调用。两种包都提供 PyArmor 保护的批量辅助接口；2.2 包还提供加密的 WNTR 适配器、快速读取器和基准脚本。Python 脚本提供 CPython 3.11 / 3.12 子目录和匹配运行时。

🧪 **验证环境**：macOS 27.0.1 原生运行；Linux x64 在 OrbStack 仿真 Debian 12 / 13 上测试；Windows x64 在 GitHub 托管的原生 Windows Server 2022 虚拟机上运行 WNTR 1.4.0 与 CPython 3.11 / 3.12。实体 Windows 电脑、原生 Linux x64 服务器性能尚未验证。macOS 运行库标注最低版本为 14.0，但尚未在 14.0 实机验证。

### 🐍 和 WNTR 一起用

下载 **2.2 兼容加密包**并解压。选择 CPython 3.11 或 3.12，然后安装包内依赖：

```bash
python -m pip install -r /path/to/unpacked/requirements.txt
```

将示例中的路径换成实际解压目录：

```python
import os
import sys
from pathlib import Path

# 在线程运行库加载前设置；按机器和模型调整。
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OMP_DYNAMIC", "FALSE")

bundle = Path("/path/to/unpacked")
python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
if python_tag not in ("cp311", "cp312"):
    raise RuntimeError("Use CPython 3.11 or 3.12")
sys.path.insert(0, str(bundle / "python" / python_tag))

import wntr
from turbo_adapter import TurboSimulator
from fast_wntr_reader import FastBinFile

network = wntr.network.WaterNetworkModel("network.inp")
simulator = TurboSimulator(network, bundle / "native" / "linux_x86_64" / "libepanet2.so")
simulator.reader = FastBinFile()  # 可选：加速结果读取
results = simulator.run_sim(file_prefix="output/run", version=2.2)

pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

先创建 `output/`；Windows 使用 `native/windows_x86_64/epanet2.dll`，macOS 使用 `native/macos_arm64/libepanet2.dylib`。不设置 `simulator.reader` 就使用 WNTR 默认读取器。`FastBinFile` 也可单独用于 WNTR 自带内核：

```python
simulator = wntr.sim.EpanetSimulator(network, reader=FastBinFile())
```

🔐 适配器、批量辅助接口、快速读取器和基准脚本由 PyArmor 保护，包内包含对应运行时；**使用者不需要安装或购买 PyArmor**。请选择与 CPython 主次版本一致的目录，并保持运行时与脚本在一起。快速读取器目前只验证并接受 **WNTR 1.4.0**；包内依赖约束 `setuptools<82`，以提供该版本 WNTR 所需的 `pkg_resources`。`TurboSimulator` 临时切换进程内的 WNTR Toolkit 类，因此不要与同一进程中的其他 WNTR 仿真并发运行。

### 🧪 自己复测

解压后的加密包已经包含基准脚本；选对应 Python 版本的目录：

```bash
python /path/to/unpacked/python/cp312/benchmark_wntr.py --inp network.inp --library /path/to/unpacked/native/linux_x86_64/libepanet2.so --runs 5 --output benchmark.json
```

脚本要求同一内核的默认和快速读取器结果逐值一致，并记录原版与 Turbo 各字段的差异、位置和最大绝对差；状态不一致、非有限结果或计算错误会停止。它不替代工程容差验收。随后记录完整 `run_sim` 和各阶段耗时。使用 `--work-dir` 可以指定临时 INP、报告和输出文件的位置。仓库中的 [verify_fast_reader.py](examples/verify_fast_reader.py) 使用 Net1/2/3；运行时将对应的加密脚本目录加入 `PYTHONPATH`。[verify_bulk_auto.py](examples/verify_bulk_auto.py) 可对两个内核和 WNTR 自带 2.2 跑自动识别、读写与回退检查。请用自己的模型、机器和实际线程数验收。

### 🛠️ 兼容性与已知边界

- ✅ **2.2 兼容内核**：macOS 和仿真 Linux 的 WNTR 1.4.0 对照中，济南子网 49 个时刻的压力、水头、需水、流量和状态一致；Net2 也核对了节点与管段水质。快速读取器的 Net1/2/3 用例覆盖水龄、化学、溯源、统计和单位转换。
- 🪟 **Windows 与摩阻精度**：原生 Windows Server 2022 x64 上，preview.6 的 CPython 3.11 / 3.12 加密 2.2 包完成 Net2 的完整 WNTR 调用、批量操作与摩阻回归；此前 preview.5 还验证了 Net1/2/3 和水质，同一内核的两种读取器逐值一致。低流量时原先先把两端水头分别保存为单精度再相减，摩阻系数和水头损失可能出现较大误差。2.2 和 2.3 正常完整仿真已修正：Net2 25 小时管段 20 的摩阻系数约为 **0.09264412**，与即时双精度参考约 **0.09264413** 相符；原 WNTR 和旧 Turbo 分别约为 0.839289 和 0。不同内核仍可能有浮点差异，应按模型验收。
- 💾 **复用 `.hyd` 的精度边界**：为保持标准文件兼容，复用任何标准 `.hyd` 时仍使用其中保存的单精度水头，包括刚生成后再次读取的文件，水头损失和摩阻系数仍可能受旧精度限制。正常完整仿真会使用临时水头差文件，空间约为 `4 字节 × 连接数 × 水力时刻数`。
- ⚠️ **统计输出**：本机所测 NumPy 2.4.6 环境中，WNTR 1.4.0 的 `AVERAGED` 统计用例在默认读取器和快速读取器均抛出相同异常。
- 🔧 **2.3 收敛修复**：已修正零设定 TCV 的系数遗漏；三节点回归用例在 macOS、仿真 Linux 和原生 Windows Server 2022 x64 完成。**这不表示所有 2.3 收敛问题都已解决。**2.3 与 2.2 的直接 Toolkit 阀门状态编码和数值也可能不同。
- 🧮 **CHOLMOD / M9**：当前发行包使用内置线性求解器，关闭 CHOLMOD、外部求解器接管和 M9 融合组装。健康合成网格测试中，CHOLMOD 在约 2 万到 5 万节点间出现候选性能交叉，但结构和初始化耗时影响很大，**不是生产启用阈值**。负压、低于 15 m、警告、非有限值或短 EPS 的模型不能让 CHOLMOD 接管。
- 📂 **源码状态**：公开仓库目前不含与这些原生二进制完全对应的 C 构建源码；Release 标签对应文档和 WNTR 适配代码。各 ZIP 包含运行库许可证及第三方源码来源。

---

<a id="english"></a>

## 🇬🇧 English

**EPANET-Turbo** explores native EPANET optimizations and faster WNTR result loading for water-network simulation. Keep your familiar WNTR workflow and measure the difference on your own models. 🚀

**v2.8.1-preview.6** is a technical preview with separate EPANET 2.2-compatible and 2.3.3-based native engines, plus a PyArmor-protected fast reader for WNTR 1.4.0 and a version-aware batch interface for 2.2 / 2.3.

> ⚠️ **Fix for earlier 2.3 releases:** in v2.8.0, v2.8.1-preview.1 and preview.2, `ENT_set_demand_multiplier` changes relative viscosity instead of the demand multiplier and can return success. **This was fixed in preview.3.** Revalidate scenarios that used the affected function; on an earlier build, use the standard `EN_setoption(project, EN_DEMANDMULT, factor)`. The new `BulkAPI` uses the standard option on every engine, avoiding this issue with older builds.

> 📦 **Previous distribution:** preview.3 contained plaintext WNTR example scripts. The 2.2 ZIPs in preview.4 use PyArmor protection; previously published copies remain unchanged.

### ⚡ WNTR benchmark

One Jinan diagnostic network with **46,834 nodes / 48,245 links**, a 24-hour simulation and 49 reporting times, on Apple M4 / macOS arm64 / WNTR 1.4.0 / Python 3.12 / NumPy 2.4.6. The subnetwork was extracted using the original closed boundaries. No negative pressures occurred at the tested reporting times; the minimum was about 1.89 m, but some node-times were below 15 m:

| Configuration | Median full `run_sim` | vs. default WNTR |
| --- | ---: | ---: |
| WNTR EPANET 2.2 + default reader | 1.896 s | Baseline |
| WNTR EPANET 2.2 + fast reader | 1.199 s | ⬇️ about 37% |
| Turbo 2.2-compatible engine, 4 threads + default reader | 2.066 s | ⬆️ about 9% |
| **Turbo 2.2-compatible engine, 4 threads + fast reader** | **1.230 s** | **⬇️ about 35%** |

Using the PyArmor-protected distribution scripts, each configuration was warmed once and measured in five rotated rounds. Timing includes WNTR INP writing, native hydraulic and quality calls, and reading all results. The model object was loaded once before timing; **initial model loading and Python import are excluded**. This model uses quality type `NONE`; the initial model load was measured once at 1.306 s and recorded separately. Default and fast readers matched exactly for each engine. Pressure, head, demand, flow and status matched across engines; headloss and friction-factor output changed with the precision fix.

🔍 **Where does the improvement come from?**

- 📥 **Faster output reading:** IDs are read in batches and result tables are built directly, avoiding a large temporary MultiIndex. With the default engine, median result-reading time fell from **0.908 s to 0.122 s**, about 7.5 times faster in this test.
- ⚙️ **Parallel pipe coefficients:** OpenMP is used when the network has at least 10,000 links and more than one thread is requested. Results depend on the network and machine.
- 🧩 **2.2 compatibility:** the separate engine offers the 2.2 Toolkit and native bulk reads and writes for existing EPANET 2.2 / WNTR projects; the same Python interface works with 2.3.

Most of this measured gain comes from **result reading**, not the native solver alone. The reader-only median was 1.199 s versus 1.230 s for the combination, so this sample does not establish an additional end-to-end gain from the native engine. These numbers describe one model on one machine, not a general Windows, Linux or cross-model speed claim.

### 🧰 2.2 / 2.3 bulk APIs for network-wide operations

Both Turbo engines expose `ENT_set_node_values` / `ENT_set_link_values` for batch writes and `EN_get_all_pressures` / `EN_get_all_flows` for batch reads. These combine per-item Python/native calls into array calls. A single open project can also run several demand-multiplier scenarios.

With **Turbo 2.2** on the same Jinan network, compare WNTR Toolkit-style per-item calls and native batch calls on the same engine. Medians of five interleaved measurements after warm-up:

| Operation | Per-item | Native bulk | API-stage speedup |
| --- | ---: | ---: | ---: |
| Read pressure for 46,834 nodes | 12.532 ms | 0.147 ms | about 85× |
| Read flow for 48,245 links | 12.632 ms | 0.091 ms | about 139× |
| Set base demand for 46,828 nodes | 14.639 ms | 1.380 ms | about 10.6× |

Reads matched exactly; the setter includes conversion from lists to NumPy, with 26,323 values changed and readback/restoration verified. With reusable arrays the native setter median was 0.139 ms. This directly times the native API, excluding `BulkAPI` input validation, model opening and solving.

On the same Jinan subnetwork and Apple M4 / macOS arm64 / WNTR 1.4.0 / Turbo 2.3.3, compare WNTR Toolkit-style per-item calls and Turbo batch calls on the **same 2.3 engine**. Reads were warmed up; medians of five interleaved measurements:

| Operation | Per-item | Bulk | API-stage speedup |
| --- | ---: | ---: | ---: |
| Read pressure for 46,834 nodes | 12.34 ms | 0.110 ms | about 112× |
| Read flow for 48,245 links | 12.86 ms | 0.095 ms | about 136× |
| Set base demand for 46,828 nodes | 14.43 ms | 1.33 ms | about 10.8× |

Reads matched exactly; the setter timing includes conversion from Python lists to NumPy arrays, with 26,323 values actually changed and readback/restoration verified. With prepared, reusable arrays the setter median was 0.109 ms. **These timings exclude model loading and hydraulic solving and are not full-simulation speedups.** They do not claim that WNTR officially supports directly replacing its core with 2.3. [EPANET 2.3 itself also provides bulk read APIs](https://github.com/OpenWaterAnalytics/EPANET/blob/v2.3.3/include/epanet2_2.h); this comparison is against WNTR-style per-item calls, not against upstream 2.3 bulk reads.

For the same model, four complete hydraulic scenarios at factors 0.9 / 1.0 / 1.1 / 0.9 took 1.487 s reusing an open 2.3 project versus 1.682 s reopening for each, about 1.13×. This is a single run measuring model open, solve and compact pressure summaries, excluding other application I/O; cold/warm pressure summaries matched.

🔍 **Automatic detection:** extract the matching 2.2 or 2.3 package and add its `python/cp311` or `python/cp312` directory to `PYTHONPATH`. With an already-open WNTR Toolkit project:

```python
from turbo_bulk import BulkAPI

bulk = BulkAPI.from_wntr(toolkit)  # toolkit is ENopen; run ENopenH / ENinitH / ENrunH as needed
print(bulk.version, bulk.capabilities)
pressure = bulk.node_values()      # after a hydraulic step; defaults to EN_PRESSURE
flow = bulk.link_values()          # after a hydraulic step; defaults to EN_FLOW
bulk.set_node_values(1, [2, 3], [12.0, 9.0])  # EN_BASEDEMAND; 1-based indices
bulk.set_demand_multiplier(0.9)    # standard EN_DEMANDMULT
```

`BulkAPI(library, project)` also attaches to an open native project. It reads the loaded library's version and probes each capability: Turbo 2.2 / 2.3 use native bulk functions where available; other libraries use EPANET 2.3 native bulk reads or per-item fallback. Check `capabilities` for the selected path; scalar fallback preserves compatibility but has no native bulk speedup. Detection is based on the **loaded library, not the INP**; choose 2.2 or 2.3 to match your project. Ordinary WNTR `run_sim` does not automatically become a bulk workflow.

The [bulk and multi-scenario example](examples/bulk_auto_demo.py) selects the platform library from either bundle:

```bash
python examples/bulk_auto_demo.py --bundle /path/to/unpacked --inp examples/Net2.inp --node 2 --node 3 --pipe 1 --node-factor 1.01 --pipe-factor 1.01 --factors 0.9 1.0 1.1 0.9
```

The example modifies only the in-memory project. Toolkit values use model-native units; WNTR results use SI units. Batch writes stop at the first error, so earlier writes may already have been applied; inspect or restore as appropriate.

### 📦 Downloads and architectures

Choose one OS, CPU architecture and engine from the [download table above](#builds): **Windows x64**, **Linux x64**, or **macOS arm64**. The 2.2-compatible core reports `20200` from `EN_getversion`; the 2.3.3 core reports `20303`. `x64` means `x86_64`; macOS arm64 is Apple Silicon. No Windows ARM64, Linux ARM64 or Intel Mac build is provided. Keep each engine beside the bundled OpenMP runtime. These archives are **not Python wheels**. Both ZIPs place the engine under `native/<platform>/`; the 2.3 archive also retains the root native libraries for existing callers. Both archives contain the PyArmor-protected batch helper; the 2.2 archive also includes the encrypted WNTR adapter, fast reader and benchmark script. Python components include matching CPython 3.11 / 3.12 runtimes.

🧪 **Tested environments:** native macOS 27.0.1; Linux x64 on emulated Debian 12 / 13 in OrbStack; Windows x64 on a GitHub-hosted native Windows Server 2022 VM with WNTR 1.4.0 and CPython 3.11 / 3.12. Physical Windows and native Linux x64 server performance have not yet been tested. The bundled macOS runtime declares a minimum of macOS 14.0; that OS version has not been tested on a real machine.

### 🐍 Use with WNTR

Download and extract the **2.2-compatible encrypted archive**. Choose CPython 3.11 or 3.12 and install the included requirements:

```bash
python -m pip install -r /path/to/unpacked/requirements.txt
```

Replace the example path with your extracted directory:

```python
import os
import sys
from pathlib import Path

# Set before the OpenMP runtime is loaded; tune for your machine and model.
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OMP_DYNAMIC", "FALSE")

bundle = Path("/path/to/unpacked")
python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
if python_tag not in ("cp311", "cp312"):
    raise RuntimeError("Use CPython 3.11 or 3.12")
sys.path.insert(0, str(bundle / "python" / python_tag))

import wntr
from turbo_adapter import TurboSimulator
from fast_wntr_reader import FastBinFile

network = wntr.network.WaterNetworkModel("network.inp")
simulator = TurboSimulator(network, bundle / "native" / "linux_x86_64" / "libepanet2.so")
simulator.reader = FastBinFile()  # Optional: faster output reading
results = simulator.run_sim(file_prefix="output/run", version=2.2)

pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

Create `output/` first; use `native/windows_x86_64/epanet2.dll` on Windows and `native/macos_arm64/libepanet2.dylib` on macOS. Omit the reader assignment to use WNTR's default reader. The fast reader can also be used with WNTR's own engine:

```python
simulator = wntr.sim.EpanetSimulator(network, reader=FastBinFile())
```

🔐 The adapter, batch helper, fast reader and benchmark script are PyArmor-protected and include the matching runtime; **users do not need to install or buy PyArmor**. Choose the folder matching your CPython major/minor version and keep the runtime beside the scripts. The fast reader is validated for, and accepts, **WNTR 1.4.0** only; the included requirements constrain `setuptools<82` to provide the `pkg_resources` module required by this WNTR version. `TurboSimulator` temporarily switches the process-wide WNTR Toolkit class, so do not run other WNTR simulations concurrently in the same process.

### 🧪 Reproduce and test

The encrypted archive includes the benchmark script; use the folder matching your Python version:

```bash
python /path/to/unpacked/python/cp312/benchmark_wntr.py --inp network.inp --library /path/to/unpacked/native/linux_x86_64/libepanet2.so --runs 5 --output benchmark.json
```

The script requires exact equality between the default and fast readers for each engine, and records per-field differences, their locations and maximum absolute differences between stock and Turbo. It stops on different statuses, non-finite results or calculation errors; it does not establish engineering equivalence. It then times full `run_sim` and its stages. Set `--work-dir` to choose where temporary INP, report and output files are written. The repository's [verify_fast_reader.py](examples/verify_fast_reader.py) checks Net1/2/3; add the appropriate encrypted-script folder to `PYTHONPATH` when running it. [verify_bulk_auto.py](examples/verify_bulk_auto.py) checks detection, reads, writes and fallback with both engines and WNTR stock 2.2. Validate using your own models, hardware and thread count.

### 🛠️ Compatibility and known boundaries

- ✅ **2.2-compatible engine:** WNTR 1.4.0 comparisons on macOS and emulated Linux matched pressure, head, demand, flow and status for all 49 reporting times of the Jinan diagnostic subnetwork; Net2 node and link quality were also checked. Fast-reader cases on Net1/2/3 cover water age, chemical quality, tracing, statistics and unit conversion.
- 🪟 **Windows and friction precision:** on native Windows Server 2022 x64, the preview.6 encrypted 2.2 package ran the full Net2 WNTR workflow, bulk operations and friction regression on CPython 3.11 / 3.12. Preview.5 also checked Net1/2/3 and water quality; both readers matched for each engine. Previously, subtracting two separately rounded single-precision heads could magnify error in headloss and friction output at low flow. Normal full simulations now retain the head difference for both the 2.2 and 2.3 engines: Net2 pipe 20 at 25 hours gives a friction factor of about **0.09264412**, consistent with the live double-precision reference **0.09264413**, versus about 0.839289 in stock WNTR and 0 in the old Turbo build. Floating-point differences between engines still require model-specific review.
- 💾 **Reused `.hyd` precision:** standard `.hyd` compatibility is retained. Reusing any standard `.hyd`, including one just saved, still uses its single-precision heads, so headloss and friction can retain the old precision limit. A normal full simulation uses a temporary head-difference file of approximately `4 bytes × links × hydraulic steps`.
- ⚠️ **Statistics:** in the tested NumPy 2.4.6 environment, the WNTR 1.4.0 `AVERAGED` statistics case raises the same exception with both the default and fast readers.
- 🔧 **2.3 convergence fix:** the missing coefficient for a zero-setting TCV is fixed; the three-node regression ran on macOS, emulated Linux and native Windows Server 2022 x64. **This does not mean that every 2.3 convergence problem is solved.** Direct Toolkit valve status codes and results can also differ between 2.2 and 2.3.
- 🧮 **CHOLMOD / M9:** the current packages use the built-in linear solver; CHOLMOD, external solver takeover and M9 fused assembly are disabled. Healthy synthetic grids showed a candidate performance crossover between about 20,000 and 50,000 nodes, but topology and initialization matter; **this is not a production threshold**. Models with negative pressure, pressure below 15 m, warnings, non-finite values or short EPS must not use CHOLMOD takeover.
- 📂 **Source availability:** the public repository does not yet contain the exact C source used for these native binaries. The Release tag points to documentation and WNTR adapter code. Each ZIP includes runtime licenses and third-party source references.

---

<div align="center">

🏎️ **Measure it. Check the results. Then make it faster.**

[📦 Releases](https://github.com/ericwanderlust/epanet-turbo/releases) · [📄 License](LICENSE)

</div>
