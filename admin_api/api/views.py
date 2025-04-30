"""
Contains the views for the Admin API.
"""

import os

from flask import Blueprint

api = Blueprint("simple_page", __name__, template_folder="templates")


@api.route("/git-pull")
def git_pull():
    """
    Perform a git pull and log the result with an isoformate datetime.
    """
    os.system('echo -e $"$(date -Iseconds)\n$(git pull)" >> logs/gitpull.log')
