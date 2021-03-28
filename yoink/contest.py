# Codeforces 'Contest' wrapper

import re

from yoink.utils import AutoName

from enum import unique, auto


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

    __pattern = re.compile(r'(?<!^)(?=[A-Z])')
    __optional = [
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
        self.id = info['id']
        self.name = info['name']
        self.type = info['type']
        self.phase = info['phase']
        self.frozen = info['frozen'] == 'true'
        self.duration_seconds = info['durationSeconds']
        self.start_time_seconds = info['startTimeSeconds']
        self.relative_time_seconds = info['relativeTimeSeconds']

        for key in Contest.__optional:
            if key in info:
                self.__setattr__(Contest.__pattern.sub('_', key), info['key'])
