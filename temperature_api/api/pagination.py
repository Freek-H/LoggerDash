import datetime
import uuid

from constants import DATA_DIR


class Pagination:
    def __init__(self, stream, start_datetime, end_datetime):
        self.file_paths = self.get_file_paths(stream, start_datetime, end_datetime)
        self.id = uuid.uuid4()
        self.expires = 

    def get_file_paths(stream, start_datetime, end_datetime):
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
        return file_paths
