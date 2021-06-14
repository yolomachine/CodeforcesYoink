import os
import json
import re
import time
import requests
import shutil
import yoink.enums as enums
from typing import Optional, Generator, Any, Union
from bs4 import BeautifulSoup
from jsonmerge import Merger

OPE = os.path.exists
OPJ = os.path.join
OMD = os.mkdir
OPS = os.path.splitext
ORE = os.rename
ORM = os.remove

__cc2sc_splitter = re.compile(r'(?<!^)(?=[A-Z])')
__timeout_counter = 0
__language_map = {
    'c++': 'cpp',
    'clang': 'cpp',
    'java': 'java',
    'c#': 'cs',
    'py': 'py',
}


def cc2sc(key: str) -> str:
    return __cc2sc_splitter.sub('_', key).lower()


def dedigitize_with_underscore_no_whitespaces_upper(tag: str) -> str:
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


def chunkenize(lst: list, n: int) -> Generator[list, Any, None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def shorten_programming_language(language: str) -> str:
    global __language_map
    buffer = language.replace(' ', '').lower()
    for key in __language_map.keys():
        if key in buffer:
            return __language_map[key]
    return language


def reset_timeout_counter() -> None:
    global __timeout_counter
    __timeout_counter = 0


def issue_timeout() -> None:
    global __timeout_counter
    __timeout_counter += 1
    if __timeout_counter >= 5:
        time.sleep(Config()['Request-Timeout'])
        reset_timeout_counter()


def check_for_redirecting(response: requests.Response) -> bool:
    while 'redirecting' in response.text.lower():
        try:
            m = re.search(r'document\.location\.href=\"(.*)\"', response.text)
            href = m.group(1)
            response = requests.get(href,
                                    headers=Config()['GET-Headers'],
                                    allow_redirects=True)
        except:
            issue_timeout()
            return True
    return False


def check_for_status(response: requests.Response) -> bool:
    try:
        response.raise_for_status()
    except requests.HTTPError:
        issue_timeout()
        return True
    return False


def get_html_content(response: requests.Response, **kwargs) -> Optional[str]:
    html_id = kwargs.get('id', None)
    if not html_id:
        return None

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.find(id=html_id).get_text()
    except AttributeError:
        issue_timeout()
        return None


def merge_data_sources(path_from: str, path_to: str):
    from_dirs = os.listdir(path_from)
    to_dirs = os.listdir(path_to)

    schema = {
        'properties': {
            'submissions': {
                'mergeStrategy': 'append'
            }
        }
    }
    merger = Merger(schema)

    for rd in from_dirs:
        from_dir = OPJ(path_from, rd)
        to_dir = OPJ(path_to, rd)
        if rd not in to_dirs:
            shutil.copytree(from_dir, to_dir, dirs_exist_ok=True)
            continue

        with open(OPJ(to_dir, 'meta.json'), 'r', encoding='utf-8') as fp:
            lhs_meta_json = json.load(fp)

        with open(OPJ(from_dir, 'meta.json'), 'r', encoding='utf-8') as fp:
            rhs_meta_json = json.load(fp)

        result = merger.merge(lhs_meta_json, rhs_meta_json)
        shutil.copytree(from_dir, to_dir, dirs_exist_ok=True)

        with open(OPJ(to_dir, 'meta.json'), 'w', encoding='utf-8') as fp:
            json.dump(result, fp, indent=4)


class CustomDefaultDict(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self.factory = kwargs.get('factory', lambda x: x)

    def __missing__(self, key):
        self[key] = self.factory(key)
        return self[key]


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TqdmControl(metaclass=Singleton):
    def __init__(self):
        self.indent = 0
        self.pos = 0

    def inc_indent(self):
        self.indent += 1

    def dec_indent(self):
        self.indent -= 1

    def inc_pos(self):
        self.pos += 1

    def dec_pos(self):
        self.pos -= 1


class Config(metaclass=Singleton):
    __built_in_path = 'yoink/config'

    def __init__(self):
        self.__data = {
            'Path-Prefix': os.path.abspath(os.sep),
            'Yoink-Path': 'Yoink-Data-Default',
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
            'After-Update': False,
            'Request-Timeout': 120,
            'Request-Delay': 1,
            'Initial-Contest-Id': -1,
            'Max-Contests': 10,
            'Max-Submissions': 2000,
            'Supported-Contest-Formats': [
                enums.Type.CF.value,
                enums.Type.ICPC.value
            ],
            'Supported-Verdicts': [
                enums.Verdict.OK.value
            ],
            'Supported-Phases': [
                enums.Phase.FINISHED.value
            ],
            'Supported-Languages': [
                enums.Language.MSCL.value,
                enums.Language.MSCL17.value,
                enums.Language.CLANG17_D.value,
                enums.Language.GPP11.value,
                enums.Language.GPP14.value,
                enums.Language.GPP17.value,
                enums.Language.GPP17_64.value,
            ],
            "Tag-Caps": {
                enums.Tag.SORT.value: 1000,
                enums.Tag.MATH.value: 1000,
                enums.Tag.GAMES.value: 1000,
                enums.Tag.GREEDY.value: 1000,
                enums.Tag.GRAPHS.value: 1000,
                enums.Tag.DYNAMIC.value: 1000,
                enums.Tag.BIN_SEARCH.value: 1000,
                enums.Tag.INTERACTIVE.value: 1000,
                enums.Tag.CONSTRUCTIVE.value: 1000,
                enums.Tag.COMBINATORICS.value: 1000,
                enums.Tag.DATA_STRUCTURES.value: 1000,
            },
        }

        self.__ensure_data()
        self.__ensure_directories()

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        self.__data[key] = value

    def __ensure_directories(self) -> None:
        if not OPE(self.working_dir_path):
            OMD(self.working_dir_path)

    def __ensure_data(self) -> None:
        if not OPE(Config.__built_in_path):
            with open(Config.__built_in_path, 'w') as fp:
                json.dump(self.__data, fp, indent=4)
        else:
            with open(Config.__built_in_path, 'r') as fp:
                data = json.load(fp)
                for key in data:
                    self[key] = data[key]

    def combine_path(self, *path) -> Union[bytes, str]:
        path = [str(i) if i else str() for i in path]
        return OPJ(self.working_dir_path, *path)

    @property
    def working_dir_path(self) -> Union[bytes, str]:
        return OPJ(self['Path-Prefix'], self['Yoink-Path'])
