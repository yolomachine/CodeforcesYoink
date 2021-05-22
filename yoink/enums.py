from enum import Enum, unique, auto


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class ProgrammingLanguageEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        __language_map = {
            'MSCL':      'MS C++',
            'MSCL17':    'MS C++ 2017',
            'CLANG17_D': 'Clang++17 Diagnostics',
            'GPP11':     'GNU C++11',
            'GPP14':     'GNU C++14',
            'GPP17':     'GNU C++17',
            'GPP17_64':  'GNU C++17 (64)',
        }
        return __language_map[name]


class TagEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        __tag_map = {
            'SORT':            'sortings',
            'MATH':            'math',
            'GAMES':           'games',
            'GREEDY':          'greedy',
            'GRAPHS':          'graphs',
            'DYNAMIC':         'dp',
            'BIN_SEARCH':      'binary search',
            'INTERACTIVE':     'interactive',
            'CONSTRUCTIVE':    'constructive algorithms',
            'COMBINATORICS':   'combinatorics',
            'DATA_STRUCTURES': 'data structures',
        }
        return __tag_map[name]


@unique
class DownloadStatus(AutoName):
    NOT_STARTED = auto()
    FAILED = auto()
    FINISHED = auto()


@unique
class Verdict(AutoName):
    FAILED = auto()
    OK = auto()
    PARTIAL = auto()
    COMPILATION_ERROR = auto()
    RUNTIME_ERROR = auto()
    WRONG_ANSWER = auto()
    PRESENTATION_ERROR = auto()
    TIME_LIMIT_EXCEEDED = auto()
    MEMORY_LIMIT_EXCEEDED = auto()
    IDLENESS_LIMIT_EXCEEDED = auto()
    SECURITY_VIOLATED = auto()
    CRASHED = auto()
    INPUT_PREPARATION_CRASHED = auto()
    CHALLENGED = auto()
    SKIPPED = auto()
    TESTING = auto()
    REJECTED = auto()


@unique
class Tag(AutoName):
    IMPLEMENTATION = auto()
    MATH = auto()
    GREEDY = auto()
    DP = auto()
    DATA = auto()
    STRUCTURES = auto()
    BRUTE = auto()
    FORCE = auto()
    CONSTRUCTIVE = auto()
    ALGORITHMS = auto()
    GRAPHS = auto()
    SORTINGS = auto()
    BINARY = auto()
    SEARCH = auto()
    DFS_AND_SIMILAR = auto()
    TREES = auto()
    STRINGS = auto()
    NUMBER = auto()
    THEORY = auto()
    COMBINATORICS = auto()
    SPECIAL = auto()
    GEOMETRY = auto()
    BITMASKS = auto()
    TWO = auto()
    POINTERS = auto()
    DSU = auto()
    SHORTEST = auto()
    PATHS = auto()
    PROBABILITIES = auto()
    DIVIDE_AND_CONQUER = auto()
    HASHING = auto()
    GAMES = auto()
    FLOWS = auto()
    INTERACTIVE = auto()
    MATRICES = auto()
    STRING = auto()
    SUFFIX = auto()
    FFT = auto()
    GRAPH = auto()
    MATCHINGS = auto()
    TERNARY = auto()
    EXPRESSION = auto()
    PARSING = auto()
    MEET_IN_THE_MIDDLE = auto()
    TWO_SAT = auto()
    CHINESE = auto()
    REMAINDER = auto()
    THEOREM = auto()
    SCHEDULES = auto()


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


@unique
class Language(ProgrammingLanguageEnum):
    MSCL = auto()
    MSCL17 = auto()
    CLANG17_D = auto()
    GPP11 = auto()
    GPP14 = auto()
    GPP17 = auto()
    GPP17_64 = auto()


@unique
class Tag(TagEnum):
    SORT = auto()
    MATH = auto()
    GAMES = auto()
    GREEDY = auto()
    GRAPHS = auto()
    DYNAMIC = auto()
    BIN_SEARCH = auto()
    INTERACTIVE = auto()
    CONSTRUCTIVE = auto()
    COMBINATORICS = auto()
    DATA_STRUCTURES = auto()
