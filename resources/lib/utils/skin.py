import urllib
import xbmcgui
from ..common import AddonSettings, PrintDebug, GENERIC_THUMBNAIL

settings = AddonSettings()
printDebug = PrintDebug("PlexBMC", "utils.skin")


def get_thumb(data, server, width=720, height=720):
    """
        Simply take a URL or path and determine how to format for images
        @ input: elementTree element, server name
        @ return formatted URL
    """

    if settings.get_setting('skipimages'):
        return ''

    thumbnail = data.get('thumb', '').split('?t')[0].encode('utf-8')

    if thumbnail.startswith("http"):
        return thumbnail

    elif thumbnail.startswith('/'):
        if settings.get_setting('fullres_thumbs'):
            return server.get_kodi_header_formatted_url(thumbnail)
        else:
            return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' %
                                                        (urllib.quote_plus('http://localhost:32400' + thumbnail),
                                                         width, height))

    return GENERIC_THUMBNAIL


def clear_shelf(movie_count=0, season_count=0, music_count=0, photo_count=0):
    # Clear out old data
    window = xbmcgui.Window(10000)
    printDebug.debug("Clearing unused properties")

    try:
        for i in range(movie_count, 50 + 1):
            window.clearProperty("Plexbmc.LatestMovie.%s.Path" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.Title" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.Year" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.Rating" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.Duration" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.Thumb" % i)
            window.clearProperty("Plexbmc.LatestMovie.%s.uuid" % i)
        printDebug.debug("Done clearing movies")
    except:
        pass

    try:
        for i in range(season_count, 50 + 1):
            window.clearProperty("Plexbmc.LatestEpisode.%s.Path" % i)
            window.clearProperty("Plexbmc.LatestEpisode.%s.EpisodeTitle" % i)
            window.clearProperty("Plexbmc.LatestEpisode.%s.EpisodeSeason" % i)
            window.clearProperty("Plexbmc.LatestEpisode.%s.ShowTitle" % i)
            window.clearProperty("Plexbmc.LatestEpisode.%s.Thumb" % i)
            window.clearProperty("Plexbmc.LatestEpisode.%s.uuid" % i)
        printDebug.debug("Done clearing tv")
    except:
        pass

    try:
        for i in range(music_count, 25 + 1):
            window.clearProperty("Plexbmc.LatestAlbum.%s.Path" % i)
            window.clearProperty("Plexbmc.LatestAlbum.%s.Title" % i)
            window.clearProperty("Plexbmc.LatestAlbum.%s.Artist" % i)
            window.clearProperty("Plexbmc.LatestAlbum.%s.Thumb" % i)
        printDebug.debug("Done clearing music")
    except:
        pass

    try:
        for i in range(photo_count, 25 + 1):
            window.clearProperty("Plexbmc.LatestPhoto.%s.Path" % i)
            window.clearProperty("Plexbmc.LatestPhoto.%s.Title" % i)
            window.clearProperty("Plexbmc.LatestPhoto.%s.Thumb" % i)
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
