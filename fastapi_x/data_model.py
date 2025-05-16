from datetime import date, datetime


class DataFeed:
    def __init__(self):
        self.data = {}
        self.position = [0, 0]
        self.test_time = datetime.now()
