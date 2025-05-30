"""
Contains the views for the Admin API.
"""

import os
import platform
import subprocess

from flask import Blueprint, Response

from constants import LOG_FOLDER, MAIN_FOLDER

api = Blueprint("simple_page", __name__, template_folder="templates")
os_name = platform.system()


@api.route("/git-pull")
def git_pull():
    """
    Perform a git pull and log the result with an isoformate datetime.
    """
    log_file_path = LOG_FOLDER / "gitpull.log"

    if os_name == "Windows":
        subprocess.call(
            [
                "C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
                f'(Get-Date -Format s) + "`n" + (git -C "{MAIN_FOLDER.absolute()}" pull) | Add-Content "{log_file_path.relative_to(MAIN_FOLDER)}"',
            ]
        )
    elif os_name == "Linux":
        os.system(
            f'echo "$(date -Iseconds)\n$(git -C {repr(str(MAIN_FOLDER.absolute()))} pull)" >> {repr(str(log_file_path))}'
        )
    else:
        raise OSError("Unexpected Operating System")

    return Response(open(log_file_path, encoding="utf-8").read(), mimetype="text/plain")
