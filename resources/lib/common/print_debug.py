import inspect
import re

from .addon_settings import AddonSettings

settings = AddonSettings()


class PrintDebug(object):
    DEBUG_OFF = 0
    DEBUG_INFO = 1
    DEBUG_DEBUG = 2
    DEBUG_DEBUGPLUS = 3

    DEBUG_MAP = {DEBUG_OFF: "off",
                 DEBUG_INFO: "info",
                 DEBUG_DEBUG: "debug",
                 DEBUG_DEBUGPLUS: "debug+"}

    def __init__(self, main, sub=None):
        self.main = main
        if sub:
            self.sub = "." + sub
        else:
            self.sub = ''

        self.level = settings.get_debug()
        self.token_regex = re.compile('-Token=[a-z|0-9].*[&|$]')
        self.ip_regex = re.compile('\.\d{1,3}\.\d{1,3}\.')

    def get_name(self, level):
        return self.DEBUG_MAP[level]

    def error(self, message):
        return self.__print_debug(message, 0)

    def info(self, message):
        return self.__print_debug(message, 1)

    def debug(self, message):
        return self.__print_debug(message, 2)

    def dev(self, message):
        return self.__print_debug(message, 3)

    def debugplus(self, message):
        return self.__print_debug(message, 3)

    def __print_debug(self, msg, level=1):
        if self.level >= level:
            # msg=self.token_regex.sub("-Token=XXXXXXXXXX&", str(msg))
            # msg=self.ip_regex.sub(".X.X.", msg)
            print "%s%s -> %s : %s" % (self.main, self.sub, inspect.stack(0)[2][3], msg)
        return

    def __call__(self, msg, level=1):
        return self.__print_debug(msg, level)