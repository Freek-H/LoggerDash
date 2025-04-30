"""
Contains the views for the Admin API.
"""

import os

from flask import Blueprint

from constants import LOG_FOLDER

api = Blueprint("simple_page", __name__, template_folder="templates")


@api.route("/git-pull")
def git_pull():
    """
    Perform a git pull and log the result with an isoformate datetime.
    """
    log_file_path = LOG_FOLDER / "gitpull.log"
    os.system(f'echo -e $"$(date -Iseconds)\n$(git pull)" >> {log_file_path}')
    return open(log_file_path, encoding="utf-8").read()
