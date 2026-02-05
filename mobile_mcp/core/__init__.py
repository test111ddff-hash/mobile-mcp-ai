"""
Compatibility shim for `mobile_mcp.core` when running from source.

This package forwards symbol-level imports (e.g. `mobile_mcp.core.MobileClient`)
to the real implementations under the top-level `core` package.

We import from local shim modules (mobile_client.py, device_manager.py) which
use importlib to load the actual implementations, avoiding relative import issues.
"""

# Import from local shim modules that use importlib for dynamic loading
from .mobile_client import MobileClient  # noqa: F401
from .device_manager import DeviceManager  # noqa: F401

__all__ = ["MobileClient", "DeviceManager"]

