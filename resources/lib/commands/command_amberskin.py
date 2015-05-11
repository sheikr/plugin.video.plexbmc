import random
import urllib
import xbmc
import xbmcgui

from .base_command import BaseCommand
from ..utils import clear_skin_sections, clear_shelf, clear_on_deck_shelf, get_link_url
from ..plexserver import plex_network, get_master_server
from ..common import PrintDebug, AddonSettings
from ..common import Mode, GENERIC_THUMBNAIL

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandAmberSkin")


class CommandAmberSkin(BaseCommand):
    def __init__(self, *args):
        super(CommandAmberSkin, self).__init__(args)
        return

    def execute(self):
        plex_network.load()
        amberskin()


def amberskin():
    #Gather some data and set the window properties
    printDebug.debug("== ENTER ==")
    #Get the global host variable set in settings
    window = xbmcgui.Window(10000)

    section_count = 0
    server_count = 0
    shared_count = 0
    shared_flag = {}
    hide_shared = settings.get_setting('hide_shared')

    server_list = plex_network.get_server_list()

    window.setProperty("plexbmc.myplex_signedin", str(plex_network.is_myplex_signedin()))
    window.setProperty("plexbmc.plexhome_enabled", str(plex_network.is_plexhome_enabled()))

    if plex_network.is_plexhome_enabled():
        window.setProperty("plexbmc.plexhome_user", str(plex_network.get_myplex_user()))
        window.setProperty("plexbmc.plexhome_avatar", str(plex_network.get_myplex_avatar()))

    printDebug.debug("Using list of %s servers: %s " % (len(server_list), server_list))

    for server in server_list:

        server.discover_sections()

        for section in server.get_sections():

            printDebug.debug("=Enter amberskin section=")
            printDebug.debug(str(section.__dict__))
            printDebug.debug("=/section=")

            extra_data = {'fanart_image': server.get_fanart(section)}

            # Determine what we are going to do process after a link
            # is selected by the user, based on the content we find
            path = section.get_path()
            base_url = "plugin://plugin.video.plexbmc/?url=%s" % server.get_url_location()

            if section.is_show():
                if hide_shared and not server.is_owned():
                    shared_flag['show'] = True
                    shared_count += 1
                    continue
                window_name = "VideoLibrary"
                mode = Mode.TVSHOWS
                window.setProperty("plexbmc.%d.search" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                    window_name, base_url, path, "/search?type=4", mode))

            elif section.is_movie():
                if hide_shared and not server.is_owned():
                    shared_flag['movie'] = True
                    shared_count += 1
                    continue
                window_name = "VideoLibrary"
                mode = Mode.MOVIES
                window.setProperty("plexbmc.%d.search" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                    window_name, base_url, path, "/search?type=1", mode))

            elif section.is_artist():
                if hide_shared and not server.is_owned():
                    shared_flag['artist'] = True
                    shared_count += 1
                    continue
                window_name = "MusicFiles"
                mode = Mode.ARTISTS
                window.setProperty("plexbmc.%d.album" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                    window_name, base_url, path, "/albums", mode))
                window.setProperty("plexbmc.%d.search" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                    window_name, base_url, path, "/search?type=10", mode))
            elif section.is_photo():
                if hide_shared and not server.is_owned():
                    shared_flag['photo'] = True
                    shared_count += 1
                    continue
                window_name = "Pictures"
                window.setProperty("plexbmc.%d.year" % section_count,
                                   "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                                       window_name, base_url, path, "/year", mode))

            else:
                if hide_shared and not server.is_owned():
                    shared_flag['movie'] = True
                    shared_count += 1
                    continue
                window_name = "Videos"
                mode = Mode.PHOTOS

            if settings.get_setting('secondary'):
                mode = Mode.GETCONTENT
                suffix = ''
            else:
                suffix = '/all'

            #Build that listing
            window.setProperty("plexbmc.%d.uuid" % section_count, section.get_uuid())
            window.setProperty("plexbmc.%d.title" % section_count, section.get_title())
            window.setProperty("plexbmc.%d.subtitle" % section_count, server.get_name())
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(%s,%s%s&mode=%s,return)" % (window_name, base_url, path + suffix, mode))
            window.setProperty("plexbmc.%d.art" % section_count, extra_data['fanart_image'])
            window.setProperty("plexbmc.%d.type" % section_count, section.get_type())
            window.setProperty("plexbmc.%d.icon" % section_count, extra_data.get('thumb', GENERIC_THUMBNAIL))
            window.setProperty("plexbmc.%d.thumb" % section_count, extra_data.get('thumb', GENERIC_THUMBNAIL))
            window.setProperty("plexbmc.%d.partialpath" % section_count,
                               "ActivateWindow(%s,%s%s" % (window_name, base_url, path))
            window.setProperty("plexbmc.%d.search" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                window_name, base_url, path, "/search?type=1", mode))
            window.setProperty("plexbmc.%d.recent" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                window_name, base_url, path, "/recentlyAdded", mode))
            window.setProperty("plexbmc.%d.all" % section_count,
                               "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (window_name, base_url, path, "/all", mode))
            window.setProperty("plexbmc.%d.viewed" % section_count, "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                window_name, base_url, path, "/recentlyViewed", mode))
            window.setProperty("plexbmc.%d.ondeck" % section_count,
                               "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                                   window_name, base_url, path, "/onDeck", mode))
            window.setProperty("plexbmc.%d.released" % section_count,
                               "ActivateWindow(%s,%s%s%s&mode=%s,return)" % (
                                   window_name, base_url, path, "/newest", mode))
            window.setProperty("plexbmc.%d.shared" % section_count, "false")
            window.setProperty("plexbmc.%d.ondeck.content" % section_count,
                               "%s%s%s&mode=%s" % (base_url, path, "/onDeck", mode))
            window.setProperty("plexbmc.%d.recent.content" % section_count,
                               "%s%s%s&mode=%s" % (base_url, path, "/recentlyAdded", mode))

            printDebug.debug(
                "Building window properties index [%s] which is [%s]" % (section_count, section.get_title()))
            printDebug.debug(
                "PATH in use is: ActivateWindow(%s,%s%s&mode=%s,return)" % (window_name, base_url, path, mode))
            section_count += 1

    if plex_network.is_myplex_signedin() and hide_shared and shared_count != 0:
        window.setProperty("plexbmc.%d.title" % section_count, "Shared Content")
        window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
        window.setProperty("plexbmc.%d.path" % section_count,
                           "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                           Mode.SHARED_ALL)
        window.setProperty("plexbmc.%d.type" % section_count, "shared")
        window.setProperty("plexbmc.%d.shared" % section_count, "true")
        section_count += 1

    elif shared_count != 0:

        window.setProperty("plexbmc.%d.title" % section_count, "Shared...")
        window.setProperty("plexbmc.%d.subtitle" % section_count, "Shared")
        window.setProperty("plexbmc.%d.type" % section_count, "shared")
        window.setProperty("plexbmc.%d.shared" % section_count, "true")

        if shared_flag.get('movie'):
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_MOVIES)

        if shared_flag.get('show'):
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_SHOWS)

        if shared_flag.get('artist'):
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(MusicFiles,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_MUSIC)

        if shared_flag.get('photo'):
            window.setProperty("plexbmc.%d.path" % section_count,
                               "ActivateWindow(Pictures,plugin://plugin.video.plexbmc/?url=/&mode=%s,return)" %
                               Mode.SHARED_PHOTOS)

        section_count += 1

    #For each of the servers we have identified
    num_of_servers = len(server_list)
    #shelfChannel (server_list)

    for server in server_list:

        printDebug.debug(server.get_details())

        if server.is_secondary():
            continue

        if settings.get_setting('channelview'):
            window.setProperty("plexbmc.channel", "1")
            window.setProperty("plexbmc.%d.server.channel" % server_count,
                               "ActivateWindow(VideoLibrary,plugin://plugin.video.plexbmc/?url=%s%s&mode=%s, return" %
                               (server.get_url_location(), "/channels/all", Mode.CHANNELVIEW))
        else:
            window.clearProperty("plexbmc.channel")
            window.setProperty("plexbmc.%d.server.video" % server_count,
                               "%s%s&mode=%s" % (server.get_url_location(), "/video", Mode.PLEXPLUGINS))
            window.setProperty("plexbmc.%d.server.music" % server_count,
                               "%s%s&mode=%s" % (server.get_url_location(), "/music", Mode.MUSIC))
            window.setProperty("plexbmc.%d.server.photo" % server_count,
                               "%s%s&mode=%s" % (server.get_url_location(), "/photos", Mode.PHOTOS))

        window.setProperty("plexbmc.%d.server.online" % server_count,
                           "%s%s&mode=%s" % (server.get_url_location(), "/system/plexonline", Mode.PLEXONLINE))

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

        #Now let's populate queue shelf items since we have MyPlex login
        if settings.get_setting('homeshelf') != '3':
            printDebug.debug("== ENTER ==")

            root = plex_network.get_myplex_queue()
            server_address = get_master_server()
            queue_count = 1

            for media in root:
                printDebug.debug("Found a queue item entry: [%s]" % (media.get('title', '').encode('UTF-8'), ))
                m_url = "plugin://plugin.video.plexbmc?url=%s&mode=%s&indirect=%s" % (
                    get_link_url(server_address.get_url_location(), media, server_address), 18, 1)
                m_thumb = _get_shelf_thumb(media, server_address)

                try:
                    movie_runtime = str(int(float(media.get('duration')) / 1000 / 60))
                except:
                    movie_runtime = ""

                window.setProperty("Plexbmc.Queue.%s.Path" % queue_count, m_url)
                window.setProperty("Plexbmc.Queue.%s.Title" % queue_count,
                                   media.get('title', 'Unknown').encode('UTF-8'))
                window.setProperty("Plexbmc.Queue.%s.Year" % queue_count,
                                   media.get('originallyAvailableAt', '').encode('UTF-8'))
                window.setProperty("Plexbmc.Queue.%s.Duration" % queue_count, movie_runtime)
                window.setProperty("Plexbmc.Queue.%s.Thumb" % queue_count, m_thumb)

                queue_count += 1

                printDebug.debug("Building Queue item: %s" % media.get('title', 'Unknown').encode('UTF-8'))
                printDebug.debug("Building Queue item url: %s" % m_url)
                printDebug.debug("Building Queue item thumb: %s" % m_thumb)

            _clear_queue_shelf(queue_count)

    else:
        window.clearProperty("plexbmc.myplex")

    _full_shelf(server_list)


def _full_shelf(server_list=None):
    # Gather some data and set the window properties
    if not server_list:
        server_list = {}

    printDebug.debug("== ENTER ==")

    if settings.get_setting('homeshelf') == '3' or (
                    not settings.get_setting('movieShelf') and not settings.get_setting(
                        'tvShelf') and not settings.get_setting(
                    'musicShelf')):
        printDebug.debug("Disabling all shelf items")
        clear_shelf()
        clear_on_deck_shelf()
        return

    #Get the global host variable set in settings
    WINDOW = xbmcgui.Window(10000)

    recentMovieCount = 1
    recentSeasonCount = 1
    recentMusicCount = 1
    recentPhotoCount = 1
    ondeckMovieCount = 1
    ondeckSeasonCount = 1
    recent_list = []
    ondeck_list = []

    if server_list == {}:
        xbmc.executebuiltin("XBMC.Notification(Unable to see any media servers,)")
        clear_shelf(0, 0, 0, 0)
        return

    randomNumber = str(random.randint(1000000000, 9999999999))

    for server_details in server_list:

        if not server_details.is_owned():
            continue

        for section in server_details.get_sections():

            if settings.get_setting('homeshelf') == '0' or settings.get_setting('homeshelf') == '2':

                tree = server_details.get_recently_added(section=section.get_key(), size=15,
                                                         hide_watched=settings.get_setting('hide_watched_recent_items'))

                if tree is None:
                    printDebug.debug(
                        "PLEXBMC -> RecentlyAdded items not found on: %s" % server_details.get_url_location())
                    continue

                libraryuuid = tree.get("librarySectionUUID", '').encode('utf-8')

                ep_helper = {}  # helper season counter
                for eachitem in tree:

                    if eachitem.get("type", "") == "episode":
                        key = int(eachitem.get("parentRatingKey"))  # season identifier

                        if key in ep_helper:
                            continue

                        ep_helper[key] = key  # use seasons as dict key so we can check

                    recent_list.append((eachitem, server_details, libraryuuid))

            if settings.get_setting('homeshelf') == '1' or settings.get_setting('homeshelf') == '2':

                tree = server_details.get_ondeck(section=section.get_key(), size=15)
                if tree is None:
                    print ("PLEXBMC -> OnDeck items not found on: " + server_details.get_url_location(), False)
                    continue

                libraryuuid = tree.get("librarySectionUUID", '').encode('utf-8')
                for eachitem in tree:
                    ondeck_list.append((eachitem, server_details, libraryuuid))

    printDebug.debugplus("Recent object is: %s" % recent_list)
    printDebug.debugplus("ondeck object is: %s" % ondeck_list)
    prefer_season = settings.get_setting('prefer_season_thumbs')

    #For each of the servers we have identified
    for media, source_server, libuuid in recent_list:

        if media.get('type') == "movie":

            if not settings.get_setting('movieShelf'):
                WINDOW.clearProperty("Plexbmc.LatestMovie.1.Path")
                continue

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            printDebug.debug("Found a recent movie entry: [%s]" % title_name)

            title_url = "plugin://plugin.video.plexbmc?url=%s&mode=%s&t=%s" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.PLAYSHELF, randomNumber)
            title_thumb = _get_shelf_thumb(media, source_server)

            if media.get('duration') > 0:
                movie_runtime = str(int(float(media.get('duration')) / 1000 / 60))
            else:
                movie_runtime = ""

            if media.get('rating') > 0:
                movie_rating = str(round(float(media.get('rating')), 1))
            else:
                movie_rating = ''

            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Path" % recentMovieCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Title" % recentMovieCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Year" % recentMovieCount, media.get('year', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Rating" % recentMovieCount, movie_rating)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Duration" % recentMovieCount, movie_runtime)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Thumb" % recentMovieCount, title_thumb)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.uuid" % recentMovieCount, libuuid)
            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Plot" % recentMovieCount,
                               media.get('summary', '').encode('UTF-8'))

            m_genre = []

            for child in media:
                if child.tag == "Genre":
                    m_genre.append(child.get('tag'))
                else:
                    continue

            WINDOW.setProperty("Plexbmc.LatestMovie.%s.Genre" % recentMovieCount, ", ".join(m_genre).encode('UTF-8'))

            recentMovieCount += 1


        elif media.get('type') == "season":

            title_name = media.get('parentTitle', 'Unknown').encode('UTF-8')
            printDebug.debug("Found a recent season entry [%s]" % title_name)

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.LatestEpisode.1.Path")
                continue

            title_url = "ActivateWindow(VideoLibrary, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.TVEPISODES)
            title_thumb = _get_shelf_thumb(media, source_server)

            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Path" % recentSeasonCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % recentSeasonCount, '')
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % recentSeasonCount,
                               media.get('title', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % recentSeasonCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Thumb" % recentSeasonCount, title_thumb)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.uuid" % recentSeasonCount,
                               media.get('librarySectionUUID', '').encode('UTF-8'))

            recentSeasonCount += 1

        elif media.get('type') == "album":

            if not settings.get_setting('musicShelf'):
                WINDOW.clearProperty("Plexbmc.LatestAlbum.1.Path")
                continue

            title_name = media.get('parentTitle', 'Unknown').encode('UTF-8')
            title_url = "ActivateWindow(MusicFiles, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.TRACKS)
            title_thumb = _get_shelf_thumb(media, source_server)

            printDebug.debug("Found a recent album entry: [%s]" % title_name)

            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Path" % recentMusicCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Title" % recentMusicCount,
                               media.get('title', 'Unknown').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Artist" % recentMusicCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestAlbum.%s.Thumb" % recentMusicCount, title_thumb)

            recentMusicCount += 1

        elif media.get('type') == "photo":

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            title_url = "ActivateWindow(Pictures, plugin://plugin.video.plexbmc/?url=%s%s&mode=%s,return" % (
                source_server.get_url_location(), "/recentlyAdded", Mode.PHOTOS)
            title_thumb = _get_shelf_thumb(media, source_server)

            printDebug.debug("Found a recent photo entry: [%s]" % title_name)

            WINDOW.setProperty("Plexbmc.LatestPhoto.%s.Path" % recentPhotoCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestPhoto.%s.Title" % recentPhotoCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestPhoto.%s.Thumb" % recentPhotoCount, title_thumb)

            recentPhotoCount += 1

        elif media.get('type') == "episode":

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            printDebug.debug("Found an Recent episode entry [%s]" % title_name)

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.LatestEpisode.1.Path")
                continue

            title_url = "ActivateWindow(Videos, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
                get_link_url(source_server.get_url_location(), media, source_server, season_shelf=True),
                Mode.TVEPISODES)
            title_thumb = _get_shelf_thumb(media, source_server, season_thumb=True, prefer_season=prefer_season)

            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Path" % recentSeasonCount, title_url)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % recentSeasonCount, title_name)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeNumber" % recentSeasonCount,
                               media.get('index', '').encode('utf-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % recentSeasonCount,
                               media.get('parentIndex', '').encode('UTF-8')
                               + '.' + media.get('index', 'Unknown').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.EpisodeSeasonNumber" % recentSeasonCount,
                               media.get('parentIndex', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % recentSeasonCount,
                               media.get('grandparentTitle', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.Thumb" % recentSeasonCount, title_thumb)
            WINDOW.setProperty("Plexbmc.LatestEpisode.%s.uuid" % recentSeasonCount, libuuid)

            recentSeasonCount += 1

        printDebug.debug(
            " Building Recent window title: %s\n    Building Recent window url: %s\n    Building Recent window thumb: %s" % (
                title_name, title_url, title_thumb))

    clear_shelf(recentMovieCount, recentSeasonCount, recentMusicCount, recentPhotoCount)

    #For each of the servers we have identified
    for media, source_server, libuuid in ondeck_list:

        if media.get('type') == "movie":

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            printDebug.debug("Found a OnDeck movie entry: [%s]" % title_name)

            if not settings.get_setting('movieShelf'):
                WINDOW.clearProperty("Plexbmc.OnDeckMovie.1.Path")
                continue

            title_url = "plugin://plugin.video.plexbmc?url=%s&mode=%s&t=%s" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.PLAYSHELF, randomNumber)
            title_thumb = _get_shelf_thumb(media, source_server)

            if media.get('duration') > 0:
                #movie_runtime = media.get('duration', '0')
                movie_runtime = str(int(float(media.get('duration')) / 1000 / 60))
            else:
                movie_runtime = ""

            if media.get('rating') > 0:
                title_rating = str(round(float(media.get('rating')), 1))
            else:
                title_rating = ''

            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Path" % ondeckMovieCount, title_url)
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Title" % ondeckMovieCount, title_name)
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Year" % ondeckMovieCount, media.get('year', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Rating" % ondeckMovieCount, title_rating)
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Duration" % ondeckMovieCount, movie_runtime)
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.Thumb" % ondeckMovieCount, title_thumb)
            WINDOW.setProperty("Plexbmc.OnDeckMovie.%s.uuid" % ondeckMovieCount, libuuid)

            ondeckMovieCount += 1

        elif media.get('type') == "season":

            title_name = media.get('parentTitle', 'Unknown').encode('UTF-8')
            printDebug.debug("Found a OnDeck season entry [%s]" % title_name)

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.OnDeckEpisode.1.Path")
                continue

            title_url = "ActivateWindow(VideoLibrary, plugin://plugin.video.plexbmc?url=%s&mode=%s, return)" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.TVEPISODES)
            title_thumb = _get_shelf_thumb(media, source_server)

            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.Path" % ondeckSeasonCount, title_url)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeTitle" % ondeckSeasonCount, '')
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeSeason" % ondeckSeasonCount,
                               media.get('title', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.ShowTitle" % ondeckSeasonCount, title_name)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.Thumb" % ondeckSeasonCount, title_thumb)

            ondeckSeasonCount += 1

        elif media.get('type') == "episode":

            title_name = media.get('title', 'Unknown').encode('UTF-8')
            printDebug.debug("Found an onDeck episode entry [%s]" % title_name)

            if not settings.get_setting('tvShelf'):
                WINDOW.clearProperty("Plexbmc.OnDeckEpisode.1.Path")
                continue

            title_url = "PlayMedia(plugin://plugin.video.plexbmc?url=%s&mode=%s&t=%s)" % (
                get_link_url(source_server.get_url_location(), media, source_server), Mode.PLAYSHELF, randomNumber)
            title_thumb = _get_shelf_thumb(media, source_server, season_thumb=True, prefer_season=prefer_season)

            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.Path" % ondeckSeasonCount, title_url)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeTitle" % ondeckSeasonCount, title_name)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeNumber" % ondeckSeasonCount,
                               media.get('index', '').encode('utf-8'))
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeSeason" % ondeckSeasonCount,
                               media.get('grandparentTitle', 'Unknown').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.EpisodeSeasonNumber" % ondeckSeasonCount,
                               media.get('parentIndex', '').encode('UTF-8'))
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.ShowTitle" % ondeckSeasonCount, title_name)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.Thumb" % ondeckSeasonCount, title_thumb)
            WINDOW.setProperty("Plexbmc.OnDeckEpisode.%s.uuid" % ondeckSeasonCount, libuuid)

            ondeckSeasonCount += 1

        printDebug.debug(
            " Building onDeck window title: %s\n    Building onDeck window url: %s\n    Building onDeck window thumb: %s" % (
                title_name, title_url, title_thumb))

    clear_on_deck_shelf(ondeckMovieCount, ondeckSeasonCount)


