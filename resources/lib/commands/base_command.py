

class BaseCommand(object):
    def __init__(self, *args):
        self.args = args
        pass

    def execute(self):
        pass