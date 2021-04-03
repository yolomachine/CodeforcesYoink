import json
import os
import time
from random import randrange

import requests
from enum import unique, auto
from functools import cached_property
from yoink.globals import config
from yoink.submission import Submission
from yoink.utils import AutoName, cc2sc

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


class Contest:
    @unique
    class Phase(AutoName):
        BEFORE = auto()
        CODING = auto()
        PENDING_SYSTEM_TEST = auto()
        SYSTEM_TEST = auto()
        FINISHED = auto()

    @unique
    class Type(AutoName):
        CF = auto()
        IOI = auto()
        ICPC = auto()

    __optional_fields = [
        'preparedBy',
        'websiteUrl',
        'description',
        'difficulty',
        'kind',
        'icpcRegion',
        'country',
        'city',
        'season',
    ]

    def __init__(self, info):
        self.meta = {'Count': 0, 'Submissions': []}
        self.submissions = {}
        self.id = str(info['id'])
        self.name = info['name']
        self.type = info['type']
        self.phase = info['phase']
        self.frozen = info['frozen'] == 'true'
        self.duration_seconds = info['durationSeconds']
        self.start_time_seconds = info['startTimeSeconds']
        self.relative_time_seconds = info['relativeTimeSeconds']

        for key in Contest.__optional_fields:
            if key in info:
                self.__setattr__(cc2sc(key), info[key])

        if self.phase != Contest.Phase.FINISHED.value:
            return

        if not _ope(self.path):
            _omd(self.path)

        if _ope(self.meta_path):
            with open(self.meta_path, 'r') as fp:
                self.meta = json.load(fp)

        config.contests_meta['Contests'].append(self.id)

    def prepare_submissions(self):
        if self.phase != Contest.Phase.FINISHED.value:
            print(f'# [Contest][{self.id}]: Not finished')
            return

        id_from = 1
        count = 25000
        print(f'# [Contest][{self.id}]: Yoinking started')
        while True:
            submissions = self.request_submissions(id_from, count)
            for entry in submissions:
                entry['contestId'] = self.id
                submission = Submission(entry, self)
                self.submissions[submission.id] = submission

            if len(submissions) < count:
                break
            id_from += count

        self.meta['Submissions'] = self.submissions.keys()
        self.meta['Count'] = len(self.submissions)

        for submission in self.submissions.values():
            submission.request_code()

    def dump(self):
        with open(self.meta_path, 'w') as fp:
            json.dump(self.meta, fp, indent=4)
        for submission in self.submissions:
            submission.dump()

    # path to dir
    @cached_property
    def path(self):
        return _opj(config.path, self.id)

    # path to json
    @cached_property
    def meta_path(self):
        return _opj(self.path, 'meta.json')

    def request_submissions(self, id_from, count):
        print(f'#? [Contest][{self.id}]: Trying to request {count} submissions from id {id_from}')
        payload = {'contestId': int(self.id), 'from': id_from, 'count': count}
        r = requests.get('https://codeforces.com/api/contest.status', params=payload)

        interval = randrange(10, 20, 1)
        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            print(f'#! FAIL')
            # In order not to cause mass destruction
            time.sleep(interval)
            return

        print(f'#! OK')
        # In order not to cause mass destruction
        time.sleep(interval)
        return r.json()['result']
