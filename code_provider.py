from yoink.yanker import Yanker

# TODO:
# Add command line arguments

if __name__ == '__main__':
    yanker = Yanker()
    yanker.download_contests()
    yanker.download_source_codes()