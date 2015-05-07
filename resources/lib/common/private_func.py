import os
import socket
import struct
import sys

import xbmc
import xbmcaddon
import xbmcgui

from .addon_settings import AddonSettings
from .print_debug import PrintDebug

settings = AddonSettings()
printDebug = PrintDebug("PlexBMC", "Utils")


def is_ip(address):
    """from http://www.seanelavelle.com/2012/04/16/checking-for-a-valid-ip-in-python/"""
    try:
        socket.inet_aton(address)
        ip = True
    except socket.error:
        ip = False

    return ip


def wake_servers():
    if settings.get_setting('wolon'):

        print "PleXBMC -> Wake On LAN: true"
        for servers in settings.get_wakeservers():
            if servers:
                try:
                    print "PleXBMC -> Waking server with MAC: %s" % servers
                    __wake_on_lan(servers)
                except ValueError:
                    print "PleXBMC -> Incorrect MAC address format for server %s" % servers
                except:
                    print "PleXBMC -> Unknown wake on lan error"


def get_link_url(url, pathData, server, season_shelf=False):
    if not season_shelf:
        path = pathData.get('key', '')
    else:
        path = pathData.get('parentKey', '') + "/children"

    printDebug.debug("Path is %s" % path)

    if path == '':
        printDebug.debug("Empty Path")
        return

    #If key starts with http, then return it
    if path.startswith('http'):
        printDebug.debug("Detected http link")
        return path

    #If key starts with a / then prefix with server address
    elif path.startswith('/'):
        printDebug.debug("Detected base path link")
        return '%s%s' % (server.get_url_location(), path)

    #If key starts with plex:// then it requires transcoding
    elif path.startswith("plex:") :
        printDebug.debug("Detected plex link")
        components = path.split('&')
        for i in components:
            if 'prefix=' in i:
                del components[components.index(i)]
                break
        if pathData.get('identifier') is not None:
            components.append('identifier='+pathData['identifier'])

        path='&'.join(components)
        return 'plex://'+server.get_location()+'/'+'/'.join(path.split('/')[3:])

    elif path.startswith("rtmp"):
        printDebug.debug("Detected RTMP link")
        return path

    #Any thing else is assumed to be a relative path and is built on existing url
    else:
        printDebug.debug("Detected relative link")
        return "%s/%s" % (url, path)

    return url



def clear_shelf(movieCount=0, seasonCount=0, musicCount=0, photoCount=0):
    # Clear out old data
    WINDOW = xbmcgui.Window(10000)
    printDebug.debug("Clearing unused properties")

    try:
        for i in range(movieCount, 50 + 1):
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Path" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Title" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Year" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Rating" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Duration" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.Thumb" % i)
            WINDOW.clearProperty("Plexbmc.LatestMovie.%s.uuid" % i)
        printDebug.debug("Done clearing movies")
    except:
        pass

    try:
        for i in range(seasonCount, 50 + 1):
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.Path" % i)
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % i)
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % i)
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % i)
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.Thumb" % i)
            WINDOW.clearProperty("Plexbmc.LatestEpisode.%s.uuid" % i)
        printDebug.debug("Done clearing tv")
    except:
        pass

    try:
        for i in range(musicCount, 25 + 1):
            WINDOW.clearProperty("Plexbmc.LatestAlbum.%s.Path" % i)
            WINDOW.clearProperty("Plexbmc.LatestAlbum.%s.Title" % i)
            WINDOW.clearProperty("Plexbmc.LatestAlbum.%s.Artist" % i)
            WINDOW.clearProperty("Plexbmc.LatestAlbum.%s.Thumb" % i)
        printDebug.debug("Done clearing music")
    except:
        pass

    try:
        for i in range(photoCount, 25 + 1):
            WINDOW.clearProperty("Plexbmc.LatestPhoto.%s.Path" % i)
            WINDOW.clearProperty("Plexbmc.LatestPhoto.%s.Title" % i)
            WINDOW.clearProperty("Plexbmc.LatestPhoto.%s.Thumb" % i)
        printDebug.debug("Done clearing photos")
    except:
        pass
    return


def clear_on_deck_shelf(movie_count=0, season_count=0):
    # Clear out old data
    window = xbmcgui.Window(10000)
    printDebug.debug("Clearing unused On Deck properties")

    try:
        for i in range(movie_count, 60 + 1):
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Path" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Title" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Thumb" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Rating" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Duration" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.Year" % i)
            window.clearProperty("Plexbmc.OnDeckMovie.%s.uuid" % i)
        printDebug.debug("Done clearing On Deck movies")
    except:
        pass

    try:
        for i in range(season_count, 60 + 1):
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.Path" % i)
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.EpisodeTitle" % i)
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.EpisodeSeason" % i)
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.ShowTitle" % i)
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.Thumb" % i)
            window.clearProperty("Plexbmc.OnDeckEpisode.%s.uuid" % i)
        printDebug.debug("Done clearing On Deck tv")
    except:
        pass
    return


def clear_skin_sections(window=None, start=0, finish=50):
    printDebug.debug("Clearing properties from [%s] to [%s]" % (start, finish))

    if window is None:
        window = xbmcgui.Window(10000)

    try:
        for i in range(start, finish + 1):
            window.clearProperty("plexbmc.%d.uuid" % i)
            window.clearProperty("plexbmc.%d.title" % i)
            window.clearProperty("plexbmc.%d.subtitle" % i)
            window.clearProperty("plexbmc.%d.url" % i)
            window.clearProperty("plexbmc.%d.path" % i)
            window.clearProperty("plexbmc.%d.window" % i)
            window.clearProperty("plexbmc.%d.art" % i)
            window.clearProperty("plexbmc.%d.type" % i)
            window.clearProperty("plexbmc.%d.icon" % i)
            window.clearProperty("plexbmc.%d.thumb" % i)
            window.clearProperty("plexbmc.%d.recent" % i)
            window.clearProperty("plexbmc.%d.all" % i)
            window.clearProperty("plexbmc.%d.search" % i)
            window.clearProperty("plexbmc.%d.viewed" % i)
            window.clearProperty("plexbmc.%d.ondeck" % i)
            window.clearProperty("plexbmc.%d.released" % i)
            window.clearProperty("plexbmc.%d.shared" % i)
            window.clearProperty("plexbmc.%d.album" % i)
            window.clearProperty("plexbmc.%d.year" % i)
            window.clearProperty("plexbmc.%d.recent.content" % i)
            window.clearProperty("plexbmc.%d.ondeck.content" % i)
    except:
        printDebug.debug("Clearing stopped")
    printDebug.debug("Finished clearing properties")


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


def setup_python_locations():
    setup = dict()
    setup['__addon__'] = xbmcaddon.Addon()
    setup['__cachedir__'] = setup['__addon__'].getAddonInfo('profile')
    setup['__cwd__'] = xbmc.translatePath(setup['__addon__'].getAddonInfo('path')).decode('utf-8')
    setup['__version__'] = setup['__addon__'].getAddonInfo('version')

    setup['__resources__'] = xbmc.translatePath(os.path.join(setup['__cwd__'], 'resources', 'lib'))
    sys.path.append(setup['__resources__'])
    return setup


def __wake_on_lan(macaddress):
    """ Switches on remote computers using WOL. """

    macaddress = macaddress.strip()

    # Check macaddress format and try to compensate.
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 12 + 5:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
    send_data = ''

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = ''.join([send_data,
                             struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 7))
