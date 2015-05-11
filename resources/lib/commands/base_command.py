from ..common import PrintDebug
printDebug = PrintDebug("PleXBMC", "BaseCommand")


class BaseCommand(object):
    def __init__(self, *args):
        self.args = args
        printDebug.debug("Received arguments: %s" % (args,))
        pass

    def execute(self):
        pass