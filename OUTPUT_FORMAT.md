# EPANET-Turbo Streaming Output Format v1.1

> 此文档定义了 v1.1 Streaming Sink 的稳定输出协议，后续版本将保持向后兼容。

## 目录结构

```plaintext
{output_dir}/
├── pressure.npy     # 节点压力 memmap [T, N]
├── flow.npy         # 管段流量 memmap [T, M]
├── times.npy        # 时间戳数组 [T]
└── metadata.json    # 元数据
```

## 文件格式

### pressure.npy / flow.npy

| 属性 | 值 |
| :--- | :--- |
| **格式** | NumPy memmap (raw binary) |
| **dtype** | `float32` (`<f4` little-endian) |
| **Layout** | Time-Major: `[T, N]` / `[T, M]` |
| **单位** | 压力: m (水头), 流量: LPS/CMH (取决于 INP 单位) |

### times.npy

| 属性 | 值 |
| :--- | :--- |
| **格式** | NumPy memmap (raw binary) |
| **dtype** | `int64` |
| **单位** | 秒 (自仿真开始) |
| **示例** | `[0, 900, 1800, 2700, ...]` |

### metadata.json

```json
{
  "version": "1.0",
  "dtype": "<f4",
  "shape_pressure": [T, N],
  "shape_flow": [T, M],
  "report_step_seconds": 900,
  "node_ids": ["J1", "J2", ...],
  "link_ids": ["P1", "P2", ...],
  "endianness": "<",
  "completed": true,
  "actual_steps": T
}
```

## 读取示例

```python
import numpy as np
import json

def load_streaming_result(output_dir):
    with open(f"{output_dir}/metadata.json") as f:
        meta = json.load(f)
    
    T = meta["actual_steps"]
    N = meta["shape_pressure"][1]
    M = meta["shape_flow"][1]
    
    pressure = np.memmap(
        f"{output_dir}/pressure.npy",
        dtype=meta["dtype"], mode='r', shape=(T, N)
    )
    flow = np.memmap(
        f"{output_dir}/flow.npy",
        dtype=meta["dtype"], mode='r', shape=(T, M)
    )
    times = np.memmap(
        f"{output_dir}/times.npy",
        dtype=np.int64, mode='r', shape=(T,)
    )
    
    return {"pressure": pressure, "flow": flow, "times": times, "meta": meta}
```

## ID 映射关系

`node_ids` 和 `link_ids` 列表的顺序与 EPANET 内部索引一致：

- `node_ids[i]` 对应 EPANET index `i+1`
- `link_ids[j]` 对应 EPANET index `j+1`
- `pressure[t, i]` = 节点 `node_ids[i]` 在时刻 `times[t]` 的压力

## 版本兼容性

| 版本 | 变更 |
| :--- | :--- |
| v1.0 | 初始版本 (EPANET-Turbo v1.1) |
