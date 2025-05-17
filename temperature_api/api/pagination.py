"""
See class docstring.
"""

import csv
import datetime
import uuid

from constants import DATA_DIR, datetime_now_local


class Pagination:
    """
    Enables pagination for the temperature API.
    """

    def __init__(self, stream, start_datetime, end_datetime):
        self.stream = stream
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.all_file_paths = self.get_all_file_paths(
            stream, start_datetime, end_datetime
        )
        self.file_paths_processed = []
        self.id = uuid.uuid4()
        self.expires = datetime_now_local() + datetime.timedelta(hours=1)
        self.current_page = 0
        self.determined_pages = {}
        self.minimum_items_per_page = 10_000

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
        for page_nr in range(requested_page + 1):
            if page_nr in self.determined_pages:
                continue
            items_selected = 0
            self.determined_pages[page_nr] = []
            for file_path in (
                path
                for path in self.all_file_paths
                if path not in self.file_paths_processed
            ):
                # Subtracting one for the header.
                items_selected += open(file_path, encoding="utf-8").readlines() - 1
                self.determined_pages[page_nr].append(file_path)
                self.file_paths_processed.append(file_path)
                if items_selected >= self.minimum_items_per_page:
                    break
        return self.determined_pages[requested_page]

    def get_data(self, requested_page=0):
        """
        Returns a dictionary of lists containing all the present raw data for the paginated stream
        between the start and end datetimes, inclusive, for the requested page.
        If no page is specified, the first one is returned.
        """
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
        return data
