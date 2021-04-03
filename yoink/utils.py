import os
import json
from enum import Enum
from functools import cached_property

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


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
        self.yoink_path = ""
        self.path_prefix = ""
        self.contests_meta = {}
        self.handles_meta = {}

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

            # Create working directories if don't exist
            if not _ope(self.path):
                _omd(self.path)

            if not _ope(self.contests_path):
                _omd(self.contests_path)

            if not _ope(self.handles_path):
                _omd(self.handles_path)

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

    # path to dir
    @cached_property
    def contests_path(self):
        return _opj(self.path, "Contests")

    # path to dir
    @cached_property
    def handles_path(self):
        return _opj(self.path, "Handles")

    # path to json
    @cached_property
    def contests_meta_path(self):
        return _opj(self.contests_path, "meta.json")

    # path to json
    @cached_property
    def handles_meta_path(self):
        return _opj(self.handles_path, "meta.json")
