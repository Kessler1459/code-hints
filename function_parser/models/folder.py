from dataclasses import dataclass
from function_parser.models.file import File
from typing import TypeVar

FolderType = TypeVar("FolderType", bound="Folder")


@dataclass
class Folder:
    name: str
    files: list[FolderType | File]

    def walk(self, type_: type[FolderType] | type[File]):
        for item in self.files:
            is_folder = isinstance(item, Folder)
            if not is_folder and type_ is File:
                yield item
            elif is_folder and type_ is Folder:
                yield item
            if is_folder:
                yield from item.walk(type_)
