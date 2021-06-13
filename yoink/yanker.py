import time
import requests
from tqdm import tqdm
from typing import List
from functools import cached_property
from yoink.contest import Contest
from yoink.utils import Singleton, Config, CustomDefaultDict, TqdmControl


class Yanker(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.contests = CustomDefaultDict(factory=lambda key: self.__request_raw_contests(id=key)[0])
        if kwargs.get('download', False):
            self.__ensure_data()

    def __ensure_data(self) -> None:
        progress_bar = tqdm(total=len(self.__eligible_raw_contests),
                            position=TqdmControl().pos,
                            leave=True,
                            desc=f'Contests',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]')
        for raw_contest in self.__eligible_raw_contests:
            contest_id = raw_contest['id']
            contest_path = Contest.get_path(contest_id, meta=True)
            TqdmControl().inc_indent()
            TqdmControl().inc_pos()
            contest_instance = Contest.deserialize(download=Config()['After-Update'], path=contest_path)
            if not contest_instance:
                contest_instance = Contest(download=True, info=raw_contest)
            TqdmControl().dec_pos()
            TqdmControl().dec_indent()
            self.contests[contest_id] = contest_instance
            progress_bar.update()

        progress_bar.close()

    @staticmethod
    def __is_eligible(raw_contest) -> bool:
        try:
            return raw_contest['phase'] in Config()['Supported-Phases'] and \
                   raw_contest['type'] in Config()['Supported-Contest-Formats']
        except:
            return False

    def __print_eligible_contests(self, contests=None):
        if not contests:
            contests = self.__eligible_raw_contests

        print(f'\n======== {len(contests)} eligible contests ========')
        if len(contests) > 0:
            print('\n*', '\n* '.join(map(lambda x: f'[{x["id"]}] {x["name"]}', contests)), '\n')

    @cached_property
    def __eligible_raw_contests(self) -> List[dict]:
        result = self.__filter_raw_contests(self.__request_raw_contests(),
                                            apply_config_constraints=True)

        self.__print_eligible_contests(contests=result)
        if len(result) > 0:
            time.sleep(Config()['Request-Delay'])

        return result

    def __filter_raw_contests(self, *args, **kwargs) -> List[dict]:
        data = args[0]
        if not isinstance(data, list):
            data = list(data)

        result = list(filter(lambda x: Yanker.__is_eligible(x), data))

        if kwargs.get('apply_config_constraints', False):
            max_contests = Config()['Max-Contests']
            initial_contest_id = Config()['Initial-Contest-Id']
            initial_contest_index = 0
            for i, v in enumerate(result):
                if v['id'] == initial_contest_id:
                    initial_contest_index = i
                    break
            if max_contests >= 0:
                start = min(initial_contest_index, len(result))
                end = min(start + max_contests, len(result))
                result = result[start:end]

        return result

    def __request_raw_contests(self, **kwargs) -> List[dict]:
        contest_id = kwargs.get('id', None)
        if contest_id:
            return [next(v for i, v in enumerate(self.__request_raw_contests()) if v['id'] == contest_id)]

        r = requests.get('https://codeforces.com/api/contest.list')

        try:
            r.raise_for_status()
        except requests.HTTPError:
            print(r.status_code)
            exit()

        return r.json()['result']
