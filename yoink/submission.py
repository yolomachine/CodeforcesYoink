import json
import os
import re
import time
import requests
import yoink.enums as enums
from functools import cached_property
from yoink.utils import Config
from bs4 import BeautifulSoup

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir
_timeout_counter = 0


class Submission:
    def __init__(self, info, owner):
        self.config = Config()
        self.source_code = ''
        self.id = str(info['id'])
        self.owner = owner
        self.time_consumed_millis = info['timeConsumedMillis']
        self.memory_consumed_bytes = info['memoryConsumedBytes']
        self.handles = [member['handle'] for member in info['author']['members']]
        self.tags = [tag for tag in info['problem']['tags']]
        self.language = info['programmingLanguage']
        self.verdict = enums.Verdict.FAILED.value
        if 'verdict' in info:
            self.verdict = info['verdict']

    def request_code(self):
        global _timeout_counter
        if _timeout_counter >= 5:
            timer = self.config.data['Request-Timeout']
            print(f'Timeout: {timer}s')
            time.sleep(timer)

        print(f'#? [{self.owner.id}/{self.id}]: Requesting source code')
        r = requests.get(
            f'https://codeforces.com/contest/{self.owner.id}/submission/{self.id}',
            headers=self.config.data['GET-Headers'],
            allow_redirects=False
        )

        while 'redirecting' in r.text.lower():
            try:
                m = re.search(r'document\.location\.href=\"(.*)\"', r.text)
                href = m.group(1)
                r = requests.get(href, headers=self.config.data['GET-Headers'], allow_redirects=True)
            except AttributeError:
                _timeout_counter += 1
                return False

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(f'#! [{r.status_code}] REQUEST ERROR')
            self.owner.meta['Submissions'][self.id] = enums.DownloadStatus.FAILED.value
            time.sleep(self.config.data['Request-Delay'])
            _timeout_counter += 1
            return False

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            self.source_code = soup.find(id='program-source-text').get_text()
        except AttributeError:
            print(f'#! COULD NOT RETRIEVE SOURCE CODE')
            self.owner.meta['Submissions'][self.id] = enums.DownloadStatus.FAILED.value
            _timeout_counter += 1
            return False
        finally:
            time.sleep(self.config.data['Request-Delay'])

        _timeout_counter = 0
        self.owner.meta['Submissions'][self.id] = enums.DownloadStatus.FINISHED.value
        return True

    def serialize(self):
        return \
            {
                'Id': self.id,
                'Contest-Id': self.owner.id,
                'Tags': self.tags,
                'Language': self.language,
                'Verdict': self.verdict,
                'Authors': self.handles,
                'Time-Consumed': self.time_consumed_millis,
                'Memory-Consumed': self.memory_consumed_bytes,
                'Source-Code': self.source_code
            }

    @staticmethod
    def deserialize(path):
        with open(path, 'r') as fp:
            data = json.load(fp)

        from yoink.yanker import Yanker
        owner = Yanker().contests[data['Contest-Id']]
        entry = {
            'id': data['Id'],
            'problem': {'tags': data['Tags']},
            'programmingLanguage': data['Language'],
            'verdict': data['Verdict'],
            'author': {'members': [{'handle': h for h in data['Authors']}]},
            'timeConsumedMillis': data['Time-Consumed'],
            'memoryConsumedBytes': data['Memory-Consumed']
        }
        instance = Submission(entry, owner)
        instance.source_code = data['Source-Code']
        return instance

    def save(self):
        with open(self.path, 'w') as fp:
            json.dump(self.serialize(), fp, indent=4)

    @cached_property
    def path(self):
        return self.owner.get_submission_path(self.id)

    @staticmethod
    def raw_tag_to_enum(tag):
        conversion_table = {
            '0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine',
        }
        tag = tag.replace(' ', '').replace('-', '_')
        tag = ''.join(list(map(lambda c: conversion_table[c] if c in conversion_table else c, *tag)))
        return tag.upper()
