import json
import os
import time
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
        self.meta = {
            'Submissions': {}
        }
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

        # Create working directory if doesn't exist
        if not _ope(self.path):
            _omd(self.path)

        # Deserialize data from JSON
        if _ope(self.meta_path):
            with open(self.meta_path, 'r') as fp:
                self.meta = json.load(fp)

    def download_submissions(self):
        if self.phase != Contest.Phase.FINISHED.value:
            print(f'# [Contest][{self.id}]: Not finished')
            return
        print(f'# [Contest][{self.id}]: Download started')

        cap = config.data['Max-Submissions']
        pointer = 1
        batch = 25000
        while True:
            submissions = self.request_submissions(pointer, batch)
            for entry in submissions:
                # TODO:
                # Refactor
                submission_id = str(entry['id'])
                if submission_id in self.meta['Submissions']:
                    serialized_submission_path = self.get_submission_path(submission_id)
                    if _ope(serialized_submission_path) and \
                            self.meta['Submissions'][submission_id] == Submission.DownloadStatus.FINISHED.value:
                        submission = Submission.deserialize(serialized_submission_path)
                        self.submissions[submission.id] = submission
                        continue

                entry['contestId'] = self.id
                submission = Submission(entry, self)
                if submission.verdict in config.data['Supported-Verdicts']:
                    self.submissions[submission.id] = submission
                    if submission.id not in self.meta['Submissions']:
                        self.meta['Submissions'][submission.id] = Submission.DownloadStatus.NOT_STARTED.value
                    cap -= 1
                    if cap == 0:
                        break
            self.save_meta()

            if len(submissions) < batch or cap == 0:
                break
            pointer += batch

    def download_source_codes(self):
        for submission in self.submissions.values():
            if self.meta['Submissions'][submission.id] != Submission.DownloadStatus.FINISHED.value or \
                    not _ope(self.get_submission_path(submission.id)):
                submission.request_code()
                submission.save()
                self.save_meta()

    def save_meta(self):
        with open(self.meta_path, 'w') as fp:
            json.dump(self.meta, fp, indent=4)

    # Path to the contest directory
    @cached_property
    def path(self):
        return config.combine_path(self.id)

    # Path to the stored meta data
    @cached_property
    def meta_path(self):
        return _opj(self.path, 'meta.json')

    def get_submission_path(self, submission_id):
        return _opj(self.path, 'submissions', f'{submission_id}.json')

    def request_submissions(self, id_from, count):
        print(f'#? [Contest][{self.id}]: Requesting {id_from}-{count} submissions')
        payload = {'contestId': int(self.id), 'from': id_from, 'count': count}
        r = requests.get('https://codeforces.com/api/contest.status', params=payload)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(f'#! [{r.status_code}] REQUEST ERROR')
            time.sleep(config.data['Request-Delay'])
            return

        time.sleep(config.data['Request-Delay'])
        return r.json()['result']
