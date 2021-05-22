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
        for entry in self.requested_contest_list:
            contest = Contest(entry)
            self.contests[contest.id] = contest
            contest.download_submissions_info()

    def download_source_codes(self):
        for contest in self.contests.values():
            try:
                contest.download_source_codes()
            finally:
                continue

    def save(self):
        with open(self.config.contests_meta_path, 'w') as fp:
            json.dump({'Contests': list(self.contests.keys())}, fp)

    def is_entry_eligible(self, entry):
        return entry['phase'] in self.config.data['Supported-Phases'] and \
               entry['type'] in self.config.data['Supported-Contest-Formats']

    @staticmethod
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    # dict
    @cached_property
    def requested_contest_list(self):
        r = requests.get('https://codeforces.com/api/contest.list')

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        result = list(filter(lambda x: self.is_entry_eligible(x), r.json()['result']))
        if self.config.data['Max-Contests'] >= 0:
            result = result[:min(self.config.data['Max-Contests'], len(result))]
        print(f'\n======== {len(result)} contests ========')
        if len(result) > 0:
            print('\n*', '\n* '.join(map(lambda x: f'[{x["id"]}] {x["name"]}', result)), '\n')
            time.sleep(self.config.data['Request-Delay'])
        return result
