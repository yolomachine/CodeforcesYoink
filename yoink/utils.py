import os
import json
import re
from enum import Enum
from functools import cached_property

from yoink.contest import Contest
from yoink.submission import Submission

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir
__splitter = re.compile(r'(?<!^)(?=[A-Z])')


def cc2sc(key):
    return __splitter.sub('_', key).lower()


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    __built_in_path = 'yoink/config'

    def __init__(self):
        self.data = {
            'Path-Prefix': os.getcwd(),
            'Yoink-Path': 'Yoink-Data-Default',
            'Contests-Meta-Json-Path': 'contests.json',
            'GET-Headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive',
                'Cookie': '',
                'Host': 'codeforces.com',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': ''
            },
            'Request-Timeout': 10,
            'Request-Delay': 0.5,
            'Supported-Verdicts': [
                Submission.Verdict.OK.value
            ],
            'Supported-Phases': [
                Contest.Phase.FINISHED.value
            ],
            'Max-Contests': 3,
            'Max-Submissions': -1
        }

        # Create working directory if doesn't exist
        if not _ope(self.working_dir_path):
            _omd(self.working_dir_path)

        # Serialize default data if doesn't exist
        if not _ope(Config.__built_in_path):
            with open(Config.__built_in_path, 'w') as fp:
                json.dump(self.data, fp)
        # Deserialize data from JSON
        else:
            with open(Config.__built_in_path, 'r') as fp:
                data = json.load(fp)
                for key in data:
                    self.data[key] = data[key]

    # Path to the working directory
    @cached_property
    def working_dir_path(self):
        return _opj(self.data['Path-Prefix'], self.data['Yoink-Path'])

    def combine_path(self, path):
        return _opj(self.working_dir_path, path)
