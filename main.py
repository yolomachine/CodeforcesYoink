from yoink.yanker import Yanker

if __name__ == '__main__':
    y = Yanker()
    y.prepare_contests(count=6)
    y.dump()
