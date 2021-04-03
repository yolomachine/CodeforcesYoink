import os
import json
import re
from enum import Enum
from functools import cached_property

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
    __path = 'yoink/config'

    def __init__(self):
        self.yoink_path = ''
        self.path_prefix = ''
        self.contests_meta = {'Count': 0, 'Contests': []}
        self.handles_meta = {'Count': 0, 'Handles': {}}

        if not _ope(Config.__path):
            with open(Config.__path, 'w') as fp:
                fp.write(f'YoinkPath = "{_opj(os.getcwd(), "Yoink Stuff")}')

        with open(Config.__path) as f:
            lines = f.read().strip().split('\n')
            for line in lines:
                (key, value) = map(lambda x: x.strip(' "'), line.split('='))
                if key == 'PathPrefix':
                    self.path_prefix = value
                if key == 'YoinkPath':
                    self.yoink_path = value

            # Create working directory if doesn't exist
            if not _ope(self.path):
                _omd(self.path)

            if _ope(self.contests_meta_path):
                with open(self.contests_meta_path, 'r') as fp:
                    self.contests_meta = json.load(fp)

            if _ope(self.handles_meta_path):
                with open(self.handles_meta_path, 'r') as fp:
                    self.handles_meta = json.load(fp)

    def dump(self):
        with open(self.contests_meta_path, 'w') as fp:
            json.dump(self.contests_meta, fp, indent=4)
        with open(self.handles_meta_path, 'w') as fp:
            json.dump(self.handles_meta, fp, indent=4)

    # path tp dir
    @cached_property
    def path(self):
        return _opj(self.path_prefix, self.yoink_path)

    # path to json
    @cached_property
    def contests_meta_path(self):
        return _opj(self.path, 'contests.json')

    # path to json
    @cached_property
    def handles_meta_path(self):
        return _opj(self.path, 'handles.json')
