"""
See class docstring.
"""

import csv
import datetime
import json
import sqlite3
from pathlib import Path
from typing import List, Union

import uuid6

from constants import APP_DATA_DIR, DATA_DIR, datetime_now_local

PAGINATION_DATABASE = APP_DATA_DIR / "pagination.sqlite3"

with sqlite3.connect(PAGINATION_DATABASE) as _connection:
    _cursor = _connection.cursor()
    _cursor.execute(
        "CREATE TABLE IF NOT EXISTS [pagination] ([paginationId], [pagination])"
    )
    _connection.commit()
    _cursor.close()


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
    ) -> None:
        if serialized_pagination is not None:
            self.deserialize(serialized_pagination)
            return
        self.id = str(uuid6.uuid7())
        self.expires = datetime_now_local() + datetime.timedelta(hours=1)
        self.stream = stream
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.minimum_items_per_page = minimum_items_per_page
        all_file_paths = self.get_all_file_paths()
        self.data = (
            [{"path": path, "page": None} for path in all_file_paths]
            if all_file_paths
            else []
        )

    def to_dict(self) -> dict:
        """
        Returns a dicitonary of the pagination object.
        The contents are JSON serializable.
        """
        return {
            "pagination": {
                "id": self.id,
                "expires": self.expires.isoformat(),
            },
            "data": [
                {
                    "path": str(item["path"].relative_to(DATA_DIR)),
                    "page": item["page"],
                }
                for item in self.data
            ],
            "metadata": {
                "stream": self.stream,
                "startDatetime": self.start_datetime.isoformat(),
                "endDatetime": self.end_datetime.isoformat(),
                "minumumItemsPerPage": self.minimum_items_per_page,
            },
        }

    def serialize(self) -> str:
        """
        Returns a serialized version of the object in the form of a JSON string.
        """
        return json.dumps(self.to_dict())

    def deserialize(self, serialized_pagination: str) -> None:
        """
        Deserializes a pagination object from a JSON string.
        """
        dictionary_ = json.loads(serialized_pagination)
        self.id = dictionary_["pagination"]["id"]
        self.expires = datetime.datetime.fromisoformat(
            dictionary_["pagination"]["expires"]
        )
        self.data = [
            {"path": DATA_DIR / item["path"], "page": item["page"]}
            for item in dictionary_["data"]
        ]
        self.stream = dictionary_["metadata"]["stream"]
        self.start_datetime = datetime.datetime.fromisoformat(
            dictionary_["metadata"]["startDatetime"]
        )
        self.end_datetime = datetime.datetime.fromisoformat(
            dictionary_["metadata"]["endDatetime"]
        )
        self.minimum_items_per_page = dictionary_["metadata"]["minumumItemsPerPage"]

    def dump(self) -> None:
        """
        Dump a pagination object to the pagination database.
        INSERT if it doesn't yet exist.
        UPDATE if it does.
        """
        with sqlite3.connect(PAGINATION_DATABASE) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM [pagination] WHERE [paginationId] = ?",
                (self.id,),
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE [pagination] SET [pagination] = ? WHERE [paginationId] = ?",
                    (
                        self.serialize(),
                        self.id,
                    ),
                )
            else:
                cursor.execute(
                    "INSERT INTO [pagination] ([paginationId], [pagination]) VALUES (?, ?)",
                    (
                        self.id,
                        self.serialize(),
                    ),
                )
            connection.commit()
            cursor.close()

    def is_expired(self) -> bool:
        """
        Returns whether pagination is expired.
        """
        return self.expires < datetime_now_local()

    def get_all_file_paths(self) -> List[Path]:
        """
        Get all files for the selected stream that are timestamped in between the start and end
         datetimes.
        """

        def file_datetime_from_file_path(file_path):
            return datetime.datetime.fromisoformat(
                file_path.name.removesuffix(file_path.suffix)
                .removeprefix(f"{self.stream}_")
                .replace(".", ":")
            )

        file_paths = []
        for file_path in (DATA_DIR / self.stream).glob("*.csv"):
            file_datetime = file_datetime_from_file_path(file_path)
            if (
                self.start_datetime.replace(minute=0, second=0, microsecond=0)
                <= file_datetime
                <= self.end_datetime.replace(minute=0, second=0, microsecond=0)
            ):
                file_paths.append(file_path)

        file_paths = sorted(file_paths, key=file_datetime_from_file_path)
        # Here we check if the last file, whether it actually has a row of data for us that we can
        #  return to the user.
        with open(file_paths[-1], encoding="utf-8") as file:
            reader = csv.DictReader(file)
            # We don't expect to ever not get a row back, as files should never be empty/only have
            #  a header, but this excepts that case.
            try:
                row = next(reader)
            except StopIteration:
                row = None
            if row is None or not (
                self.start_datetime
                <= datetime.datetime.fromisoformat(row["Datetime"])
                <= self.end_datetime
            ):
                file_paths.pop()
        return file_paths

    def get_file_paths_for_page(self, requested_page=0) -> Union[dict, List[Path]]:
        """
        Assigns files to pages based on the minimum number of items per page set and the number of
         lines per files.
        """
        if requested_page < 0:
            return {
                "message": f"Invalid page number {requested_page}. \
Page number needs to be 0 or greater."
            }
        for page_nr in range(requested_page + 1):
            if page_nr in (item["page"] for item in self.data):
                continue
            items_selected = 0
            for item in self.data:
                if item["page"] is not None:
                    continue
                # Subtracting one for the header.
                items_selected += (
                    len(open(item["path"], encoding="utf-8").readlines()) - 1
                )
                item["page"] = page_nr
                if items_selected >= self.minimum_items_per_page:
                    break
        available_page_numbers = [item["page"] for item in self.data]
        if requested_page not in available_page_numbers:
            return {
                "message": f"Invalid page number, {requested_page} is greater than the number of \
pages available ({max(available_page_numbers)})."
            }
        return [item["path"] for item in self.data if item["page"] == requested_page]

    def get_data(self, requested_page=0) -> dict:
        """
        Returns a dictionary of lists containing all the present raw data for the paginated stream
        between the start and end datetimes, inclusive, for the requested page.
        If no page is specified, the first one is returned.
        """
        if not self.data:
            return {
                "message": f"No valid files found for stream={self.stream} and datetime range of \
{self.start_datetime.isoformat()} to {self.end_datetime.isoformat()}"
            }
        if self.is_expired():
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
        if not isinstance(file_paths, list):
            return file_paths
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
        return_value = self.to_dict()
        return_value["data"] = data
        return_value["metadata"]["page"] = requested_page
        if any(item["page"] is None for item in self.data) or requested_page < max(
            item["page"] for item in self.data
        ):
            return_value["bodyNextPage"] = {
                "paginationId": self.id,
                "page": requested_page + 1,
            }
        return return_value


def load_pagination(pagination_id: str) -> Union[dict, Pagination]:
    """
    Loads a pagination object from the pagination database if it exists.
    """
    with sqlite3.connect(PAGINATION_DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(
            "SELECT [pagination] FROM [pagination] WHERE [paginationId] = ?",
            (pagination_id,),
        )
        data = cursor.fetchone()
        cursor.close()
    if not data:
        return {"message": f"No pagination found for ID {pagination_id}"}
    return Pagination(serialized_pagination=data["pagination"])


def delete_expired() -> None:
    """
    Deletes the expired paginations from the database.
    """
    with sqlite3.connect(PAGINATION_DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM [pagination]")
        for row in cursor.fetchall():
            pagination = Pagination(serialized_pagination=row["pagination"])
            if pagination.is_expired():
                cursor.execute(
                    "DELETE FROM [pagination] WHERE [paginationId] = ?",
                    (row["paginationId"],),
                )
                print(f"Deleted {pagination.id=}, expired {pagination.expires}")
        connection.commit()
        cursor.close()
