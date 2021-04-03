import requests
from functools import cached_property
from yoink.globals import config
from yoink.contest import Contest
from yoink.utils import Singleton


class Yanker(metaclass=Singleton):
    def __init__(self):
        self.contests = {}

    def prepare_contests(self):
        for entry in self.requested_contest_list:
            contest = Contest(entry)
            self.contests[contest.id] = contest
            if contest.id not in config.contests_meta:
                config.contests_meta[contest.id] = 0

    @staticmethod
    def dump():
        config.dump()

    # dict
    @cached_property
    def requested_contest_list(self):
        r = requests.get("https://codeforces.com/api/contest.list")

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        return r.json()["result"]
