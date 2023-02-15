import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Iterable, Iterator, Literal

from bs4 import BeautifulSoup
from requests import HTTPError, Response, Session

logger = logging.getLogger(__name__)

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
                logger.debug(f"Status {response.status_code} on {url}")
                response.raise_for_status()
                return response
            except HTTPError as ex:
                logger.debug(ex)
                remaining_requests = int(response.headers.get("X-RateLimit-Remaining"))
                if response.status_code == 403 and not remaining_requests:
                    now = time.time()
                    release_timestamp = int(response.headers.get("X-RateLimit-Reset"))
                    remaining_time = release_timestamp - now
                    release_time = datetime.fromtimestamp(release_timestamp)
                    logger.info(
                        f"API limit exceeded waiting until {release_time.strftime('%H:%M:%S')}"
                    )
                    time.sleep(remaining_time + 5)
            except Exception as ex:
                logger.warning(ex)
                logger.warning(f"Waiting {sleep_time}.\nAttempt {attempt} / {max_attempts}")
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
