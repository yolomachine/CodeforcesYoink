import os
import json
import re
import yoink.enums as enums
from functools import cached_property

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir
__splitter = re.compile(r'(?<!^)(?=[A-Z])')


def cc2sc(key):
    return __splitter.sub('_', key).lower()


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
            'Path-Prefix': os.path.abspath(os.sep),
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
            'Request-Timeout': 120,
            'Request-Delay': 1,
            'Max-Contests': -1,
            'Max-Submissions': -1,
            'Supported-Contest-Formats': [
                enums.Type.CF,
                enums.Type.ICPC
            ],
            'Supported-Verdicts': [
                enums.Verdict.OK
            ],
            'Supported-Phases': [
                enums.Phase.FINISHED
            ],
            'Supported-Languages': [
                enums.Language.MSCL,
                enums.Language.MSCL17,
                enums.Language.CLANG17_D,
                enums.Language.GPP11,
                enums.Language.GPP14,
                enums.Language.GPP17,
                enums.Language.GPP17_64,
            ],
            "Tag-Caps": {
                enums.Tag.SORT: 1000,
                enums.Tag.MATH: 1000,
                enums.Tag.GAMES: 1000,
                enums.Tag.GREEDY: 1000,
                enums.Tag.GRAPHS: 1000,
                enums.Tag.DYNAMIC: 1000,
                enums.Tag.BIN_SEARCH: 1000,
                enums.Tag.INTERACTIVE: 1000,
                enums.Tag.CONSTRUCTIVE: 1000,
                enums.Tag.COMBINATORICS: 1000,
                enums.Tag.DATA_STRUCTURES: 1000,
            },
        }

        # Serialize default data if doesn't exist
        if not _ope(Config.__built_in_path):
            with open(Config.__built_in_path, 'w') as fp:
                json.dump(self.data, fp, indent=4)
        # Deserialize data from JSON
        else:
            with open(Config.__built_in_path, 'r') as fp:
                data = json.load(fp)
                for key in data:
                    self.data[key] = data[key]

        # Create working directory if doesn't exist
        if not _ope(self.working_dir_path):
            _omd(self.working_dir_path)

    # Path to the working directory
    @cached_property
    def working_dir_path(self):
        return _opj(self.data['Path-Prefix'], self.data['Yoink-Path'])

    # Path to contests meta JSON
    @cached_property
    def contests_meta_path(self):
        return self.combine_path(self.data['Contests-Meta-Json-Path'])

    def combine_path(self, path):
        return _opj(self.working_dir_path, path)
