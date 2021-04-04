import time
import requests
from functools import cached_property
from yoink.globals import config
from yoink.contest import Contest
from yoink.utils import Singleton


class Yanker(metaclass=Singleton):
    def __init__(self):
        self.contests = {}

    def download_contests(self):
        i = 0
        count = len(self.requested_contest_list) if config.data['Max-Contests'] == -1 else config.data['Max-Contests']
        while i < count and i < len(self.requested_contest_list):
            entry = self.requested_contest_list[i]
            contest = Contest(entry)
            if contest.phase in config.data['Supported-Phases']:
                i += 1
                contest.download_submissions()
                self.contests[contest.id] = contest

    # dict
    @cached_property
    def requested_contest_list(self):
        r = requests.get('https://codeforces.com/api/contest.list')

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        time.sleep(config.data['Request-Delay'])
        return r.json()['result']
