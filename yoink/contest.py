import os
import re
from enum import unique, auto
from functools import cached_property
from yoink.globals import config
from yoink.utils import AutoName

_ope = os.path.exists
_opj = os.path.join
_omd = os.mkdir


class Contest:
    @unique
    class Phase(AutoName):
        BEFORE = auto()
        CODING = auto()
        PENDING_SYSTEM_TEST = auto()
        SYSTEM_TEST = auto()
        FINISHED = auto()

    @unique
    class Type(AutoName):
        CF = auto()
        IOI = auto()
        ICPC = auto()

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

    def __init__(self, info):
        self.meta = {}
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
                self.__setattr__(Contest.__cc2sc(key), info[key])

    @staticmethod
    def __cc2sc(key):
        return Contest.__splitter.sub('_', key)
    __splitter = re.compile(r'(?<!^)(?=[A-Z])')

    # path to dir
    @cached_property
    def path(self):
        return _opj(config.contests_path, self.id)

    # path to json
    @cached_property
    def meta_path(self):
        return _opj(self.path, "meta.json")
