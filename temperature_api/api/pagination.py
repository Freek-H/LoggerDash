"""
See class docstring.
"""

import csv
import datetime
import json
import sqlite3

import uuid6

from constants import APP_DATA_DIR, DATA_DIR, datetime_now_local

PAGINATION_DATABASE = APP_DATA_DIR / "pagination.sqlite3"

if not PAGINATION_DATABASE.exists():
    CONNECTION = sqlite3.connect(PAGINATION_DATABASE)
    CONNECTION.close()


class Pagination:
    """
    Enables pagination for the temperature API.
    """

    def __init__(
        self,
        stream=None,
        start_datetime=None,
        end_datetime=None,
        minimum_items_per_page=10_000,
        serialized_pagination=None,
    ):
        if (
            stream is None
            and start_datetime is None
            and end_datetime is None
            and serialized_pagination is not None
        ):
            self.deserialize(serialized_pagination)
            return
        self.id = uuid6.uuid7()
        self.expires = datetime_now_local() + datetime.timedelta(hours=1)
        self.data = [
            {"path": path, "page": None}
            for path in self.get_all_file_paths(stream, start_datetime, end_datetime)
        ]
        self.stream = stream
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.minimum_items_per_page = minimum_items_per_page

    def serialize(self):
        """
        Returns a serialized version of the object in the form of a JSON string.
        """
        return json.dumps(
            {
                "id": self.id,
                "expires": self.expires.isoformat(),
                "data": [
                    {"path": item["path"].relative_to(DATA_DIR), "page": item["page"]}
                    for item in self.data
                ],
                "metadata": {
                    "stream": self.stream,
                    "startDatetime": self.start_datetime.isoformat(),
                    "endDatetime": self.end_datetime.isoformat(),
                    "minumumItemsPerPage": self.minimum_items_per_page,
                },
            }
        )

    def deserialize(self, serialized_pagination: str):
        """
        Deserializes a pagination object from a JSON string.
        """
        dictionary_ = json.loads(serialized_pagination)
        self.id = dictionary_["id"]
        self.expires = dictionary_["expires"]
        self.data = [
            {"path": DATA_DIR / item["path"], "page": item["page"]}
            for item in dictionary_
        ]
        self.stream = dictionary_["metadata"]["stream"]
        self.start_datetime = dictionary_["metadata"]["startDatetime"]
        self.end_datetime = dictionary_["metadata"]["endDatetime"]
        self.minimum_items_per_page = dictionary_["metadata"]["minimumItemsPerPage"]

    def dump(self):
        """
        Dump a pagination object to the pagination database.
        INSERT if it doesn't yet exist.
        UPDATE if it does.
        """
        with sqlite3.connect(
            PAGINATION_DATABASE
        ) as connection, sqlite3.Row as connection.row_factory, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM [pagination] WHERE [paginationId] = ?",
                self.id,
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE [pagination] SET [pagination] = ? WHERE [paginationId] = ?",
                    self.serialize(),
                    self.id,
                )
            else:
                cursor.execute(
                    "INSERT INTO [pagination] ([paginationId], [pagination]) VALUES (?, ?)",
                    self.id,
                    self.serialize(),
                )
            connection.commit()

    def get_all_file_paths(self, stream, start_datetime, end_datetime):
        """
        Get all files for the selected stream that are timestamped in between the start and end
         datetimes.
        """
        file_paths = []
        for file_path in (DATA_DIR / stream).glob("*.csv"):
            file_datetime = datetime.datetime.fromisoformat(
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
        return file_paths

    def get_file_paths_for_page(self, requested_page=0):
        """
        Assigns files to pages based on the minimum number of items per page set and the number of
         lines per files.
        """
        # TODO: edge-case, higher page number than required pages
        for page_nr in range(requested_page + 1):
            if page_nr in (item["page"] for item in self.data):
                continue
            items_selected = 0
            for item in self.data:
                if item["page"] is not None:
                    continue
                # Subtracting one for the header.
                items_selected += open(item["path"], encoding="utf-8").readlines() - 1
                item["page"] = page_nr
                if items_selected >= self.minimum_items_per_page:
                    break
        return [item["path"] for item in self.data if item["page"] == requested_page]

    def get_data(self, requested_page=0):
        """
        Returns a dictionary of lists containing all the present raw data for the paginated stream
        between the start and end datetimes, inclusive, for the requested page.
        If no page is specified, the first one is returned.
        """
        if self.expires > datetime_now_local():
            example_data = json.dumps(
                {
                    "stream": self.stream,
                    "startDatetime": self.start_datetime.isoformat(),
                    "endDatetime": self.end_datetime.isoformat(),
                    "minimumItemsPerPage": self.minimum_items_per_page,
                },
                indent=4,
            )
            return {
                "message": f"This pagination ID has expired since {self.expires.isoformat()}. \
Please send a fresh request. \
Based on the data for this pagination ID that POST request would use the data: {example_data}"
            }
        self.expires = datetime_now_local() + datetime.timedelta(days=1)
        file_paths = self.get_file_paths_for_page(requested_page)
        data = {}
        for file_path in file_paths:
            with open(file_path, encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if (
                        self.start_datetime
                        <= datetime.datetime.fromisoformat(row["Datetime"])
                        <= self.end_datetime
                    ):
                        for key, value in row.items():
                            if key not in data:
                                data[key] = []
                            data[key].append(value)
        self.dump()
        return data


def load_pagination(pagination_id: str):
    """
    Loads a pagination object from the pagination database if it exists.
    """
    with sqlite3.connect(
        PAGINATION_DATABASE
    ) as connection, sqlite3.Row as connection.row_factory, connection.cursor() as cursor:
        cursor.execute(
            "SELECT [pagination] FROM [pagination] WHERE [paginationId] = ?",
            pagination_id,
        )
        data = cursor.fetchone()
    if not data:
        return {"message": f"No pagination found for ID {pagination_id}"}
    return Pagination(serialized_pagination=data["pagination"])
