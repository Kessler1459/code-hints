from dataclasses import dataclass


@dataclass
class File:
    name: str
    web_url: str
    data: None | str
