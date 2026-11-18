"""Import the HA-free api module without loading Home Assistant."""
from pathlib import Path
import sys
import types

root = Path(__file__).parents[1] / "custom_components" / "prana_air_local"
package = types.ModuleType("prana_lib")
package.__path__ = [str(root)]
sys.modules["prana_lib"] = package
