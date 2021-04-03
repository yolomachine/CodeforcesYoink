import time

import requests
from functools import cached_property
from yoink.globals import config
from yoink.contest import Contest
from yoink.utils import Singleton


class Yanker(metaclass=Singleton):
    def __init__(self):
        self.contests = {}

    def prepare_contests(self, count=-1):
        r = range(len(self.requested_contest_list) if count == -1 else count)
        for i in r:
            entry = self.requested_contest_list[i]
            contest = Contest(entry)
            contest.prepare_submissions()
            self.contests[contest.id] = contest

    def dump(self):
        config.handles_meta['Count'] = len(config.handles_meta['Handles'])
        config.contests_meta['Count'] = len(config.contests_meta['Contests'])
        config.dump()
        for contest in self.contests.values():
            contest.dump()

    # dict
    @cached_property
    def requested_contest_list(self):
        r = requests.get('https://codeforces.com/api/contest.list')

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        # In order not to cause mass destruction
        time.sleep(5)
        return r.json()['result']