def _get_shelf_thumb(data, server, season_thumb=False, prefer_season=False, width=400, height=400):
    """
        Simply take a URL or path and determine how to format for images
        @ input: elementTree element, server name
        @ return formatted URL
    """

    if season_thumb:
        if prefer_season:
            thumbnail = data.get('parentThumb', data.get('grandparentThumb', '')).split('?t')[0].encode('utf-8')
        else:
            thumbnail = data.get('grandparentThumb', '').split('?t')[0].encode('utf-8')
    else:
        thumbnail = data.get('thumb', '').split('?t')[0].encode('utf-8')

    if thumbnail.startswith("http"):
        return thumbnail

    elif thumbnail.startswith('/'):
        if settings.get_setting('fullres_thumbs'):
            return server.get_kodi_header_formatted_url(thumbnail)
        else:
            return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' % (
                urllib.quote_plus('http://localhost:32400' + thumbnail), width, height))

    return GENERIC_THUMBNAIL


def _clear_queue_shelf(queueCount=0):
    WINDOW = xbmcgui.Window(10000)

    try:
        for i in range(queueCount, 15 + 1):
            WINDOW.clearProperty("Plexbmc.Queue.%s.Path" % ( i ))
            WINDOW.clearProperty("Plexbmc.Queue.%s.Title" % ( i ))
            WINDOW.clearProperty("Plexbmc.Queue.%s.Thumb" % ( i ))
        printDebug.debug("Done clearing Queue shelf")
    except:
        pass

    return