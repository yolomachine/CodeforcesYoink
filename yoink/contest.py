import json
import os
import time
import requests
import yoink.enums as enums
from functools import cached_property
from yoink.submission import Submission
from yoink.utils import cc2sc, Config

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


class Contest:
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
        self.config = Config()
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

        if not _ope(_opj(self.path, 'submissions')):
            _omd(_opj(self.path, 'submissions'))

        # Deserialize data from JSON
        if _ope(self.meta_path):
            with open(self.meta_path, 'r') as fp:
                self.meta = json.load(fp)

    def download_submissions_info(self):
        if self.phase != enums.Phase.FINISHED.value:
            print(f'# [Contest][{self.id}]: Not finished')
            return
        print(f'# [Contest][{self.id}]: Getting raw submissions\' info')

        cap = self.config.data['Max-Submissions']
        pointer = 1
        batch = 25000
        while True:
            submissions = self.request_submissions(pointer, batch)
            if len(submissions) > 0:
                print(f'Received {len(submissions)} submissions')
            counter = 0
            for entry in submissions:
                # TODO:
                # Refactor
                submission_id = str(entry['id'])
                if submission_id in self.meta['Submissions']:
                    serialized_submission_path = self.get_submission_path(submission_id)
                    if _ope(serialized_submission_path) and \
                            self.meta['Submissions'][submission_id] == enums.DownloadStatus.FINISHED.value:
                        submission = Submission.deserialize(serialized_submission_path)
                        self.submissions[submission.id] = submission
                        counter += 1
                        continue

                entry['contestId'] = self.id
                submission = Submission(entry, self)
                if submission.verdict in self.config.data['Supported-Verdicts'] and (
                        len(self.config.data['Supported-Languages']) == 0 or
                        submission.language in self.config.data['Supported-Languages']
                ):
                    self.submissions[submission.id] = submission
                    if submission.id not in self.meta['Submissions']:
                        self.meta['Submissions'][submission.id] = enums.DownloadStatus.NOT_STARTED.value
                    counter += 1
                    cap -= 1
                    if cap == 0:
                        break
            print(f'Approved {counter} submissions')
            self.save_meta()

            if len(submissions) < batch or cap == 0:
                break
            pointer += batch

    def download_source_codes(self):
        if self.phase != enums.Phase.FINISHED.value:
            print(f'# [Contest][{self.id}]: Not finished')
            return
        if len(self.submissions) == 0:
            print(f'# [Contest][{self.id}]: No submissions\' info stored, download it first')
            return
        for submission in self.submissions.values():
            if self.meta['Submissions'][submission.id] != enums.DownloadStatus.FINISHED.value or \
                    not _ope(self.get_submission_path(submission.id)):
                if submission.request_code():
                    submission.save()
                self.save_meta()

    def save_meta(self):
        with open(self.meta_path, 'w') as fp:
            json.dump(self.meta, fp, indent=4)

    # Path to the contest directory
    @cached_property
    def path(self):
        return self.config.combine_path(self.id)

    # Path to the stored meta data
    @cached_property
    def meta_path(self):
        return _opj(self.path, 'meta.json')

    def get_submission_path(self, submission_id):
        return _opj(self.path, 'submissions', f'{submission_id}.json')

    def request_submissions(self, id_from, count):
        print(f'#? [Contest][{self.id}]: Requesting {id_from}-{id_from + count - 1} submissions')
        payload = {'contestId': int(self.id), 'from': id_from, 'count': count}
        r = requests.get('https://codeforces.com/api/contest.status', params=payload)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(f'#! [{r.status_code}] REQUEST ERROR')
            time.sleep(self.config.data['Request-Delay'])
            return

        time.sleep(self.config.data['Request-Delay'])
        return r.json()['result']
