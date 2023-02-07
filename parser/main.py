from repo_scraper import RepoScraper
from models.call import Call
from repo_parser import RepoParser
import pickle


calls = []
scraper = RepoScraper('Python')
for repo in scraper.get_top_repos(5):
    repo_parser = RepoParser(repo)
    repo_calls = repo_parser.get_repo_calls()
    calls.extend(repo_calls)


with open('pickle', 'wb') as f:
    pickle.dump(calls, f)

with open('pickle', 'rb') as f:
    calls: list[Call] = pickle.load(f)
print()
