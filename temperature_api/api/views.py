"""API exposing temperature logging data"""

from datetime import datetime

from flask import Blueprint, Response, abort, jsonify, request

from constants import DATA_DIR
from temperature_api.api.pagination import Pagination, load_pagination

api = Blueprint("simple_page", __name__, template_folder="templates")

# TODO: Endpoint/other way to request max number of pages expected for a stream?
# TODO: Bug where if the end datetime is set to a whole hour an empty last page is generated.
# TODO: Serve data sorted by filename. DONE


def get_available_streams():
    """
    Returns a list of the streams of data that can be accessed.
    """
    return [item.name for item in DATA_DIR.iterdir() if item.is_dir()]


@api.route("/streams", methods=["GET", "POST"])
def streams():
    """
    GET: Returns a list of all the streams from which data can be requested.
    POST: Returns JSON containing:
     - the first page of data for the selected stream between the start and end datetimes
        (inclusive);
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
        "minimumItemsPerPage": int,
        // Optional, default 10_000
        "pagination_id": UUIDv7,
        // Optional, used in pagination, will be part of the response if more data is requested
        //  than fits on one page.
        "page": int,
        // Optional, used in pagination, will be part of the response if more data is requested
        //  than fits on one page.
    }
    """
    if request.method == "GET":
        return jsonify(get_available_streams())

    data = request.get_json()

    try:
        page_number = int(data.get("page", 0))
    except ValueError:
        return abort(Response(f"Invalid value for page: {data.get('page')}", 400))

    pagination_id = data.get("paginationId")
    if pagination_id is not None:
        pagination = load_pagination(pagination_id)
        if not isinstance(pagination, Pagination):
            return abort(Response(pagination["message"], 404))
        pageinated_data = pagination.get_data(requested_page=page_number)
        if "message" in pageinated_data:
            return abort(Response(pageinated_data["message"], 400))
        return pageinated_data

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

    minimum_items_per_page = data.get("minimumItemsPerPage", 10_000)
    pagination = Pagination(
        stream=stream,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        minimum_items_per_page=minimum_items_per_page,
    )

    print(data)
    pageinated_data = pagination.get_data(requested_page=page_number)
    if "message" in pageinated_data:
        return abort(Response(pageinated_data["message"], 400))
    return jsonify(pagination.get_data(requested_page=page_number))
