import xbmc
import xbmcaddon
import inspect
import os
import sys
import socket
import re
from settings import AddonSettings


class PrintDebug:

    def __init__(self, main, sub=None):

        self.main = main
        if sub:
            self.sub = "."+sub
        else:
            self.sub = ''

        self.level = settings.get_debug()
        self.privacy = settings.get_setting('privacy')

        self.DEBUG_OFF = 0
        self.DEBUG_INFO = 1
        self.DEBUG_DEBUG = 2
        self.DEBUG_DEBUGPLUS = 3
        self.token_regex = re.compile('-Token=[a-z|0-9].*?[&|$]')
        self.ip_regex = re.compile('\.\d{1,3}\.\d{1,3}\.')
        self.user_regex = re.compile('-User=[a-z|0-9].*?[&|$]')

        self.DEBUG_MAP = {self.DEBUG_OFF      : "off",
                          self.DEBUG_INFO     : "info",
                          self.DEBUG_DEBUG    : "debug",
                          self.DEBUG_DEBUGPLUS: "debug+"}

    def get_name(self, level):
        return self.DEBUG_MAP[level]

    def error(self, message):
        return self.__print_message(message, 0)

    def warn(self, message):
        return self.__print_message(message, 0)

    def info(self, message):
        return self.__print_message(message, 1)

    def debug(self, message):
        return self.__print_message(message, 2)

    def dev(self, message):
        return self.__print_message(message, 3)

    def debugplus(self, message):
        return self.__print_message(message, 3)

    def __print_message(self, msg, level=1):
        if self.level >= level:
            if self.privacy:
                msg = self.token_regex.sub("X-Plex-Token=XXXXXXXXXX&", str(msg))
                msg = self.ip_regex.sub(".X.X.", msg)
                msg = self.user_regex.sub("X-Plex-User=XXXXXXX&", msg)

            try:
                print "%s%s -> %s : %s" % (self.main, self.sub, inspect.stack(0)[2][3], msg.encode('utf-8'))
            except:
                print "%s%s -> %s : %s [NONUTF8]" % (self.main, self.sub, inspect.stack(0)[2][3], msg)

        return

    def __call__(self, msg, level=1):
        return self.__print_message(msg, level)


def get_platform():
    if xbmc.getCondVisibility('system.platform.osx'):
        return "OSX"
    elif xbmc.getCondVisibility('system.platform.atv2'):
        return "ATV2"
    elif xbmc.getCondVisibility('system.platform.ios'):
        return "iOS"
    elif xbmc.getCondVisibility('system.platform.windows'):
        return "Windows"
    elif xbmc.getCondVisibility('system.platform.linux'):
        return "Linux/RPi"
    elif xbmc.getCondVisibility('system.platform.android'): 
        return "Linux/Android"
    return "Unknown"


def wake_servers():
    if settings.get_setting('wolon'):
        from WOL import wake_on_lan
        print "PleXBMC -> Wake On LAN: true"
        for servers in settings.get_wakeservers():
            if servers:
                try:
                    print "PleXBMC -> Waking server with MAC: %s" % servers
                    wake_on_lan(servers)
                except ValueError:
                    print "PleXBMC -> Incorrect MAC address format for server %s" % servers
                except:
                    print "PleXBMC -> Unknown wake on lan error"


def setup_python_locations():
    setup = {}
    setup['__addon__'] = xbmcaddon.Addon()
    setup['__cachedir__'] = setup['__addon__'].getAddonInfo('profile')
    setup['__cwd__'] = xbmc.translatePath(setup['__addon__'].getAddonInfo('path')).decode('utf-8')
    setup['__version__'] = setup['__addon__'].getAddonInfo('version')
    setup['__resources__'] = xbmc.translatePath(os.path.join(setup['__cwd__'], 'resources', 'lib'))
    sys.path.append(setup['__resources__'])
    return setup                


def is_ip(address):
    """from http://www.seanelavelle.com/2012/04/16/checking-for-a-valid-ip-in-python/"""
    try:
        socket.inet_aton(address)
        ip = True
    except socket.error:
        ip = False

    return ip


def get_platform_ip():
    return xbmc.getIPAddress()

GLOBAL_SETUP = setup_python_locations()
GLOBAL_SETUP['platform'] = get_platform()
GENERIC_THUMBNAIL = "%s/resource/thumb.png" % GLOBAL_SETUP['__cwd__']
REQUIRED_REVISION = "1.0.7"
settings = AddonSettings('plugin.video.plexbmc')

# Get the setting from the appropriate file.
MODE_GETCONTENT = 0
MODE_TVSHOWS = 1
MODE_MOVIES = 2
MODE_ARTISTS = 3
MODE_TVSEASONS = 4
MODE_PLAYLIBRARY = 5
MODE_TVEPISODES = 6
MODE_PLEXPLUGINS = 7
MODE_PROCESSXML = 8
MODE_CHANNELSEARCH = 9
MODE_CHANNELPREFS = 10
MODE_PLAYSHELF = 11
MODE_BASICPLAY = 12
MODE_SHARED_MOVIES = 13
MODE_ALBUMS = 14
MODE_TRACKS = 15
MODE_PHOTOS = 16
MODE_MUSIC = 17
MODE_VIDEOPLUGINPLAY = 18
MODE_PLEXONLINE = 19
MODE_CHANNELINSTALL = 20
MODE_CHANNELVIEW = 21
MODE_PLAYLIBRARY_TRANSCODE = 23
MODE_DISPLAYSERVERS = 22
MODE_MYPLEXQUEUE = 24
MODE_SHARED_SHOWS = 25
MODE_SHARED_MUSIC = 26
MODE_SHARED_PHOTOS = 27
MODE_DELETE_REFRESH = 28
MODE_SHARED_ALL = 29
MODE_PLAYLISTS = 30

SUB_AUDIO_XBMC_CONTROL = "0"
SUB_AUDIO_PLEX_CONTROL = "1"
SUB_AUDIO_NEVER_SHOW = "2"
