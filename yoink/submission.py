import json
import os
import re
import time
import requests
from enum import unique, auto
from functools import cached_property
from yoink.globals import config, yanker
from yoink.utils import AutoName
from bs4 import BeautifulSoup

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


class Submission:
    @unique
    class DownloadStatus(AutoName):
        NOT_STARTED = auto()
        FAILED = auto()
        FINISHED = auto()

    @unique
    class Verdict(AutoName):
        FAILED = auto()
        OK = auto()
        PARTIAL = auto()
        COMPILATION_ERROR = auto()
        RUNTIME_ERROR = auto()
        WRONG_ANSWER = auto()
        PRESENTATION_ERROR = auto()
        TIME_LIMIT_EXCEEDED = auto()
        MEMORY_LIMIT_EXCEEDED = auto()
        IDLENESS_LIMIT_EXCEEDED = auto()
        SECURITY_VIOLATED = auto()
        CRASHED = auto()
        INPUT_PREPARATION_CRASHED = auto()
        CHALLENGED = auto()
        SKIPPED = auto()
        TESTING = auto()
        REJECTED = auto()

    @unique
    class Tag(AutoName):
        IMPLEMENTATION = auto()
        MATH = auto()
        GREEDY = auto()
        DP = auto()
        DATA = auto()
        STRUCTURES = auto()
        BRUTE = auto()
        FORCE = auto()
        CONSTRUCTIVE = auto()
        ALGORITHMS = auto()
        GRAPHS = auto()
        SORTINGS = auto()
        BINARY = auto()
        SEARCH = auto()
        DFS_AND_SIMILAR = auto()
        TREES = auto()
        STRINGS = auto()
        NUMBER = auto()
        THEORY = auto()
        COMBINATORICS = auto()
        SPECIAL = auto()
        GEOMETRY = auto()
        BITMASKS = auto()
        TWO = auto()
        POINTERS = auto()
        DSU = auto()
        SHORTEST = auto()
        PATHS = auto()
        PROBABILITIES = auto()
        DIVIDE_AND_CONQUER = auto()
        HASHING = auto()
        GAMES = auto()
        FLOWS = auto()
        INTERACTIVE = auto()
        MATRICES = auto()
        STRING = auto()
        SUFFIX = auto()
        FFT = auto()
        GRAPH = auto()
        MATCHINGS = auto()
        TERNARY = auto()
        EXPRESSION = auto()
        PARSING = auto()
        MEET_IN_THE_MIDDLE = auto()
        TWO_SAT = auto()
        CHINESE = auto()
        REMAINDER = auto()
        THEOREM = auto()
        SCHEDULES = auto()

    def __init__(self, info, owner):
        self.source_code = ''
        self.id = str(info['id'])
        self.owner = owner
        self.time_consumed_millis = info['timeConsumedMillis']
        self.memory_consumed_bytes = info['memoryConsumedBytes']
        self.handles = [member['handle'] for member in info['author']['members']]
        self.tags = [tag for tag in info['problem']['tags']]
        self.verdict = Submission.Verdict.FAILED.value
        if 'verdict' in info:
            self.verdict = info['verdict']

    def request_code(self):
        print(f'#? [{self.owner.id}/{self.id}]: Requesting source code')
        r = requests.get(
            f'https://codeforces.com/contest/{self.owner.id}/submission/{self.id}',
            headers=config.data['GET-Headers'],
            allow_redirects=False
        )

        while 'redirecting' in r.text.lower():
            try:
                m = re.search(r'document\.location\.href=\"(.*)\"', r.text)
                href = m.group(1)
                r = requests.get(href, headers=config.data['GET-Headers'], allow_redirects=True)
            except AttributeError:
                return

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(f'#! [{r.status_code}] REQUEST ERROR')
            self.owner.meta['Submissions'][self.id] = Submission.DownloadStatus.FAILED.value
            time.sleep(config.data['Request-Delay'])
            return

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            self.source_code = soup.find(id='program-source-text').get_text()
        except AttributeError:
            print(f'#! COULD NOT RETRIEVE SOURCE CODE')
            self.owner.meta['Submissions'][self.id] = Submission.DownloadStatus.FAILED.value
            return
        finally:
            time.sleep(config.data['Request-Delay'])

        self.owner.meta['Submissions'][self.id] = Submission.DownloadStatus.FINISHED.value

    def serialize(self):
        return {
            'Id': self.id,
            'Contest-Id': self.owner.id,
            'Tags': self.tags,
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

        owner = yanker.contests[data['Contest-Id']]
        entry = {
            'id': data['Id'],
            'problem': {'tags': data['Tags']},
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
            json.dump(self.serialize(), fp)

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
