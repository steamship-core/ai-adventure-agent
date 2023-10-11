"""
Pytest reads this file in before doing any work. Read more about conftest.py under:
  - https://docs.pytest.org/en/stable/fixture.html
  - https://docs.pytest.org/en/stable/writing_plugins.html
"""

import sys
from pathlib import Path

# Make sure `steamship_tests` is on the PYTHONPATH. Otherwise cross-test imports (e.g. to util libraries) will fail.
sys.path.append(str(Path(__file__).parent.absolute()))

from steamship_tests.fixtures import (  # noqa: F401, E402
    client,
    invocable_handler,
    invocable_handler_with_client,
)
