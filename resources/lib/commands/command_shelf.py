import random

import xbmc
from .base_command import BaseCommand
from ..plexserver import plex_network
from ..common import AddonSettings, PrintDebug, EnumMode
from ..utils import clear_shelf, get_thumb, get_link_url
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PlexBMC", "utils.skin")


class CommandShelf(BaseCommand):
    def __init__(self, *args):
        super(CommandShelf, self).__init__(args)
        return

    def execute(self):
        plex_network.load()

        try:
            server_list = self.args[0]
        except:
            server_list = None

        _shelf(server_list)
        return


def _shelf(server_list=None):
    #Gather some data and set the window properties
    printDebug.debug("== ENTER ==")

    if not (settings.get_setting('movieShelf') and settings.get_setting('tvShelf') and settings.get_setting(
            'musicShelf')) or settings.get_setting('homeshelf') == '3':
        printDebug.debug("Disabling all shelf items")
        clear_shelf()
        return

    #Get the global host variable set in settings
    WINDOW = xbmcgui.Window(10000)

    movieCount = 1
    seasonCount = 1
    musicCount = 1
    added_list = {}
    direction = True
    full_count = 0

    if server_list is None:
        server_list = plex_network.get_server_list()

    if server_list == {}:
        xbmc.executebuiltin("XBMC.Notification(Unable to see any media servers,)")
        clear_shelf(0, 0, 0)
        return

    randomNumber = str(random.randint(1000000000, 9999999999))

    for server_details in server_list():

        if server_details.is_secondary() or not server_details.is_owned():
            continue

        if settings.get_setting('homeshelf') == '0' or settings.get_setting('homeshelf') == '2':
            tree = server_details.get_server_recentlyadded()
        else:
            direction = False
            tree = server_details.get_server_ondeck()

        if tree is None:
            xbmc.executebuiltin("XBMC.Notification(Unable to contact server: %s,)" % server_details.get_name())
            clear_shelf()
            return

        for eachitem in tree:

            if direction:
                added_list[int(eachitem.get('addedAt', 0))] = (eachitem, server_details )
            else:
                added_list[full_count] = (eachitem, server_details)
                full_count += 1

    library_filter = settings.get_setting('libraryfilter')
    acceptable_level = settings.get_setting('contentFilter')

    #For each of the servers we have identified
    for media, server in sorted(added_list, reverse=direction):

        if media.get('type') == "movie":

            title_name = media.get('title', 'Unknown').encode('UTF-8')

            printDebug.debug("Found a recent movie entry: [%s]" % title_name)

            if not settings.get_setting('movieShelf'):
                WINDOW.clearProperty("Plexbmc.LatestMovie.1.Path")
                continue

            if not _display_content(acceptable_level, media.get('contentRating')):
                continue

            if media.get('librarySectionID') == library_filter:
                printDebug.debug(
                    "SKIPPING: Library Filter match: %s = %s " % (library_filter, media.get('librarySectionID')))
                continue

            title_url = "plugin://plugin.video.plexbmc?url=%s&mode=%s&t=%s" % (
            get_link_url(server.get_url_location(), media, server), EnumMode.PLAYSHELF, randomNumber)
            title_thumb = get_thumb(media, server)

            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Path" % movieCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Title" % movieCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Thumb" % movieCount, title_thumb)

            movieCount += 1

        elif media.get('type') == "season":

            printDebug.debug(
                "Found a recent season entry [%s]" % ( media.get('parentTitle', 'Unknown').encode('UTF-8'), ))

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.LatestEpisode.1.Path")
                continue

            title_name = media.get('parentTitle', 'Unknown').encode('UTF-8')
            title_url = "ActivateWindow(VideoLibrary, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
            get_link_url(server.get_url_location(), media, server), EnumMode.TVEPISODES)
            title_thumb = get_thumb(media, server)

            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Path" % seasonCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % seasonCount, '')
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % seasonCount,
                               media.get('title', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % seasonCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Thumb" % seasonCount, title_thumb)
            seasonCount += 1

        elif media.get('type') == "album":

            if not settings.get_setting('musicShelf'):
                WINDOW.clearProperty("Plexbmc.LatestAlbum.1.Path")
                continue

            printDebug.debug("Found a recent album entry")

            title_name = media.get('parentTitle', 'Unknown').encode('UTF-8')
            title_url = "ActivateWindow(MusicFiles, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
            get_link_url(server.get_url_location(), media, server), EnumMode.TRACKS)
            title_thumb = get_thumb(media, server)

            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Path" % musicCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Title" % musicCount,
                               media.get('title', 'Unknown').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Artist" % musicCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Thumb" % musicCount, title_thumb)
            musicCount += 1

        elif media.get('type') == "episode":

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            printDebug.debug("Found an onDeck episode entry [%s]" % title_name)

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.LatestEpisode.1.Path")
                continue

            # todo: to few arguments in "format string"
            title_url = "PlayMedia(plugin://plugin.video.plexbmc?url=%s&mode=%s%s)" % (
            get_link_url(server.get_url_location(), media, server), EnumMode.PLAYSHELF)
            title_thumb = server.get_kodi_header_formatted_url(media.get('grandparentThumb', ''))

            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Path" % seasonCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % seasonCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % seasonCount,
                               media.get('grandparentTitle', 'Unknown').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % seasonCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Thumb" % seasonCount, title_thumb)
            seasonCount += 1

        printDebug.debug(
            " Building Recent window title: %s\n        Building Recent window url: %s\n        Building Recent window thumb: %s" % (
            title_name, title_url, title_thumb))

    clear_shelf(movieCount, seasonCount, musicCount)


