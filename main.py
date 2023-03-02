import logging
import os

from dotenv import load_dotenv

from config import set_logger
from function_parser.db.dynamo import Dynamo
from function_parser.repo_parser import RepoParser
from function_parser.repo_scraper import RepoScraper

# LOGGING
set_logger()
logger = logging.getLogger(__name__)

# ENVS
load_dotenv()
github_token = os.getenv("GITHUBTOKEN")
repo_count = int(os.getenv("REPOCOUNT", 0))
aws_region = os.getenv("AWSREGION")
aws_access_key_id = os.getenv("AWSACCESSKEY")
aws_secret_access_key = os.getenv("AWSSECRETACCESSKEY")
aws_endpoint = os.getenv("AWSENDPOINT")


if __name__ == "__main__":
    if not all((github_token, aws_region, aws_access_key_id, aws_secret_access_key)):
        raise ValueError("Missing environmentals!")

    database = Dynamo(
        aws_region, aws_access_key_id, aws_secret_access_key, aws_endpoint, True
    )
    scraper = RepoScraper(github_token)

    for i, repo in enumerate(scraper.get_top_repos(repo_count), 1):
        repo_parser = RepoParser(repo)
        repo_calls = repo_parser.get_repo_calls()
        database.call_table.write_batch_threaded(repo_calls)
        logging.info(f"{'#'*9} {i} / {repo_count} repositories {'#'*9}")
