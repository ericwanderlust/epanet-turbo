# EPANET-Turbo Streaming Output Format v1.3 (Protocol V1)

> 引入于 EPANET-Turbo v1.3 (M3)，取代了旧版的分离式 NPY 格式。

## 目录结构

输出目录或文件前缀将生成及其关联元数据：

```plaintext
{filename}.out        # 二进制数据流文件 (Header + Data Blocks)
{filename}.meta.json  # 元数据 (IDs, Config)
```

## 1. 二进制数据文件 (.out)

采用紧凑的二进制格式存储，包含 **文件头 (Header)** 和 **数据步 (Data Steps)**。

### 1.1 文件头 (Header) - 512 Bytes

文件起始为固定的 512 字节头，用于校验和元数据解析。

| 偏移 (Offset) | 类型 (Type) | 字段 (Field) | 说明 |
| :--- | :--- | :--- | :--- |
| 0 | `char[4]` | `magic` | 固定为 `b'EPST'` (EPANET Streaming) |
| 4 | `int32` | `version` | 协议版本，当前为 `1` |
| 8 | `int32` | `n_nodes` | 节点总数 (N) |
| 12 | `int32` | `n_links` | 管段总数 (M) |
| 16 | `int64` | `start_time` | 仿真开始 Unix 时间戳 |
| 24 | `int32` | `rpt_step` | 报告步长 (秒) |
| 28 | `byte[484]` | `reserved` | 保留位 (全零) |

### 1.2 数据体 (Data Body)

头部之后紧接数据块。每个输出步长 (Reporting Step) 生成一个数据块。

**单步块结构 (Block Structure):**

| 顺序 | 数据内容 | 大小 (Bytes) | 类型 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Time | 4 | `int32` | 仿真时刻 (秒, 从 0 开始) |
| 2 | Node Pressures | $N \times 4$ | `float32[]` | 所有节点压力数组 |
| 3 | Link Flows | $M \times 4$ | `float32[]` | 所有管段流量数组 |

**文件总大小**: `512 + T * (4 + N*4 + M*4)` 字节。

---

## 2. 元数据文件 (.meta.json)

存储人类可读的配置信息与 ID 索引。

```json
{
  "version": 1,
  "created_at": 1709...,
  "rpt_step": 3600,
  "counts": {
    "nodes": 118796,
    "links": 120000
  },
  "ids": {
    "nodes": ["J1", "J2", ...],  // 对应 pressure 数组下标
    "links": ["P1", "P2", ...]   // 对应 flow 数组下标
  }
}
```

---

## 3. 读取示例 (Python)

使用 `epanet_turbo.streaming.load_streaming_result` 即可自动解析。

```python
from epanet_turbo.streaming import load_streaming_result

# 传入 .out 文件路径或包含 .out 的目录
res = load_streaming_result("output/model_result.out")

# 返回字典
# res['times']: [0, 3600, 7200, ...]
# res['pressure']: ndarray (T, N) float32
# res['flow']: ndarray (T, M) float32
# res['node_ids']: list of str
```

## 变更历史

| 版本 | 协议版本 | 变更 |
| :--- | :--- | :--- |
| v1.3 | V1 | 引入单文件 Header+Body 格式，支持元数据分离 (.meta.json) |
| v1.2 | v1.0 | I/O重构阶段 (NumPy memmap) |
