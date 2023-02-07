import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Iterator, Literal

from requests import Response, Session
from bs4 import BeautifulSoup


class Request:
    session: Session
    headers: dict

    def __init__(self, headers: dict):
        self.session = Session()
        self.headers = headers

    def request(
        self, url: str, max_attempts: int = 5, headers: dict | None = None
    ) -> Response | None:
        sleep_time = 10
        headers = headers if headers is not None else self.headers
        for attempt in range(max_attempts):
            try:
                response = self.session.get(url, headers=headers)
                print(f"Status {response.status_code} on {url}")
                response.raise_for_status()
                return response
            except Exception as ex:
                print(ex)
                print(f"Waiting {sleep_time}.\nAttempt {attempt} / {max_attempts}")
                time.sleep(sleep_time)

    def soup_request(
        self, url: str, headers: dict | None = None
    ) -> BeautifulSoup | None:
        response = self.request(url, headers=headers)
        if response:
            return BeautifulSoup(response.text, "lxml")

    def json_request(self, url: str, headers: dict | None = None) -> dict | None:
        response = self.request(url, headers=headers)
        if response:
            return response.json()

    def text_request(self, url: str, headers: dict | None = None) -> str | None:
        response = self.request(url, headers=headers)
        if response:
            return response.text

    def threaded_requests(
        self,
        urls: Iterable[str],
        return_type: Literal["JSON", "TEXT", "RESPONSE"] = "RESPONSE",
    ) -> Iterator[
        tuple[str, str] | tuple[dict, str] | tuple[Response, str] | tuple[None, str]
    ]:
        if return_type == "JSON":
            request_method = self.json_request
        elif return_type == "TEXT":
            request_method = self.text_request
        else:
            request_method = self.request
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(request_method, url): url for url in urls}
            for future in as_completed(futures):
                try:
                    yield future.result(), futures[future]
                except Exception:
                    raise
