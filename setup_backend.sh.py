from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("/Users/amidamaru/Documents/Projects/netops-assistant")


def main() -> None:
    """Устанавливает backend-проект в editable-режиме с dev-зависимостями."""
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "./backend[dev]"],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()