def _display_content(acceptable_level, content_level):
    """
        Takes a content Rating and decides whether it is an allowable
        level, as defined by the content filter
        @input: content rating
        @output: boolean
    """

    printDebug.info("Checking rating flag [%s] against [%s]" % (content_level, acceptable_level))

    if acceptable_level == "Adults":
        printDebug.debug("OK to display")
        return True

    content_map = {'Kids': 0,
                   'Teens': 1,
                   'Adults': 2}

    rating_map = {'G': 0,  # MPAA Kids
                  'PG': 0,  # MPAA Kids
                  'PG-13': 1,  # MPAA Teens
                  'R': 2,  # MPAA Adults
                  'NC-17': 2,  # MPAA Adults
                  'NR': 2,  # MPAA Adults
                  'Unrated': 2,  # MPAA Adults

                  'U': 0,  # BBFC Kids
                  'PG': 0,  # BBFC Kids
                  '12': 1,  # BBFC Teens
                  '12A': 1,  # BBFC Teens
                  '15': 1,  # BBFC Teens
                  '18': 2,  # BBFC Adults
                  'R18': 2,  # BBFC Adults

                  'E': 0,  #ACB Kids (hopefully)
                  'G': 0,  #ACB Kids
                  'PG': 0,  #ACB Kids
                  'M': 1,  #ACB Teens
                  'MA15+': 2,  #ADC Adults
                  'R18+': 2,  #ACB Adults
                  'X18+': 2,  #ACB Adults

                  'TV-Y': 0,  # US TV - Kids
                  'TV-Y7': 0,  # US TV - Kids
                  'TV -G': 0,  # Us TV - kids
                  'TV-PG': 1,  # US TV - Teens
                  'TV-14': 1,  # US TV - Teens
                  'TV-MA': 2,  # US TV - Adults

                  'G': 0,  # CAN - kids
                  'PG': 0,  # CAN - kids
                  '14A': 1,  # CAN - teens
                  '18A': 2,  # CAN - Adults
                  'R': 2,  # CAN - Adults
                  'A': 2}  # CAN - Adults

    if content_level is None or content_level == "None":
        printDebug.debug("Setting [None] rating as %s" % settings.get_setting('contentNone'))
        if content_map[settings.get_setting('contentNone')] <= content_map[acceptable_level]:
            printDebug.debug("OK to display")
            return True
    else:
        try:
            if rating_map[content_level] <= content_map[acceptable_level]:
                printDebug.debug("OK to display")
                return True
        except:
            print "Unknown rating flag [%s] whilst lookuing for [%s] - will filter for now, but needs to be added" % (
            content_level, acceptable_level)

    printDebug.debug("NOT OK to display")
    return False