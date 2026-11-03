"""Run a WNTR EPANET 2.2 simulation with an explicitly selected Turbo library.

Use this adapter in a process that does not start other WNTR simulations
concurrently. WNTR chooses its toolkit through a process-wide module variable.
"""

import ctypes
import os
from pathlib import Path
from threading import Lock

import wntr
import wntr.epanet.toolkit as toolkit


_TOOLKIT_LOCK = Lock()


class TurboSimulator(wntr.sim.EpanetSimulator):
    def __init__(self, water_network, library_path):
        super().__init__(water_network)
        self.library_path = Path(library_path).expanduser().resolve(strict=True)

    def run_sim(self, *args, **kwargs):
        with _TOOLKIT_LOCK:
            original = toolkit.ENepanet
            library_path = str(self.library_path)

            class TurboToolkit(original):
                def __init__(self, *toolkit_args, **toolkit_kwargs):
                    if float(toolkit_kwargs.get("version", 2.2)) != 2.2:
                        raise ValueError("TurboSimulator requires WNTR's EPANET 2.2 API")
                    super().__init__(*toolkit_args, **toolkit_kwargs)
                    loader = ctypes.WinDLL if os.name == "nt" else ctypes.CDLL
                    self.ENlib = loader(library_path)

            toolkit.ENepanet = TurboToolkit
            try:
                return super().run_sim(*args, **kwargs)
            finally:
                toolkit.ENepanet = original
