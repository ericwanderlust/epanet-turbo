# EPANET-Turbo v2.3.0 Release Notes / 发布说明

## 🚀 Performance Breakthrough: "Targeted Adaptive Relaxation"

## 🚀 性能突破："目标自适应松弛 (Targeted Adaptive Relaxation)"

This release introduces a major upgrade to the hydraulic solver's convergence strategy (M7-9), specifically optimized for large-scale and difficult-to-solve models.
本次发布对水力求解器的收敛策略进行了重大升级 (M7-9)，专门针对大规模和难收敛的模型进行了优化。

> [!IMPORTANT]
> **Windows Only**
> The current M7 optimization is only enabled for Windows (x64) users due to the updated `epanet2.dll`. Linux and macOS users will receive the standard v2.2 solver.
> **仅限 Windows**
> 目前 M7 优化仅对 Windows (x64) 用户生效 (因 `epanet2.dll` 更新)。Linux 和 macOS 用户将继续使用标准的 v2.2 求解器。

### Key Highlights / 核心亮点

- **2.8x Speedup on Large Models**: The reference `40w_fixed.inp` (400k nodes) simulation time dropped from **403s** to **142s**.
  **大模型 2.8倍 提速**: 基准模型 `40w_fixed.inp` (40万节点) 的模拟时间从 **403秒** 降至 **142秒**。

- **Iteration Optimization**: Average iterations per hydraulic step reduced by **81%** (from 5.3 to 1.01).
  **迭代优化**: 每个水力模拟步的平均迭代次数减少了 **81%** (从 5.3次 降至 1.01次)。

- **Convergence Bottleck Eliminated**: Time spent in convergence checks reduced by **98%** (141s -> 2.5s).
  **消除收敛瓶颈**: 收敛检查 (Convergence Check) 的耗时减少了 **98%** (141秒 -> 2.5秒)。

### Technical Details / 技术细节

- **Adaptive Relaxation**: Implemented a smart damping strategy that automatically detects "Long Tail" oscillation (steps with >10 iterations) and applies aggressive relaxation (`RelaxFactor = 0.5`) to break the cycle.
  **自适应松弛**: 实施了一种智能阻尼策略，自动检测 "长尾" 震荡 (迭代超过10次的步骤)，并应用激进的松弛因子 (`RelaxFactor = 0.5`) 来打破循环。

- **Minimal Overhead**: The new strategy is only active when needed, ensuring zero impact on standard, easy-to-solve steps.
  **极低开销**: 新策略仅在需要时激活，确保对标准、易求解的步骤零影响。

### Full Changelog / 完整更新日志

- **[Feature]** M7-9: Targeted Adaptive Relaxation for hydraulic solver (Windows only).
  **[新特性]** M7-9: 水力求解器的目标自适应松弛策略 (仅限 Windows)。
- **[Enhancement]** Optimized `hydraul.c` iteration profiling and tracking.
  **[改进]** 优化了 `hydraul.c` 的迭代分析和跟踪。
- **[Fix]** Corrected step counting logic in iteration profiler.
  **[修复]** 修正了迭代分析器中的步数统计逻辑。

> **Note**: This version is fully backward compatible with v2.2.0.
> **注意**: 此版本与 v2.2.0 完全向后兼容。
