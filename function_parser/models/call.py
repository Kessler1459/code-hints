import time
from dataclasses import dataclass
from hashlib import md5

from .file import File


@dataclass
class Call:
    id: str
    path: str
    line_number: int
    file: File

    def __init__(self, path: str, line_number: int, file: File) -> None:
        unique_id = f"{path}{file.web_url}{line_number}{time.time()}"
        self.id = md5(unique_id.encode("utf-8")).hexdigest()
        self.path = path
        self.line_number = line_number
        self.file = file

    def __eq__(self, __o: object) -> bool:
        return self.id == __o.id

    def __hash__(self) -> int:
        return hash(self.id)