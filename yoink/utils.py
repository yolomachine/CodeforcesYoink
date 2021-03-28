from enum import Enum


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
