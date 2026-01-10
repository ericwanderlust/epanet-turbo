# EPANET-Turbo Streaming Output Format v2.0 (Protocol V2)

> 适用版本: EPANET-Turbo v2.0+

EPANET-Turbo 采用自定义的 **流式二进制格式 (Streaming Binary Format)** 来存储大规模仿真结果。该格式旨在实现：

1. **极低内存占用**: 支持 50万+ 节点 x 8760 小时（全年）的仿真结果存储。
2. **零拷贝读取**: 支持 Python `numpy.memmap` 直接映射读取。
3. **结构化分离**: 核心数据 (.out) 与元数据 (.meta.json) 分离。

## 目录结构

每次仿真通过 `StreamingReporter` 将生成以下两个文件：

```plaintext
{filename}.out        # 二进制数据体 (Protocol V2 Binary)
{filename}.meta.json  # 语义元数据 (IDs, Config, Stats)
```

---

## 1. 二进制数据文件 (.out)

采用 **Protocol V2** 格式，由 **512字节文件头** 和后续紧凑排列的 **时间步数据块** 组成。默认采用 **小端序 (Little-Endian)**。

### 1.1 文件头 (Header) - Fixed 512 Bytes

| 偏移 (Hex) | 大小 | 类型 | 字段名 | 值/说明 |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | 4 | `char[4]` | `magic` | `b'EPST'` (EPANET Streaming Turbo) |
| `0x04` | 4 | `int32` | `version` | `2` (代表 Protocol V2) |
| `0x08` | 4 | `int32` | `n_nodes` | 节点数量 (N) |
| `0x0C` | 4 | `int32` | `n_links` | 管段数量 (M) |
| `0x10` | 8 | `int64` | `start_ts` | 仿真起始 Unix 时间戳 |
| `0x18` | 4 | `int32` | `rpt_step` | 报告输出步长 (秒) |
| `0x1C` | 484 | `byte[]` | `reserved` | 保留填充位 (全0) |

### 1.2 数据体 (Data Body)

头部之后，每经过一个报告步长 (Reporting Step)，追加写入一个数据块 (Block)。

**单步块结构 (Block Structure):**

| 顺序 | 字段 | 大小 (Bytes) | 数据类型 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `t_idx` | 4 | `int32` | 当前仿真时刻 (秒, 相对 T=0) |
| 2 | `pressures` | $N \times 4$ | `float32[]` | 所有节点压力值 (m) |
| 3 | `flows` | $M \times 4$ | `float32[]` | 所有管段流量值 (LPS) |

**计算公式:**

- 单步大小 (Block Size): $S_{block} = 4 + 4N + 4M$ (bytes)
- 文件偏移 (File Offset): $Offset(t) = 512 + t \times S_{block}$

> **v2.0 改进**: Protocol V2 强制对齐 float32 数组边界，确保 SIMD 指令集读取时的最佳性能。

---

## 2. 元数据文件 (.meta.json)

存储模型的语义信息，用于将二进制数组下标映射回实际 ID。

```json
{
  "protocol": 2,
  "engine_version": "2.0.0",
  "created_at": "2026-01-10T12:00:00",
  "config": {
    "rpt_step": 3600,
    "duration": 604800,
    "start_time": 1735689600
  },
  "stats": {
    "nodes": 400000,
    "links": 420000
  },
  "ids": {
    "nodes": ["J-1", "J-2", "Tank-1", ...],  // 索引 0 -> N-1
    "links": ["P-1", "P-2", "Pump-1", ...]   // 索引 0 -> M-1
  }
}
```

---

## 3. 读取示例 (Python SDK)

EPANET-Turbo SDK 提供了封装好的读取器：

```python
from epanet_turbo.streaming import load_streaming_result

# 自动加载 .out 和 .meta.json
res = load_streaming_result("simulation_output.out")

# 1. 获取 ID 列表
node_ids = res.node_ids  # List[str]

# 2. 获取压力矩阵 (Lazy Loading via Memmap)
# Shape: (TimeSteps, Nodes)
pressures = res.pressures 

# 3. 获取第 24 小时的某个节点压力
p_val = pressures[24, 0] 
print(f"Time: {res.times[24]}s, Node: {node_ids[0]}, P: {p_val:.2f}")
```

---

## 变更历史

| 版本 | 协议 | 关键变更 |
| :--- | :--- | :--- |
| **v2.0** | **V2** | 数据边界对齐优化；强化 Meta JSON 字段；支持 Unix Timestamp。 |
| v1.3 | V1 | 引入分离式 Header+Body 二进制设计。 |
| v1.0 | V0 | 初始版本 (基于 NPY)。 |
