import os

import requests

import json

from yoink.utils import Singleton
from yoink.contest import Contest


class Settings(metaclass=Singleton):
    __path = 'yoink/settings'

    def __init__(self):
        self.yoink_path = ""
        self.path_prefix = ""
        if not os.path.exists(Settings.__path):
            with open(Settings.__path, 'w') as fp:
                fp.write(f'YoinkPath = "{os.getcwd()}\\Yoink Stuff"')

        with open(Settings.__path) as f:
            lines = f.read().strip().split('\n')
            for line in lines:
                (key, value) = map(lambda x: x.strip(' "'), line.split('='))
                if key == 'PathPrefix':
                    self.path_prefix = value
                if key == 'YoinkPath':
                    self.yoink_path = value
            if not os.path.exists(self.get_path()):
                os.mkdir(self.get_path())
            if not os.path.exists(self.get_contests_path()):
                os.mkdir(self.get_contests_path())

    def get_path(self):
        return os.path.join(self.path_prefix, self.yoink_path)

    def get_contests_path(self):
        return os.path.join(self.get_path(), "Contests")

    def get_contests_meta_path(self):
        return os.path.join(self.get_contests_path(), "meta.json")


class Handler(metaclass=Singleton):

    def __init__(self):
        self.settings = Settings()
        self.contests = {}
        self.meta = {}
        if os.path.exists(self.settings.get_contests_meta_path()):
            with open(self.settings.get_contests_meta_path(), 'r') as fp:
                self.meta = json.load(fp)

    def get_contests(self):
        r = requests.get("https://codeforces.com/api/contest.list")

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)

        result = r.json()["result"]
        for entry in result:
            contest = Contest(entry)
            self.contests[contest.id] = contest
            if contest.id not in self.meta:
                self.meta[contest.id] = 0

        with open(self.settings.get_contests_meta_path(), 'w') as fp:
            json.dump(self.meta, fp, indent=4)
