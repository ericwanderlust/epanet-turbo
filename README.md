# EPANET-Turbo

> **预览版已知问题：** macOS arm64 在一个存在断连和负压的内部大型模型首步返回水力求解错误 110；WNTR 自带 EPANET 2.2 与历史 v2.8 库完成计算但报告负压警告 6。原因正在排查；此预览不适合作为性能交付或生产版本。

EPANET-Turbo 是基于 OWA-EPANET 2.3 的水力计算引擎；本次构建的 `EN_getversion` 返回 `20300`。本仓库提供项目文档、示例以及与 WNTR 的接入示例。最新的原生库按操作系统和 CPU 架构分别发布。

## 最新版本

[**v2.8.1-preview.1 — 分平台原生库**](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.1) 是预览版。三个库来自同一份 Phase D C 引擎快照；使用内置求解器构建，未启用 OpenMP，也不包含 CHOLMOD 插件。只读 shadow ABI 可用于诊断，不接管水力求解。

| 系统 | CPU 架构 | Release 文件 | 验证状态 |
| --- | --- | --- | --- |
| Windows | x64 / x86_64 | `epanet2-windows-x64.dll` | 已交叉编译并检查 EPANET 2.2 API 导出；待 Windows 实机运行验证 |
| Linux | x64 / x86_64 | `libepanet2-linux-x64.so` | OrbStack x86_64 Linux：WNTR 1.4.0、Python 3.11 和 Net1 已对照验证 |
| macOS | arm64 / Apple Silicon | `libepanet2-macos-arm64.dylib` | WNTR 1.4.0、Python 3.12 和 Net1 已对照验证 |

Linux 库构建于 Debian 12、glibc 2.36 环境。macOS 库的部署目标为 macOS 11.0，实际测试环境为 macOS 27.0.1；较旧系统尚未实测。当前没有 Windows ARM64、Linux ARM64 或 Intel Mac 的预览构建。下载库时请同时查看 Release 中的 `LICENSES.txt`。

这些文件是原生库，供已有 EPANET 或 WNTR 集成使用，不是 Python wheel。上一版包含 wheel 的集成发布仍可在 [v2.8.0](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.0) 找到。当前公开仓库未包含与本次二进制完全对应的 C 构建源码；Release 标签对应本仓库的文档和 WNTR 适配代码。

## 与 WNTR 一起使用

[WNTR](https://github.com/USEPA/WNTR) 默认使用自己附带的 EPANET 库，不会自动切换到 Turbo。下载与操作系统、CPU 架构匹配的库，并使用本仓库的 [WNTR 适配器](examples/turbo_adapter.py) 显式指定路径。适配器保留 WNTR 的 `SimulationResults` 返回格式：

```python
import wntr
from turbo_adapter import TurboSimulator  # 将 examples/turbo_adapter.py 放在项目目录中

network = wntr.network.WaterNetworkModel("network.inp")
simulator = TurboSimulator(network, "/absolute/path/to/platform/library")
results = simulator.run_sim(file_prefix="output/run", version=2.2)
pressure = results.node["pressure"]
flow = results.link["flowrate"]
```

本次 Linux 测试使用 WNTR 1.4.0 和 Python 3.11；该组合需要 `six` 以及仍提供 `pkg_resources` 的 setuptools。独立环境可使用 `pip install "wntr==1.4.0" "six>=1.17" "setuptools<81" "python-dateutil<3"`。

也可以在仓库目录运行示例：

```bash
python examples/demo_adapter.py --inp examples/Net1.inp \
  --library /absolute/path/to/platform/library --file-prefix output/run
```

`output/` 应事先存在。适配器会在运行期间临时选择 WNTR toolkit 类；请在没有其他并发 WNTR 仿真的独立进程中使用。适配器要求 WNTR 的 EPANET 2.2 API，不能把 WNTR 的其他版本选项视为已经验证。

macOS 和 OrbStack Linux 的 Net1 对照均覆盖 24 小时、25 个报告时刻，压力、水头、需水量和流量均与 WNTR 自带 EPANET 2.2 的对应输出一致。它不代表所有模型、控制规则、水质功能或平台都已通过兼容性验收；请使用自己的模型开展对照。

## 收敛问题的历史

旧文档中的 **Turbo v2.3 / M7** 是产品版本号；它与底层 **EPANET 2.3** 是两个不同的版本概念。M7 引入了针对长尾迭代震荡的自适应松弛，当前引擎源码保留该逻辑，但这不等于所有模型的收敛问题都已解决。

2026 年 5 月的一次 Net1 异常被定位到默认启用的融合矩阵组装：当时出现 26 步和警告 4。默认路径随后改回 legacy 矩阵组装；本次 macOS 和 Linux 原生 Net1 全周期均为 27 个水力步，调用返回码为 0。融合优化和 CHOLMOD/NMM 的生产就绪性仍需独立验证。

## 已知边界

- Windows 库尚未在 Windows 或 Windows CI 中运行验证。
- M9 的 NMM/CHOLMOD 病态模型正确性和生产接管仍未完成；本预览版不启用 CHOLMOD 接管。
- 带负压、低压、非有限值、求解警告或硬错误的模型不能仅凭 shadow 结果启用外部求解器。
- 原有性能数字来自历史实验，不能据此推断此次构建或其他模型的加速比。

## English

The [v2.8.1-preview.1 release](https://github.com/ericwanderlust/epanet-turbo/releases/tag/v2.8.1-preview.1) distributes separate native libraries for **Windows x64**, **Linux x64**, and **macOS arm64**. Windows is cross-compiled and awaits a Windows runtime test. The Linux build uses Debian 12 / glibc 2.36. The macOS deployment target is 11.0; runtime testing was performed on macOS 27.0.1. The macOS and emulated Linux x64 builds have been compared with WNTR 1.4.0's EPANET 2.2 on Net1. Windows ARM64, Linux ARM64, and Intel macOS binaries are not included.

For WNTR, copy [examples/turbo_adapter.py](examples/turbo_adapter.py) into your project and pass the downloaded library path to `TurboSimulator`. Run it in a process without concurrent WNTR simulations; the adapter temporarily selects a process-wide toolkit class. The underlying engine reports EPANET 2.3. The preview retains Turbo's adaptive relaxation and uses the built-in solver with OpenMP disabled and does not enable CHOLMOD takeover. The release contains native libraries, not a Python wheel. The matching C build source is not included in this public repository.

## License

See [LICENSE](LICENSE) and the `LICENSES.txt` file supplied with the native release.
