"""
Forwarder module so that `from mobile_mcp.core.device_manager import DeviceManager`
works when running from source.
"""

from pathlib import Path
import importlib.util
import sys


# 项目根目录：.../mobile_mcp
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _load_impl():
    """
    Load the real `core.device_manager` module and return its DeviceManager.

    We need to ensure the core package is properly set up for relative imports.
    """
    # First, ensure core package is in sys.modules
    core_init_path = _PROJECT_ROOT / "core" / "__init__.py"
    if "core" not in sys.modules:
        spec = importlib.util.spec_from_file_location("core", core_init_path)
        core_module = importlib.util.module_from_spec(spec)
        sys.modules["core"] = core_module
        if spec.loader is not None:
            spec.loader.exec_module(core_module)
    
    # Now load device_manager as part of the core package
    impl_path = _PROJECT_ROOT / "core" / "device_manager.py"
    spec = importlib.util.spec_from_file_location(
        "core.device_manager", impl_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.DeviceManager


DeviceManager = _load_impl()

__all__ = ["DeviceManager"]

