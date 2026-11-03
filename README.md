# EPANET-Turbo

> **严重问题：** 2.3 版的 `ENT_set_demand_multiplier` 会错误地修改相对黏度，而非需水倍率，并可能返回成功。请勿调用；可改用 `EN_setoption(project, EN_DEMANDMULT, factor)`，并重新验证使用此接口得到的工况结果。macOS arm64 和仿真 Linux x64 已复现，Windows 由同一实现构建。2.2 兼容包不导出此接口。
>
> **Critical:** The 2.3 `ENT_set_demand_multiplier` changes relative viscosity instead of the demand multiplier and can return success. Do not use it; revalidate affected scenarios.

EPANET-Turbo 探索 EPANET 原生水力性能优化。[v2.8.1-preview.2](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.2) 仅在一个模型上测得小幅加速，尚未证明在其他模型或 Windows / Linux 实机上有显著性能优势；其 2.3 批量需水接口存在上面的错误。下载包按操作系统、CPU 架构和 EPANET 内核分别提供。

## 选择内核和平台

| 内核 | Release 文件名中的标识 | 适用场景 |
| --- | --- | --- |
| EPANET 2.2 兼容 | `epanet22-compat` | 现有 EPANET 2.2 Toolkit 或 WNTR 项目；`EN_getversion` 返回 `20200`。该变体提供标准 2.2 Toolkit，不包含 Turbo 专有的 bulk API。 |
| EPANET 2.3.3 | `epanet23` | 使用 2.3.3 引擎能力的项目；`EN_getversion` 返回 `20303`。 |

| 平台 | 架构 | 引擎文件 | 当前验证 |
| --- | --- | --- | --- |
| Windows | x64 / x86_64 | `epanet2.dll` | OrbStack 中通过 Wine 仿真运行；尚未在真实 Windows 上测试。 |
| Linux | x64 / x86_64 | `libepanet2.so` | OrbStack 仿真 Debian 12 / glibc 2.36，WNTR 1.4.0 已验证。 |
| macOS | arm64 / Apple Silicon | `libepanet2.dylib` | 原生测试 macOS 27.0.1；随包运行库标注最低 macOS 14.0，较旧系统未实测。 |

Release 中每个平台、每种内核是单独的 ZIP。解压后请保留同目录的 OpenMP 运行库和许可证文件；它们不是 Python wheel。当前没有 Windows ARM64、Linux ARM64 或 Intel Mac 构建。旧版 wheel 集成包可在 [v2.8.0](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.0) 查看。

## 与 WNTR 一起使用

[WNTR](https://github.com/USEPA/WNTR) 默认使用自己附带的 EPANET 库。将 [examples/turbo_adapter.py](examples/turbo_adapter.py) 复制到项目目录，选择与系统和架构匹配的原生库路径：

```python
import os

# 在线程运行库加载前设置；按实际机器调整线程数。
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OMP_DYNAMIC", "FALSE")

import wntr
from turbo_adapter import TurboSimulator

network = wntr.network.WaterNetworkModel("network.inp")
results = TurboSimulator(network, "/absolute/path/to/libepanet2.so").run_sim(
    file_prefix="output/run", version=2.2
)
pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

`output/` 应事先存在；Windows 和 macOS 分别使用 ZIP 中的 `.dll` 和 `.dylib` 路径。`version=2.2` 指 WNTR 使用的 Toolkit 接口；实际计算内核由 `library_path` 指定。适配器运行时会临时切换进程内的 WNTR toolkit 类，请勿在同一进程并发运行其他 WNTR 仿真。

2.2 兼容版在 macOS（Python 3.12）与仿真 Linux x64（Python 3.11）上用 WNTR 1.4.0 对照测试：一个 46,834 节点、49 个报告时刻的诊断子网的压力、水头、需水、流量和状态与 WNTR 自带的 2.2 结果逐值一致；Net2 的 56 个报告时刻还核对了节点和管段水质。请继续对自己的模型和控制规则做对照。

2.3 与 2.2 的数值和直接 Toolkit 状态语义可能不同：例如 `EN_STATUS` 对活动阀在 2.2 中返回 `1`，在 2.3 中可能返回 `2`。WNTR 适配器负责加载和运行，不为直接 Toolkit 调用转换状态值。需要延续 2.2 计算语义的项目应选择 `epanet22-compat`。

## 性能实测

在 Apple M4 / macOS arm64 上，同一 46,834 节点诊断子网、24 小时 / 49 步，分别预热后交错测量 9 轮，以下为 `EN_solveH` 水力计算中位数：

| 对照 | 候选 | 对照中位数 | 候选中位数 | 耗时变化 |
| --- | --- | ---: | ---: | ---: |
| WNTR 自带 EPANET 2.2，1 线程 | 2.2 兼容版，4 线程 | 0.3230 s | 0.2912 s | 下降 9.9% |
| 官方 OWA EPANET 2.3.3，1 线程 | 2.3 版，4 线程 | 0.3339 s | 0.3200 s | 下降 4.2% |

测试只计原生 `EN_solveH`，包含水力文件保存，不包含 WNTR 输入转换、结果读取或水质模拟。管道系数并行在网络至少有 10,000 条连接且线程数大于 1 时启用。结果只说明此模型和测试机器的表现，不代表其他模型、完整 WNTR 工作流或 Windows / Linux 实机性能。

## 收敛与已知边界

- 2.3 版修正了零设定 TCV 的系数遗漏：三节点正压回归用例在 macOS、仿真 Linux 和 Wine Windows x64 均完成。此前 [preview.1](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.1) 在 macOS 和仿真 Linux 上对此用例返回错误 110。
- 历史 Turbo M7 的自适应松弛不等同于 EPANET 2.3 版本号；当前 2.3 候选采用与 OWA 对齐的松弛逻辑。现有证据不支持声称所有 EPANET 2.3 收敛问题均已修复。
- 当前发行包使用内置线性求解器，启用管道系数 OpenMP，并关闭外部求解器接管、M9 融合组装和 CHOLMOD。M9 / NMM 的矩阵一致性、并发写入和内存所有权仍需修复与验证。
- Windows 尚未在真实 Windows 环境执行，Linux 尚未在 x64 服务器实测性能；macOS 14 的运行库最低版本依据二进制元数据，尚未在 macOS 14 实机测试。此版本是预览，使用生产模型前请自行完成对应环境与数值验收。
- 当前公开仓库不包含与本次原生二进制完全对应的 C 构建源码；Release 标签对应文档和 WNTR 适配代码。每个 ZIP 包含运行库许可证和第三方源码来源。

## English

The [v2.8.1-preview.2 technical preview](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.2) ships separate native packages for **Windows x64**, **Linux x64**, and **macOS arm64**, with a choice between an EPANET 2.2 compatibility core and an EPANET 2.3.3-based core. Each ZIP includes its platform's OpenMP runtime. Windows was tested using Wine in emulation; Linux was tested on emulated Debian 12 with WNTR 1.4.0; macOS was tested natively on macOS 27.0.1. The bundled macOS runtime declares a macOS 14 minimum. Choose the 2.2 core when matching existing 2.2 / WNTR behavior matters, and validate against your own models. The 2.3 core fixes the zero-setting TCV regression; it does not claim to resolve every convergence issue. CHOLMOD and M9 takeover are disabled.

See [LICENSE](LICENSE), the licenses in each package, and the release notes for measurements and limitations.
