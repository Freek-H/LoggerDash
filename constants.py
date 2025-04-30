"""
Functions as a central location to load constants from such as paths to directories and files,
 values that are globally configured, and secrets loaded from environment.
"""

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

MAIN_FOLDER = Path(__file__).parent
load_dotenv(MAIN_FOLDER / ".env")

os_name = platform.system()
if os_name == "Windows":
    DATA_DIR = MAIN_FOLDER / "streams"
elif os_name == "Linux":
    DATA_DIR = Path("~/scripts/prod/logs").expanduser()
else:
    raise OSError("Unexpected Operating System")

DATA_DIR.mkdir(exist_ok=True, parents=True)

APP_DATA_DIR = MAIN_FOLDER / "data"
APP_DATA_DIR.mkdir(exist_ok=True, parents=True)
IMAGES_FOLDER = APP_DATA_DIR / "images"
IMAGES_FOLDER.mkdir(exist_ok=True, parents=True)

LOG_FOLDER = MAIN_FOLDER / "logs"
LOG_FOLDER.mkdir(exist_ok=True, parents=True)

TEMPERATURE_API_ADDRESS = os.getenv(
    "TEMPERATURE_API_ADDRESS", default="http://127.0.0.1:5001/api"
)
