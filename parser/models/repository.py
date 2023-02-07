from dataclasses import dataclass
from models.folder import Folder


@dataclass()
class Repository:
    id: int
    name: str
    owner: str
    web_url: str
    api_url: str
    language: str
    default_branch: str
    directory: Folder
