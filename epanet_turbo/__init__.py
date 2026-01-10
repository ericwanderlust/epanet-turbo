from .parser import InpParser
from .cache import ModelCache
from .context import simulate, ModelContext

# Constants (assuming engine.py has them or we define them)
# If engine.py doesn't have them, we might need a separate enums.py or import from engine if it has *
# For now, exporting specific ones used in tests.
from .engine import EN_STATUS, EN_CLOSED, EN_OPEN, EN_LINKCOUNT, EN_FLOW

__version__ = "1.3.0"
