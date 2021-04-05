import json
import time
import requests
from functools import cached_property
from yoink.contest import Contest
from yoink.utils import Singleton, Config


class Yanker(metaclass=Singleton):
    def __init__(self):
        self.config = Config()
        self.contests = {}

    def download_contests(self):
        i = 0
        count = len(self.requested_contest_list) if self.config.data['Max-Contests'] == -1 else self.config.data['Max-Contests']
        while count > 0 and i < len(self.requested_contest_list):
            entry = self.requested_contest_list[i]
            if entry['phase'] in self.config.data['Supported-Phases'] and \
                    entry['type'] in self.config.data['Allowed-Contest-Formats']:
                count -= 1
                contest = Contest(entry)
                self.contests[contest.id] = contest
                contest.download_submissions_info()
            i += 1

    def download_source_codes(self):
        for contest in self.contests.values():
            try:
                contest.download_source_codes()
            finally:
                continue

    def save(self):
        with open(self.config.contests_meta_path, 'w') as fp:
            json.dump({'Contests': list(self.contests.keys())}, fp)

    # dict
    @cached_property
    def requested_contest_list(self):
        r = requests.get('https://codeforces.com/api/contest.list')

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        time.sleep(self.config.data['Request-Delay'])
        return r.json()['result']
