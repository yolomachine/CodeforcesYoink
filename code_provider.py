import yoink.utils
from yoink.yanker import Yanker

# TODO:
# Add command line arguments

if __name__ == '__main__':
    #yoink.utils.merge_data_sources('D://Yoink-Data-Java', 'D://Yoink-Data-Cpp')
    yanker = Yanker(download=True)
    for contest in yanker.contests.values():
        contest.download_source_code()
