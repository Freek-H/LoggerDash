"""API exposing temperature logging data"""

import csv
from datetime import datetime

from flask import Blueprint, Response, abort, jsonify, request

from constants import DATA_DIR

api = Blueprint("simple_page", __name__, template_folder="templates")


def get_available_streams():
    """
    Returns a list of the streams of data that can be accessed.
    """
    return [item.name for item in DATA_DIR.iterdir() if item.is_dir()]


def get_data_from_stream(stream, start_datetime, end_datetime):
    """
    Returns a dictionary of lists containing all the present raw data for the requested stream
     between the start and end datetimes, inclusive.
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


@api.route("/streams", methods=["GET", "POST"])
def available_streams():
    """
    GET: Returns a list of all the streams from which data can be requested.
    POST: Returns all data for the selected stream between the start and end datetimes (inclusive)
     with the specified granularity.

    Expected application/json:
    {
        "stream": string,
        // Mandatory, allowed values can be requested with GET method
        "datetimeStart": datetime,
        // Optional, default "1900-01-01T00:00:00", has to be in isoformat
        "datetimeEnd": datetime,
        // Optional, default "2999-01-01T00:00:00", has to be in isoformat
    }
    """
    if request.method == "GET":
        return jsonify(get_available_streams())

    data = request.get_json()
    stream = data.get("stream")
    if stream is None:
        return abort(Response("Missing key: stream", 400))
    if stream not in get_available_streams():
        return abort(Response("Invalid stream", 400))

    start_datetime = data.get("datetimeStart", "1900-01-01T00:00:00")
    try:
        start_datetime = datetime.fromisoformat(start_datetime)
    except ValueError:
        return abort(
            Response(
                "Invalid start datetime, please use isoformat date or datetime.", 400
            )
        )

    end_datetime = data.get("datetimeEnd", "2999-01-01T00:00:00")
    try:
        end_datetime = datetime.fromisoformat(end_datetime)
    except ValueError:
        return abort(
            Response(
                "Invalid end datetime, please use isoformat date or datetime.", 400
            )
        )

    print(data)
    return jsonify(get_data_from_stream(stream, start_datetime, end_datetime))
