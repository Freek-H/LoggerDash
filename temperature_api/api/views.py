"""API exposing temperature logging data"""

import csv
from datetime import datetime

from flask import Blueprint, Response, abort, jsonify

from constants import DATA_DIR

api = Blueprint("simple_page", __name__, template_folder="templates")


def get_available_streams():
    """
    Returns a list of the streams of data that can be accessed.
    """
    return [item.name for item in DATA_DIR.iterdir() if item.is_dir()]


def get_data_from_stream(stream, start_datetime, end_datetime):
    """
    Returns a dictionary of lists containing all the present data for the requested stream between
     the start and end datetimes, inclusive.
    """
    file_paths = []
    for file_path in (DATA_DIR / stream).glob("*.csv"):
        file_datetime = datetime.fromisoformat(
            file_path.name.removesuffix(file_path.suffix)
            .removeprefix(f"{stream}_")
            .replace(".", ":")
        )
        if (
            start_datetime.replace(minute=0, second=0, microsecond=0)
            <= file_datetime
            <= end_datetime.replace(minute=0, second=0, microsecond=0)
        ):
            file_paths.append(file_path)
    data = {}
    for file_path in file_paths:
        with open(file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (
                    start_datetime
                    <= datetime.fromisoformat(row["Datetime"])
                    <= end_datetime
                ):
                    for key, value in row.items():
                        if key not in data:
                            data[key] = []
                        data[key].append(value)
    return data


@api.route("/streams")
def available_streams():
    """
    Returns a list of all the streams from which data can be requested.
    """
    return jsonify(get_available_streams())


@api.route("/stream/<stream>/<start_datetime>/<end_datetime>")
def data_for_stream(stream, start_datetime, end_datetime):
    """
    Returns all data for the requested stream between the start and end datetimes, inclusive.
    """
    if stream not in get_available_streams():
        return abort(Response("Invalid stream", 400))
    try:
        start_datetime = datetime.fromisoformat(start_datetime)
    except ValueError:
        return abort(
            Response("Invalid start datetime, please use isoformat date or datetime.")
        )
    try:
        end_datetime = datetime.fromisoformat(end_datetime)
    except ValueError:
        return abort(
            Response("Invalid end datetime, please use isoformat date or datetime.")
        )

    return jsonify(get_data_from_stream(stream, start_datetime, end_datetime))
