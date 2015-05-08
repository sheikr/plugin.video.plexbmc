from ..common import PrintDebug, AddonSettings, Mode
from ..utils import get_link_url
from ..plexserver import plex_network
from .base_command import BaseCommand

import xbmc
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandChannelShelf")


class CommandChannelShelf(BaseCommand):
    def __init__(self, *args):
        super(CommandChannelShelf, self).__init__(args)

    def execute(self):
        plex_network.load()
        _shelf_channel()


def _shelf_channel():
    #Gather some data and set the window properties
    printDebug.debug("== ENTER ==")
    if not settings.get_setting('channelShelf') or settings.get_setting('homeshelf') == '3':
        printDebug.debug("Disabling channel shelf")
        _clear_channel_shelf()
        return

    #Get the global host variable set in settings
    WINDOW = xbmcgui.Window(10000)

    channelCount = 1

    server_list = plex_network.get_server_list()

    if server_list == {}:
        xbmc.executebuiltin("XBMC.Notification(Unable to see any media servers,)")
        _clear_channel_shelf()
        return

    for server_details in server_list:
        if server_details.is_secondary() or not server_details.is_owned():
            continue

        if not settings.get_setting('channelShelf') or settings.get_setting('homeshelf') == '3':
            WINDOW.clearProperty("Plexbmc.LatestChannel.1.Path")
            return

        tree = server_details.get_channel_recentlyviewed()
        if tree is None:
            xbmc.executebuiltin("XBMC.Notification(Unable to contact server: %s, )" % server_details.get_name())
            _clear_channel_shelf(0)
            return

        #For each of the servers we have identified
        for media in tree:

            printDebug.debug("Found a recent channel entry")
            suffix = media.get('key').split('/')[1]

            if suffix == "photos":
                mode = Mode.PHOTOS
                channel_window = "Pictures"

            elif suffix == "video":
                mode = Mode.PLEXPLUGINS
                channel_window = "VideoLibrary"

            elif suffix == "music":
                mode = Mode.MUSIC
                channel_window = "MusicFiles"

            else:
                mode = Mode.GETCONTENT
                channel_window = "VideoLibrary"

            c_url = "ActivateWindow(%s, plugin://plugin.video.plexbmc?url=%s&mode=%s)" % (
                channel_window, get_link_url(server_details.get_url_location(), media, server_details), mode)
            pms_thumb = str(media.get('thumb', ''))

            if pms_thumb.startswith('/'):
                c_thumb = server_details.get_kodi_header_formatted_url(pms_thumb)

            else:
                c_thumb = pms_thumb

            WINDOW.setProperty("Plexbmc.LatestChannel.%s.Path" % channelCount, c_url)
            WINDOW.setProperty("Plexbmc.LatestChannel.%s.Title" % channelCount, media.get('title', 'Unknown'))
            WINDOW.setProperty("Plexbmc.LatestChannel.%s.Thumb" % channelCount, c_thumb)

            channelCount += 1

            printDebug.debug(
                "Building Recent window title: %s\n      Building Recent window url: %s\n      Building Recent window thumb: %s" % (
                    media.get('title', 'Unknown'), c_url, c_thumb))

    _clear_channel_shelf(channelCount)
    return


def _clear_channel_shelf(channel_count=0):
    WINDOW = xbmcgui.Window(10000)

    try:
        for i in range(channel_count, 30 + 1):
            WINDOW.clearProperty("Plexbmc.LatestChannel.%s.Path" % ( i ))
            WINDOW.clearProperty("Plexbmc.LatestChannel.%s.Title" % ( i ))
            WINDOW.clearProperty("Plexbmc.LatestChannel.%s.Thumb" % ( i ))
        printDebug.debug("Done clearing channels")
    except:
        pass

    return