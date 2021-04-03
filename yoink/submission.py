import json
import os
import re
import time
from random import randrange

import requests
from enum import unique, auto
from functools import cached_property
from yoink.globals import config
from yoink.utils import AutoName
from bs4 import BeautifulSoup

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


class Submission:
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
        self.owner = owner
        self.id = str(info['id'])
        self.time_consumed_millis = info['timeConsumedMillis']
        self.memory_consumed_bytes = info['memoryConsumedBytes']
        self.handles = [member['handle'] for member in info['author']['members']]
        self.tags = [tag for tag in info['problem']['tags']]
        self.verdict = Submission.Verdict.FAILED.value
        if 'verdict' in info:
            self.verdict = info['verdict']

        for handle in self.handles:
            if handle not in config.handles_meta['Handles']:
                config.handles_meta['Handles'][handle] = []
            config.handles_meta['Handles'][handle].append(self.owner.id)

    def request_code(self):
        print(f'#? [{self.owner.id}/{self.id}]: Trying to request source code')
        h = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Cookie': 'lastOnlineTimeUpdaterInvocation=1617456506420; 39ce7=CFu0VbD3; 70a7c28f3de=7nc1hfj1tp7g61eo2i; JSESSIONID=EB9629F08ABD285475F38FE4F40F6827-n1; evercookie_png=7nc1hfj1tp7g61eo2i; evercookie_etag=7nc1hfj1tp7g61eo2i; evercookie_cache=7nc1hfj1tp7g61eo2i; RCPC=af9ba144452752c3c8f9fff0c0b622e2; X-User-Sha1=b3841e4d0e51ddbe34a155b049a619d8635f44bd; lastOnlineTimeUpdaterInvocation=1617454694761',
            'Host': 'codeforces.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'
        }
        r = requests.get(f'https://codeforces.com/contest/{self.owner.id}/submission/{self.id}', headers=h, allow_redirects=False)
        while 'redirecting' in r.text.lower():
            m = re.search(r'document\.location\.href=\"(.*)\"', r.text)
            href = m.group(1)
            r = requests.get(href, headers=h, allow_redirects=True)

        interval = randrange(2, 5, 1)
        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            print(f'#! FAIL')
            # In order not to cause mass destruction
            time.sleep(interval)
            return

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            self.source_code = soup.find(id='program-source-text').get_text()
            print(f'#! OK')
        except AttributeError:
            return
        finally:
            # In order not to cause mass destruction
            time.sleep(interval)

        self.dump()

    def dump(self):
        if self.source_code == '':
            return

        with open(self.path, 'w') as fp:
            json.dump(self.to_dict(), fp, indent=4)

    def to_dict(self):
        return {
            'Id': self.id,
            'ContestId': self.owner.id,
            'Tags': self.tags,
            'Verdict': self.verdict,
            'Authors': self.handles,
            'SourceCode': self.source_code
        }

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

    @cached_property
    def path(self):
        return _opj(self.owner.path, f'{self.id}.json')
