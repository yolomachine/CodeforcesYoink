import json
import time
import requests
import yoink.enums as enums
from yoink.utils import Config, OPE, OMD
from yoink.utils import reset_timeout_counter, check_for_redirecting, check_for_status, get_html_content


class Submission:
    @staticmethod
    def serialize(**kwargs):
        instance = kwargs.get('instance', None)
        if not instance:
            return {}

        # TODO: don't serialize empty fields.
        return \
            {
                'Id': instance.id,
                'Download-Status': instance.download_status,
                'Contest-Id': instance.contest_id,
                'Tags': instance.tags,
                'Language': instance.language,
                'Verdict': instance.verdict,
                'Authors': instance.handles,
                'Time-Consumed': instance.time_consumed_millis,
                'Memory-Consumed': instance.memory_consumed_bytes
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

        # TODO: check if key is present before accessing it.
        return Submission(contest_id=data['Contest-Id'],
                          download_status=data['Download-Status'],
                          info={
                              'id': data['Id'],
                              'problem': {'tags': data['Tags']},
                              'programmingLanguage': data['Language'],
                              'verdict': data['Verdict'],
                              'author': {'members': [{'handle': h for h in data['Authors']}]},
                              'timeConsumedMillis': data['Time-Consumed'],
                              'memoryConsumedBytes': data['Memory-Consumed']
                          })

    @staticmethod
    def get_code_path(submission_id, contest_id, language):
        path = [contest_id, language, submission_id]
        if not any(path):
            return str()
        return Config().combine_path(*path)

    def __init__(self, *args, **kwargs):
        self.id = int()
        self.contest_id = kwargs.get('contest_id', int())
        self.time_consumed_millis = int()
        self.memory_consumed_bytes = int()
        self.handles = list()
        self.tags = list()
        self.language = str()
        self.verdict = enums.Verdict.FAILED.value
        self.download_status = kwargs.get('download_status',
                                          enums.DownloadStatus.NOT_STARTED.value)
        if kwargs.get('info', None):
            self.__sync(kwargs['info'])
        if kwargs.get('download', False):
            self.download_source_code()

    def __sync(self, info):
        self.id = info['id']
        self.time_consumed_millis = info['timeConsumedMillis']
        self.memory_consumed_bytes = info['memoryConsumedBytes']
        self.handles = [member['handle'] for member in info['author']['members']]
        self.tags = [tag for tag in info['problem']['tags']]
        self.language = info['programmingLanguage']
        self.verdict = info.get('verdict', enums.Verdict.FAILED.value)

    def __ensure_directories(self):
        path = Submission.get_code_path(self.id, self.contest_id, self.language)
        if not OPE(path):
            OMD(path)

    def download_source_code(self):
        r = requests.get(
            f'https://codeforces.com/contest/{self.contest_id}/submission/{self.id}',
            headers=Config()['GET-Headers'],
            allow_redirects=False
        )
        time.sleep(Config()['Request-Delay'])

        if check_for_redirecting(r):
            self.download_status = enums.DownloadStatus.FAILED.value
            return self.download_status

        if check_for_status(r):
            self.download_status = enums.DownloadStatus.FAILED.value
            return self.download_status

        text = get_html_content(r, id='program-source-text')
        if not text:
            self.download_status = enums.DownloadStatus.FAILED.value
            return self.download_status

        reset_timeout_counter()
        self.__dump_code(text)
        self.download_status = enums.DownloadStatus.FINISHED.value
        return self.download_status

    def __dump_code(self, text):
        self.__ensure_directories()
        data = \
            {
                'Id': self.id,
                'Contest-Id': self.contest_id,
                'Source-Code': text
            }

        with open(Submission.get_code_path(self.id, self.contest_id, self.language), 'w') as fp:
            json.dump(data, fp)
