import logging
import re
from io import BytesIO
from typing import Iterator
from zipfile import ZipFile

from models.file import File
from models.folder import Folder
from models.repository import Repository
from utils.request import Request

logger = logging.getLogger(__name__)


class RepoScraper:
    IGNORED_FOLDERS = {".vscode"}
    repository_regex = re.compile(r"REPOSITORY_NAME_HEADING")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer ",
    }

    def __init__(self, api_token: str):
        self.session = Request(self.headers)
        self.headers["Authorization"] += api_token

    def get_repository(self, repo_url: str) -> Repository | None:
        # https://api.github.com/repos/home-assistant/core
        logger.info(f"Scraping {repo_url.split('/')[-1]}")
        repo_data = self.session.json_request(repo_url)
        if repo_data:
            default_branch = repo_data["default_branch"]
            html_url = repo_data["html_url"]
            owner_name = repo_data["owner"]["login"]
            last_commit_hash = self._get_last_commit_hash(repo_data['commits_url'])
            contents_folder = self._get_repo_files(owner_name, repo_data["name"], last_commit_hash, html_url)
            repo = Repository(
                repo_data["id"],
                repo_data["name"],
                owner_name,
                html_url,
                repo_url,
                repo_data["language"],
                default_branch,
                contents_folder,
            )
            return repo

    def get_top_repos(self, max_results: int = 0) -> Iterator[Repository]:
        repo_count = 0
        paginate = True
        page = 1
        while paginate:
            url = f"https://github.com/topics/python?page={page}"
            soup = self.session.soup_request(url, {})
            headers = soup.select("article h3")
            repo_anchors = (
                header.find("a", {"data-hydro-click": self.repository_regex})
                for header in headers
            )
            repo_urls = {
                "https://api.github.com/repos" + a["href"] for a in repo_anchors
            }
            if not repo_urls:
                break
            for url in repo_urls:
                yield self.get_repository(url)
                if repo_count and repo_count == max_results:
                    paginate = False
                    break
                repo_count += 1
            page += 1

    def _get_repo_files(
        self, owner_name: str, repo_name: str, commit_sha: str, html_url: str
    ) -> Folder:
        zip_url = f"https://github.com/{owner_name}/{repo_name}/archive/{commit_sha}.zip"
        zip_response = self.session.request(zip_url)
        with ZipFile(BytesIO(zip_response.content)) as zip_file:
            return self._get_folder_from_zip(
                zip_file, html_url, commit_sha
            )

    def _get_folder_from_zip(
        self, zip_file: ZipFile, html_url: str, commit_sha: str
    ) -> Folder:
        """Parses zip file to Folder/File structure"""
        estructure = {}
        for file_name in zip_file.namelist():
            path = file_name.split("/")
            pos = estructure
            for depth, item in enumerate(ele for ele in path if ele):
                is_folder = depth < len(path) - 1
                value = pos.get(item)
                if value is None and is_folder:
                    pos[item] = {}
                elif value is None and not is_folder:
                    # Not extracting unless its a python file
                    data = zip_file.read(file_name) if item.endswith(".py") else None
                    file_url = f"{html_url}/blob/{commit_sha}/{'/'.join(path[1:])}"
                    pos[item] = File(item, file_url, data)
                pos = pos[item]
        return next(iter(self._dict_to_folders(estructure)))

    def _get_last_commit_hash(self, commits_url: str) -> str:
        url = commits_url.replace("{/sha}", "?per_page=1")
        res = self.session.json_request(url=url, headers=self.headers)
        return res[0]['sha']

    def _dict_to_folders(self, estructure: dict) -> list[Folder]:
        """transform dict folder structure to class Folder"""
        folders = []
        for key, item in estructure.items():
            if isinstance(item, dict):
                folder = Folder(key, self._dict_to_folders(item))
                folders.append(folder)
            else:
                folders.append(item)
        return folders
