from dataclasses import dataclass

from models.file import File


@dataclass
class Call:
    path: str
    line_number: int
    file: File
