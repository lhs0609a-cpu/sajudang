import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


@pytest.fixture(autouse=True)
def restore_reloaded_api_modules():
    """Tests that boot a fresh API must not leave two live module registries behind.

    Payment fixtures reload routers/store for isolated SQLite settings. Restore
    the registry afterwards so later tests patch the same provider their app uses.
    """
    def isolated(name):
        return name in ("store", "payments", "db", "main", "analytics") or name == "routers" or name.startswith("routers.")
    original = {name: module for name, module in sys.modules.items() if isolated(name)}
    yield
    for name in list(sys.modules):
        if isolated(name):
            sys.modules.pop(name, None)
    sys.modules.update(original)
