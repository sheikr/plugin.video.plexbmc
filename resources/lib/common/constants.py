import os
import sys
import xbmcaddon
import xbmc


def __get_platform():
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


def __setup_python_locations():
    setup = dict()
    setup['__addon__'] = xbmcaddon.Addon()
    setup['__cachedir__'] = setup['__addon__'].getAddonInfo('profile')
    setup['__cwd__'] = xbmc.translatePath(setup['__addon__'].getAddonInfo('path')).decode('utf-8')
    setup['__version__'] = setup['__addon__'].getAddonInfo('version')

    setup['__resources__'] = xbmc.translatePath(os.path.join(setup['__cwd__'], 'resources', 'lib'))
    sys.path.append(setup['__resources__'])
    return setup


ADDON_NAMESPACE = 'plugin.video.plexbmc'

GLOBAL_SETUP = __setup_python_locations()
GLOBAL_SETUP['platform'] = __get_platform()
GENERIC_THUMBNAIL = "%s/resource/thumb.png" % GLOBAL_SETUP['__cwd__']
REQUIRED_REVISION = "1.0.7"

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