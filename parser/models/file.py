from dataclasses import dataclass


@dataclass
class File:
    name: str
    sha: str
    web_url: str
    api_url: str
    data_url: str
    data: None | str
