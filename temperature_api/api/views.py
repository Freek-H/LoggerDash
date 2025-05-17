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


def get_data_from_stream(pagination, requested_page):

    # TODO: get the requested page from the pagination object, or if no page is given, return the first page.
    return pagination.get_data(requested_page)


@api.route("/streams", methods=["GET", "POST"])
def streams():
    """
    GET: Returns a list of all the streams from which data can be requested.
    POST: Returns JSON containing:
     - the first page of data for the selected stream between the start and end datetimes (inclusive);
     - the JSON object to request next page;
     - metadata.

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

    pagination_id = data.get("paginationId")
    if pagination_id is not None:
        return load_pagination(pagination_id).get_data()

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
    return jsonify(get_data_from_stream(pagination))
