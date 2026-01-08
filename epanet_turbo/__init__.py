"""
EPANET-Turbo 🏎️
极速水力计算引擎 | High-Performance Hydraulic Engine

Copyright (c) 2026 ES (Serein) - All Rights Reserved
Project UID: EPANET-TURBO-ES-2026-SEREIN93

基于 EPANET 2.2，采用 Polars 并行解析 + OpenMP 多线程仿真
Powered by Polars parallel parsing + OpenMP multi-threaded simulation
"""

__version__ = "1.1.0"
__author__ = "ES (Serein)"
__license__ = "MIT"

# 核心模块导出
from .parser import InpParserPolars as InpParser
from .parser import load_inp
from .engine import simulate, run_simulation
from .context import ModelContext

# 遥测初始化 (非阻塞，可通过环境变量禁用遥测，但许可证检查强制执行)
try:
    from . import telemetry as _tel
    _tel._init_beacon()
except ImportError:
    pass

__all__ = [
    "InpParser",
    "load_inp", 
    "simulate",
    "run_simulation",
    "ModelContext",
    "__version__",
]
