# EPANET-Turbo v2.1.0 Release Notes

🚀 **EPANET-Turbo v2.1.0** 正式发布！本次更新带来了核心 Rule Engine 的性能飞跃，并统一了里程碑命名规范。

## 🌟 核心更新 (Key Highlights)

### 1. Milestone M6-2: 状态驱动规则优化 (State-Driven Rule Evaluation)

- **从 M2-2 更名为 M6-2**: 为保持架构演进逻辑一致，我们将“规则引擎优化”里程碑正式定名为 M6-2。
- **倒排索引技术 (Inverted Index)**: 建立节点/管段状态变更到规则的映射，实现“仅评估受影响规则”，大幅降低大规模规则集下的计算开销。
- **依赖追踪 (Dependency Tracking)**: 自动分析规则逻辑，跳过无关的评估步骤。

### 2. 引擎稳定性与兼容性 (Stability & Compatibility)

- **OWA 2.3 基准同步**: 同步了最新的 OWA-EPANET 2.3 核心定义，提升了 API 的标准化程度。
- **跨平台支持强化**: 完善了 Windows (x86_64), Linux (x86_64) 及 macOS (Apple Silicon) 的编译支持。
- **底层 Bug 修复**: 解决了旧版本中规则引擎内存释放及头文件引用顺序导致的编译冲突。

## 📦 如何安装 (Installation)

推荐下载 **[EPANET-Turbo_v2.1.0_Release.zip](Releases/EPANET-Turbo_v2.1.0_Release.zip)**，并使用内置的安装器：

```bash
# 1. 解压后进入目录
# 2. 运行一键安装与演示脚本
python setup_and_demo.py
```

或者直接安装 Wheel 包：

```bash
pip install ./dist/epanet_turbo-2.1.0-py3-none-any.whl
```

## 📋 变更详情 (Changelog)

- **[Feature]** 全局重构 M2-2 逻辑为 M6-2。
- **[Refactor]** 修复 `rules.c` 中的大小写敏感问题及 `include` 顺序冲突。
- **[Build]** 成功产出集成 OpenMP 与 M6-2 优化的 `epanet2.dll`。
- **[Docs]** 更新了 `README.md` 及核心文档索引。

---
*感谢您对 EPANET-Turbo 的支持！更极速，更稳定。*
