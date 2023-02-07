import re
from typing import Iterator

from models.file import File
from models.folder import Folder
from models.repository import Repository
from utils.request import Request


class RepoScraper:
    language: str
    IGNORED_FOLDERS = {".vscode"}
    repository_regex = re.compile(r"REPOSITORY_NAME_HEADING")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer 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",
    }
    file_extensions = {"Python": "py"}

    def __init__(self, language: str):
        self.session = Request(self.headers)
        self.language = language

    def get_repository(self, repo_url: str) -> Repository | None:
        res = self.session.json_request(repo_url)
        if res:
            contents_folder = self._get_repo_files(repo_url)
            repo = Repository(
                res["id"],
                res["name"],
                res["owner"]["login"],
                res["html_url"],
                repo_url,
                res["language"],
                res["default_branch"],
                contents_folder,
            )
            return repo

    def get_top_repos(self, max_results: int = 0) -> Iterator[Repository]:
        repo_count = 0
        paginate = True
        page = 1
        while paginate:
            url = f"https://github.com/topics/{self.language.lower()}?page={page}"
            soup = self.session.soup_request(url, {})
            headers = soup.select("article h3")
            repo_anchors = (
                header.find("a", {"data-hydro-click": self.repository_regex})
                for header in headers
            )
            repo_urls = {
                "https://api.github.com/repos" + a["href"] for a in repo_anchors
            }
            for url in repo_urls:
                yield self.get_repository(url)
                if repo_count and repo_count == max_results:
                    paginate = False
                    break
                repo_count += 1
            else:
                break

    def _get_repo_files(self, repo_url: str) -> Folder:
        folder = self._get_folder_files(f"{repo_url}/contents", repo_url.split("/")[-1])
        text_responses = self.session.threaded_requests(
            {
                file.data_url
                for file in folder.walk(File)
                if file.name.endswith(self._get_file_extension())
            },
            "TEXT",
        )
        for text, url in text_responses:
            file = next(file for file in folder.walk(File) if file.data_url == url)
            file.data = text
        return folder

    def _get_folder_files(
        self, folder_url: str, folder_name: None | str = None
    ) -> Folder:
        """Get all folders with files recursively, uses folder_name for root folder"""
        files = []
        items = self.session.json_request(folder_url)
        for item in items or []:
            if item["type"] == "file" and item["name"].endswith(
                self._get_file_extension()
            ):
                new_file = File(
                    item["name"],
                    item["sha"],
                    item["html_url"],
                    item["url"],
                    item["download_url"],
                    None,
                )
                files.append(new_file)
            elif item["type"] == "dir" and item["name"] not in self.IGNORED_FOLDERS:
                files.append(self._get_folder_files(item["url"]))
        folder_name = folder_name or folder_url.split("?")[0].split("/")[-1]
        return Folder(folder_name, files)

    def _get_file_extension(self) -> str:
        return self._language_to_extension(self.language)

    @classmethod
    def _language_to_extension(cls, language: str) -> str:
        return cls.file_extensions[language]
