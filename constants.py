"""
Functions as a central location to load constants from such as paths to directories and files,
 values that are globally configured, and secrets loaded from environment.
"""

import platform
from pathlib import Path

MAIN_FOLDER = Path(__file__).parent

os_name = platform.system()
if os_name == "Windows":
    DATA_DIR = MAIN_FOLDER / "data"
elif os_name == "Linux":
    DATA_DIR = Path("~/scripts/prod/logs")
else:
    raise OSError("Unexpected Operating System")

DATA_DIR.mkdir(exist_ok=True, parents=True)

LOG_FOLDER = MAIN_FOLDER / "logs"
LOG_FOLDER.mkdir(exist_ok=True, parents=True)
