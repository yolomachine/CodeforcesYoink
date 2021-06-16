from __future__ import annotations

import json
import time
import requests
import yoink.enums as enums
from typing import Optional
from yoink.utils import Config, OPE, OMD, ORE, OPS, ORM, shorten_programming_language
from yoink.utils import reset_timeout_counter, check_for_redirecting, check_for_status, get_html_content


class Submission:
    @staticmethod
    def serialize(**kwargs) -> Optional[dict]:
        instance = kwargs.get('instance', None)
        if not instance:
            return None

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
    def deserialize(**kwargs) -> Optional[Submission]:
        string = kwargs.get('string', None)
        path = kwargs.get('path', None)
        if string:
            data = json.loads(string)
        elif path and OPE(path):
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
    def get_code_path_extensionless(submission_id: int, contest_id: int, language: str) -> Optional[str]:
        path = [contest_id, shorten_programming_language(language), submission_id]
        if not any(path):
            return None
        return Config().combine_path(*path)

    @staticmethod
    def get_dumped_code_meta_path(submission_id: int, contest_id: int, language: str) -> Optional[str]:
        path = Submission.get_code_path_extensionless(submission_id, contest_id, language)
        if not path:
            return None
        return f'{path}.json'

    @staticmethod
    def get_dumped_code_path(submission_id: int, contest_id: int, language: str) -> Optional[str]:
        path = Submission.get_code_path_extensionless(submission_id, contest_id, language)
        if not path:
            return None
        return f'{path}.{shorten_programming_language(language)}'

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

    def __sync(self, info) -> None:
        self.id = info['id']
        self.time_consumed_millis = info['timeConsumedMillis']
        self.memory_consumed_bytes = info['memoryConsumedBytes']
        self.handles = [member['handle'] for member in info['author']['members']]
        self.tags = [tag for tag in info['problem']['tags']]
        self.language = info['programmingLanguage']
        self.verdict = info.get('verdict', enums.Verdict.FAILED.value)

    def __ensure_directories(self) -> None:
        path = Config().combine_path(self.contest_id, shorten_programming_language(self.language))
        if path and not OPE(path):
            OMD(path)

    def download_source_code(self) -> enums.DownloadStatus:
        r = requests.get(
            f'https://codeforces.com/contest/{self.contest_id}/submission/{self.id}',
            headers=Config()['GET-Headers'],
            allow_redirects=False
        )
        time.sleep(Config()['Request-Delay'])

        if check_for_redirecting(r):
            status = enums.DownloadStatus.FAILED
            self.download_status = status.value
            return status

        if check_for_status(r):
            status = enums.DownloadStatus.FAILED
            self.download_status = status.value
            return status

        text = get_html_content(r, id='program-source-text')
        if not text:
            status = enums.DownloadStatus.FAILED
            self.download_status = status.value
            return status

        reset_timeout_counter(reset_consecutive=True)
        self.__dump_code(text)
        status = enums.DownloadStatus.FINISHED
        self.download_status = status.value
        return status

    def validate_code(self, fixup=False) -> bool:
        data_path = self.get_dumped_code_path(self.id, self.contest_id, self.language)
        meta_path = self.get_dumped_code_meta_path(self.id, self.contest_id, self.language)

        if OPE(OPS(meta_path)[0] + '.meta'):
            ORE(OPS(meta_path)[0] + '.meta', meta_path)

        if OPE(data_path):
            with open(data_path, 'r', encoding='utf-8') as fp:
                data = fp.read()
            if data is None or len(data) == 0 and fixup:
                ORM(data_path)
                return False

        if OPE(meta_path):
            with open(meta_path, 'r') as fp:
                meta = json.load(fp)
            if meta and fixup:
                dump_id = meta.get('Id', None)
                dump_contest_id = meta.get('Contest-Id', None)
                dump_language = meta.get('Language', None)
                dump_tags = meta.get('Tags', None)
                dump_code = meta.get('Source-Code', None)

                if dump_id != self.id \
                        or dump_contest_id != self.contest_id \
                        or (dump_language and dump_language != self.language) \
                        or (dump_tags and set(dump_tags) != set(self.tags)):
                    ORM(meta_path)
                    if OPE(data_path):
                        ORM(data_path)
                    return False
                else:
                    if not OPE(data_path) and dump_code and len(dump_code) > 0:
                        self.__dump_code(dump_code)
        return True

    def __dump_code(self, text: str) -> None:
        self.__ensure_directories()
        data_path = self.get_dumped_code_path(self.id, self.contest_id, self.language)
        meta_path = self.get_dumped_code_meta_path(self.id, self.contest_id, self.language)
        meta = \
            {
                'Id': self.id,
                'Contest-Id': self.contest_id,
                'Language': self.language,
                'Tags': self.tags
            }

        if meta_path:
            with open(meta_path, 'w+') as fp:
                json.dump(meta, fp, indent=4)

        if data_path:
            with open(data_path, 'w+', encoding='utf-8') as fp:
                fp.write(text.replace('\\r\\n', '\n').replace('\r\n', '\n').replace('\n\n', '\n'))
