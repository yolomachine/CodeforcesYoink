from yoink.yanker import Yanker

# TODO:
# Add command line arguments

if __name__ == '__main__':
    yanker = Yanker(download=True)
    for contest in yanker.contests.values():
        contest.download_source_code()
