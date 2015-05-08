from .private_func import setup_python_locations, get_platform


REQUIRED_REVISION = "1.0.7"
GLOBAL_SETUP = setup_python_locations()
GLOBAL_SETUP['platform'] = get_platform()
GENERIC_THUMBNAIL = "%s/resource/thumb.png" % GLOBAL_SETUP['__cwd__']


class EnumMode:
    # Get the setting from the appropriate file.
    GETCONTENT = 0
    TVSHOWS = 1
    MOVIES = 2
    ARTISTS = 3
    TVSEASONS = 4
    PLAYLIBRARY = 5
    TVEPISODES = 6
    PLEXPLUGINS = 7
    PROCESSXML = 8
    CHANNELSEARCH = 9
    CHANNELPREFS = 10
    PLAYSHELF = 11
    BASICPLAY = 12
    SHARED_MOVIES = 13
    ALBUMS = 14
    TRACKS = 15
    PHOTOS = 16
    MUSIC = 17
    VIDEOPLUGINPLAY = 18
    PLEXONLINE = 19
    CHANNELINSTALL = 20
    CHANNELVIEW = 21
    PLAYLIBRARY_TRANSCODE = 23
    DISPLAYSERVERS = 22
    MYPLEXQUEUE = 24
    SHARED_SHOWS = 25
    SHARED_MUSIC = 26
    SHARED_PHOTOS = 27
    DELETE_REFRESH = 28
    SHARED_ALL = 29
    PLAYLISTS = 30

    def __init__(self):
        pass


class EnumSubAudioControl:
    XBMC_CONTROL = "0"
    PLEX_CONTROL = "1"
    NEVER_SHOW = "2"

    def __init__(self):
        pass