import xbmcgui

from .base_command import BaseCommand
from ..plexserver import plex_network
from ..common import PrintDebug, AddonSettings, Mode, GENERIC_THUMBNAIL
from ..utils import clear_skin_sections

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandSkin")


class CommandSkin(BaseCommand):
    def __init__(self, *args):
        super(CommandSkin, self).__init__(args)
        return

    def execute(self):
        plex_network.load()
        try:
            skin_type = self.args[0]
        except:
            skin_type = None

        try:
            server_list = self.args[1]
        except:
            server_list = None

        _skin(skin_type, server_list)
        return


def _skin(skin_type=None, server_list=None):
    # Gather some data and set the window properties
    printDebug.debug("== ENTER ==")
    # Get the global host variable set in settings
    window = xbmcgui.Window(10000)

    section_count = 0
    server_count = 0
    shared_flag = {}
    hide_shared = settings.get_setting('hide_shared')

    window.setProperty("plexbmc.myplex_signedin", str(plex_network.is_myplex_signedin()))
    window.setProperty("plexbmc.plexhome_enabled", str(plex_network.is_plexhome_enabled()))

    if server_list is None:
        server_list = plex_network.get_server_list()

    for server in server_list:

        server.discover_sections()

        for section in server.get_sections():

            extra_data = {'fanart_image': server.get_fanart(section),
                          'thumb': server.get_fanart(section)}

            # Determine what we are going to do process after a link
            # is selected by the user, based on the content we find

            path = section.get_path()

            if section.is_show():
                if hide_shared == "true" and not server.is_owned():
                    shared_flag['show'] = True
                    continue
                window_name = "VideoLibrary"
                mode = Mode.TVSHOWS
                window.setProperty("plexbmc.%d.search" % section_count,
                                   "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                       window_name, server.get_url_location(), section.get_path(), "/search?type=4",
                                       mode))
            if section.is_movie():
                if hide_shared == "true" and not server.is_owned():
                    shared_flag['movie'] = True
                    continue
                window_name = "VideoLibrary"
                mode = Mode.MOVIES
                window.setProperty("plexbmc.%d.search" % section_count,
                                   "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                       window_name, server.get_url_location(), section.get_path(), "/search?type=1",
                                       mode))
            if section.is_artist():
                if hide_shared == "true" and not server.is_owned():
                    shared_flag['artist'] = True
                    continue
                window_name = "MusicFiles"
                mode = Mode.ARTISTS
                window.setProperty("plexbmc.%d.album" % section_count,
                                   "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                       window_name, server.get_url_location(), section.get_path(), "/albums", mode))
                window.setProperty("plexbmc.%d.search" % section_count,
                                   "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                       window_name, server.get_url_location(), section.get_path(), "/search?type=10",
                                       mode))
            if section.is_photo():
                if hide_shared == "true" and not server.is_owned():
                    shared_flag['photo'] = True
                    continue
                window_name = "Pictures"
                window.setProperty("plexbmc.%d.year" % section_count,
                                   "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                       window_name, server.get_url_location(), section.get_path(), "/year", mode))
                mode = Mode.PHOTOS

            if settings.get_setting('secondary'):
                mode = Mode.GETCONTENT
            else:
                path += '/all'

            s_url = '%s%s&mode=%s' % (server.get_url_location(), path, mode)

            #Build that listing..
            window.setProperty("plexbmc.%d.title" % section_count, section.get_title())
            window.setProperty("plexbmc.%d.subtitle" % section_count, server.get_name())
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s,return)" % (window_name, s_url))
            window.setProperty("plexbmc.%d.art" % section_count, extra_data['fanart_image'])
            window.setProperty("plexbmc.%d.type" % section_count, section.get_type())
            window.setProperty("plexbmc.%d.icon" % section_count, extra_data.get('thumb', GENERIC_THUMBNAIL))
            window.setProperty("plexbmc.%d.thumb" % section_count, extra_data.get('thumb', GENERIC_THUMBNAIL))
            window.setProperty("plexbmc.%d.partialpath" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s" % (
                                   window_name, server.get_url_location(), section.get_path()))
            window.setProperty("plexbmc.%d.search" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/search?type=1", mode))
            window.setProperty("plexbmc.%d.recent" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/recentlyAdded", mode))
            window.setProperty("plexbmc.%d.all" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/all", mode, ))
            window.setProperty("plexbmc.%d.viewed" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/recentlyViewed", mode))
            window.setProperty("plexbmc.%d.ondeck" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/onDeck", mode))
            window.setProperty("plexbmc.%d.released" % section_count,
                               "ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s%s%s&mode=%s,return)" % (
                                   window_name, server.get_url_location(), section.get_path(), "/newest", mode))
            window.setProperty("plexbmc.%d.shared" % section_count, "false")

            printDebug.debug(
                "Building window properties index [%s] which is [%s]" % (section_count, section.get_title()))
            printDebug.debug(
                "PATH in use is: ActivateWindow(%s,plugin://plugin.video.plexbmc/?url=%s,return)" % (
                window_name, s_url))
            section_count += 1

    if skin_type == "nocat":
        window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
        window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
        window.setProperty("plexbmc.%d.path" % section_count,
                           "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                           Mode.SHARED_ALL)
        window.setProperty("plexbmc.%d.type" % section_count, "movie")
        window.setProperty("plexbmc.%d.shared" % section_count, "true")
        section_count += 1

    else:

        if shared_flag.get('movie'):
            window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
            window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_MOVIES)
            window.setProperty("plexbmc.%d.type" % section_count, "movie")
            window.setProperty("plexbmc.%d.shared" % section_count, "true")
            section_count += 1

        if shared_flag.get('show'):
            window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
            window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_SHOWS)
            window.setProperty("plexbmc.%d.type" % section_count, "show")
            window.setProperty("plexbmc.%d.shared" % section_count, "true")
            section_count += 1

        if shared_flag.get('artist'):
            window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
            window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(MusicFiles,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_MUSIC)
            window.setProperty("plexbmc.%d.type" % section_count, "artist")
            window.setProperty("plexbmc.%d.shared" % section_count, "true")
            section_count += 1

        if shared_flag.get('photo'):
            window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
            window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(Pictures,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_PHOTOS)
            window.setProperty("plexbmc.%d.type" % section_count, "photo")
            window.setProperty("plexbmc.%d.shared" % section_count, "true")
            section_count += 1

    #For each of the servers we have identified
    num_of_servers = len(server_list)

    for server in server_list:

        if server.is_secondary():
            continue

        if settings.get_setting('channelview'):
            window.setProperty("plexbmc.channel", "1")
            window.setProperty("plexbmc.%d.server.channel" % server_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=%s/channels/all&mode=21,return)" %
                               server.get_url_location())
        else:
            window.clearProperty("plexbmc.channel")
            window.setProperty("plexbmc.%d.server.video" % server_count, "%s/video&mode=7" % server.get_url_location())
            window.setProperty("plexbmc.%d.server.music" % server_count,
                               "%s/music&mode=17" % server.get_url_location())
            window.setProperty("plexbmc.%d.server.photo" % server_count,
                               "%s/photos&mode=16" % server.get_url_location())

        window.setProperty("plexbmc.%d.server.online" % server_count,
                           "%s/system/plexonline&mode=19" % server.get_url_location())

        window.setProperty("plexbmc.%d.server" % server_count, server.get_name())

        server_count += 1

    #Clear out old data
    clear_skin_sections(window, section_count, int(window.getProperty("plexbmc.sectionCount") if '' else 50))

    printDebug.debug("Total number of skin sections is [%s]" % section_count)
    printDebug.debug("Total number of servers is [%s]" % num_of_servers)
    window.setProperty("plexbmc.sectionCount", str(section_count))
    window.setProperty("plexbmc.numServers", str(num_of_servers))
    if plex_network.is_myplex_signedin():
        window.setProperty("plexbmc.queue",
                           "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=http://myplexqueue&mode=24,return)")
        window.setProperty("plexbmc.myplex", "1")
    else:
        window.clearProperty("plexbmc.myplex")

    return