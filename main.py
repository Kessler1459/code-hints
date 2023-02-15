import logging
import os

from config import set_logger
from function_parser.db.dynamo import Dynamo
from function_parser.repo_parser import RepoParser
from function_parser.repo_scraper import RepoScraper

# LOGGING
set_logger()
logger = logging.getLogger(__name__)

# ENVS
github_token = os.getenv("GITHUBTOKEN")

if __name__ == "__main__":
    database = Dynamo()
    scraper = RepoScraper(github_token)

    REPOCOUNT = 3
    for i, repo in enumerate(scraper.get_top_repos(REPOCOUNT), 1):
        # TODO SEGUNDA TABLA CON REPOS PARA EVITAR REPETIRLOS
        repo_parser = RepoParser(repo)
        repo_calls = repo_parser.get_repo_calls()
        database.call_table.write_batch(repo_calls)
        logging.info(f"{'#'*6} {i} / {REPOCOUNT} repositories {'#'*6}")
