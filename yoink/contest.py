import json
import time
import requests
from tqdm import tqdm
from functools import cached_property, lru_cache
from yoink.submission import Submission
from yoink.utils import cc2sc, Config, OPE, OMD


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

    @staticmethod
    def serialize(**kwargs):
        instance = kwargs.get('instance', None)
        if not instance:
            return {}

        submissions = {}
        for submission_instance in instance.submissions.values():
            submissions[submission_instance.id] = Submission.serialize(instance=submission_instance)

        # TODO: don't serialize empty fields.
        return \
            {
                'Id': instance.id,
                'Name': instance.name,
                'Type': instance.type,
                'Phase': instance.phase,
                'Frozen': instance.frozen,
                'Duration': instance.duration_seconds,
                'Start-Time': instance.start_time_seconds,
                'Relative-Time': instance.relative_time_seconds,
                'Submissions': submissions,
            }

    @staticmethod
    def deserialize(**kwargs):
        string = kwargs.get('string', None)
        path = kwargs.get('path', None)
        if string:
            data = json.loads(string)
        elif path:
            with open(path, 'r') as fp:
                data = json.load(fp)
        else:
            return None

        submissions = {}
        for serialized_submission in data['Submissions'].values():
            submission = Submission.deserialize(string=json.dumps(serialized_submission))
            submissions[submission.id] = submission

        # TODO: check if key is present before accessing it.
        return Contest(submissions=submissions,
                       info={
                            'id': data['Id'],
                            'name': data['Name'],
                            'type': data['Type'],
                            'phase': data['Phase'],
                            'frozen': data['Frozen'] == 'True',
                            'durationSeconds': data['Duration'],
                            'startTimeSeconds': data['Start-Time'],
                            'relativeTimeSeconds': data['Relative-Time'],
                       })

    @staticmethod
    def get_path(contest_id, **kwargs):
        if not contest_id:
            return None

        path = [str(contest_id)]
        if kwargs.get('meta', False):
            path = [*path, 'meta.json']
        return Config().combine_path(*path)

    def __init__(self, *args, **kwargs):
        self.id = int()
        self.name = str()
        self.type = str()
        self.phase = str()
        self.frozen = False
        self.duration_seconds = int()
        self.start_time_seconds = int()
        self.relative_time_seconds = int()
        self.submissions = kwargs.get('submissions', {})
        if kwargs.get('info', None):
            self.__sync(kwargs['info'])
        if kwargs.get('download', False):
            self.__download_data()

    def download_source_code(self):
        for submission in tqdm(self.submissions,
                               total=len(self.submissions),
                               position=0,
                               leave=True,
                               desc='Contests'):
            self.submissions[submission.id].download_status = submission.download_source_code()
            self.__dump()

    def __sync(self, info):
        self.id = info['id']
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

    def __ensure_directories(self):
        path = Contest.get_path(self.id)
        if not OPE(path):
            OMD(path)

    def __download_data(self):
        if len(self.submissions) == 0:
            for raw_submission in self.__eligible_raw_submissions:
                submission_id = raw_submission['id']
                self.submissions[submission_id] = Submission(download=False,
                                                             contest_id=self.id,
                                                             info=raw_submission)
            self.__dump()

    def __dump(self):
        self.__ensure_directories()
        with open(Contest.get_path(self.id, meta=True), 'w') as fp:
            json.dump(Contest.serialize(instance=self), fp, indent=4)

    @staticmethod
    def __is_eligible(raw_submission):
        try:
            return \
                raw_submission['verdict'] in Config()['Supported-Verdicts'] \
                and (raw_submission['programmingLanguage'] in Config()['Supported-Languages'] or
                     len(Config()['Supported-Languages']) == 0)
        except:
            return False

    @cached_property
    def __eligible_raw_submissions(self):
        result = []
        current_index = 1
        batch_size = 20000
        max_submissions = Config()['Max-Submissions']
        progress_bar = None
        if max_submissions > 0:
            progress_bar = tqdm(total=max_submissions,
                                position=0,
                                leave=True,
                                desc=f'\t[{self.id}][Not found] Downloading submissions',
                                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]')
        while len(result) < max_submissions or max_submissions == -1:
            raw_submissions = self.__request_raw_submissions(self.id, current_index, batch_size)
            if len(raw_submissions) == 0:
                break

            raw_submissions = self.__filter_raw_submissions(raw_submissions,
                                                            apply_config_constraints=True)
            for submission in raw_submissions:
                result.append(submission)
                progress_bar.update()

            current_index += batch_size

        if progress_bar:
            progress_bar.update(min(0, max_submissions - progress_bar.last_print_n))
            progress_bar.close()
        return result

    def __filter_raw_submissions(self, *args, **kwargs):
        data = args[0]
        if not isinstance(data, list):
            data = list(data)

        result = list(filter(lambda x: Contest.__is_eligible(x), data))

        if kwargs.get('apply_config_constraints', False):
            max_submissions = Config()['Max-Submissions']
            if max_submissions >= 0:
                result = result[:min(max_submissions, len(result))]

        return result

    @lru_cache
    def __request_raw_submissions(self, contest_id, start, count):
        payload = {'contestId': contest_id, 'from': start, 'count': count}
        r = requests.get('https://codeforces.com/api/contest.status',
                         # headers=Config()['GET-Headers'],
                         # allow_redirects=False,
                         params=payload)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            time.sleep(Config()['Request-Delay'])
            return []

        time.sleep(Config()['Request-Delay'])
        return r.json()['result']
