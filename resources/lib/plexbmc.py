"""
    @document   : plexbmc.py
    @package    : PleXBMC add-on
    @author     : Hippojay (aka Dave Hawes-Johnson)
    @copyright  : 2011-2015, Hippojay
    @version    : 4.0 (Helix)

    @license    : Gnu General Public License - see LICENSE.TXT
    @description: pleXBMC XBMC add-on

    This file is part of the XBMC PleXBMC Plugin.

    PleXBMC Plugin is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    PleXBMC Plugin is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with PleXBMC Plugin.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib
import urlparse
import time
import random
import datetime
import sys

import xbmc
import xbmcplugin
import xbmcgui

from .utils import wake_servers, get_link_url
from .utils import get_thumb

from .common import AddonSettings, PrintDebug
from .common import Mode, SubAudioControl, GENERIC_THUMBNAIL, GLOBAL_SETUP
from .plexserver import plex_network, get_master_server

from .commands import COMMANDS, BaseCommand

settings = AddonSettings()


def media_type(part_data, server, dvd_playback=False):
    stream = part_data['key']
    file_name = part_data['file']

    if (file_name is None) or (settings.get_stream() == "1"):
        printDebug.debug("Selecting stream")
        return server.get_formatted_url(stream)

    # First determine what sort of 'file' file is
    if file_name[0:2] == "\\\\":
        printDebug.debug("Detected UNC source file")
        file_type = "UNC"
    elif file_name[0:1] == "/" or file_name[0:1] == "\\":
        printDebug.debug("Detected unix source file")
        file_type = "nixfile"
    elif file_name[1:3] == ":\\" or file_name[1:2] == ":/":
        printDebug.debug("Detected windows source file")
        file_type = "winfile"
    else:
        printDebug.debug("Unknown file type source: %s" % file_name)
        file_type=None

    # 0 is auto select.  basically check for local file first, then stream if not found
    if settings.get_stream() == "0":
        # check if the file can be found locally
        if file_type == "nixfile" or file_type == "winfile":
            printDebug.debug("Checking for local file")
            try:
                exists = open(file_name, 'r')
                printDebug.debug("Local file found, will use this")
                exists.close()
                return "file:%s" % file_name
            except:
                pass

        printDebug.debug("No local file")
        if dvd_playback:
            printDebug.debug("Forcing SMB for DVD playback")
            settings.set_stream("2")
        else:
            return server.get_formatted_url(stream)

    # 2 is use SMB
    elif settings.get_stream() == "2" or settings.get_stream() == "3":

        file_name = urllib.unquote(file_name)
        if settings.get_stream() == "2":
            protocol = "smb"
        else:
            protocol = "afp"

        printDebug.debug("Selecting smb/unc")
        if file_type == "UNC":
            filelocation="%s:%s" % (protocol, file_name.replace("\\", "/"))
        else:
            # Might be OSX type, in which case, remove Volumes and replace with server
            server = server.get_location().split(':')[0]
            loginstring = ""

            if settings.get_setting('nasoverride'):
                if settings.get_setting('nasoverrideip'):
                    server=settings.get_setting('nasoverrideip')
                    printDebug.debug("Overriding server with: %s" % server)

                if settings.get_setting('nasuserid'):
                    loginstring = "%s:%s@" % (settings.get_setting('nasuserid'), settings.get_setting('naspass'))
                    printDebug.debug("Adding AFP/SMB login info for user: %s" % settings.get_setting('nasuserid'))

            if file_name.find('Volumes') > 0:
                filelocation = "%s:/%s" % (protocol, file_name.replace("Volumes", loginstring+server))
            else:
                if file_type == "winfile":
                    filelocation = ("%s://%s%s/%s" % (protocol, loginstring, server, file_name[3:].replace("\\", "/")))
                else:
                    # else assume its a file local to server available over smb/samba
                    # (now we have linux PMS). Add server name to file path.
                    filelocation = "%s://%s%s%s" % (protocol, loginstring, server, file_name)

        if settings.get_setting('nasoverride') and settings.get_setting('nasroot'):
            # Re-root the file path
            printDebug.debug("Altering path %s so root is: %s" % (filelocation, settings.get_setting('nasroot')))
            if '/'+settings.get_setting('nasroot')+'/' in filelocation:
                components = filelocation.split('/')
                index = components.index(settings.get_setting('nasroot'))
                for i in range(3,index):
                    components.pop(3)
                filelocation = '/'.join(components)
    else:
        printDebug.debug("No option detected, streaming is safest to choose")
        filelocation = server.get_formatted_url(stream)

    printDebug.debug("Returning URL: %s " % filelocation)
    return filelocation


def addGUIItem(url, details, extraData, context=None, folder=True):

    printDebug.debug("Adding Dir for [%s]\n      Passed details: %s\n      Passed extraData: %s" % ( details.get('title', 'Unknown'), details, extraData))

    #Create the URL to pass to the item
    if not folder and extraData['type'] == "image" :
        link_url=url
    elif url.startswith('http') or url.startswith('file'):
        link_url="%s?url=%s&mode=%s" % ( sys.argv[0], urllib.quote(url), extraData.get('mode',0))
    else:
        link_url="%s?url=%s&mode=%s" % ( sys.argv[0], url, extraData.get('mode',0))

    if extraData.get('parameters'):
        for argument, value in extraData.get('parameters').items():
            link_url = "%s&%s=%s" % (link_url, argument, urllib.quote(value))

    printDebug.debug("URL to use for listing: %s" % link_url)

    liz=xbmcgui.ListItem(details.get('title', 'Unknown'), thumbnailImage=extraData.get('thumb', GENERIC_THUMBNAIL))

    printDebug.debug("Setting thumbnail as %s" % extraData.get('thumb', GENERIC_THUMBNAIL))

    #Set the properties of the item, such as summary, name, season, etc
    liz.setInfo(type=extraData.get('type','Video'), infoLabels=details )

    #Music related tags
    if extraData.get('type','').lower() == "music":
        liz.setProperty('Artist_Genre', details.get('genre',''))
        liz.setProperty('Artist_Description', extraData.get('plot',''))
        liz.setProperty('Album_Description', extraData.get('plot',''))

    #For all end items
    if not folder:
        liz.setProperty('IsPlayable', 'true')

        if extraData.get('type','video').lower() == "video":
            liz.setProperty('TotalTime', str(extraData.get('duration')))
            liz.setProperty('ResumeTime', str(extraData.get('resume')))

            if not settings.get_setting('skipflags'):
                printDebug.debug("Setting VrR as : %s" % extraData.get('VideoResolution',''))
                liz.setProperty('VideoResolution', extraData.get('VideoResolution',''))
                liz.setProperty('VideoCodec', extraData.get('VideoCodec',''))
                liz.setProperty('AudioCodec', extraData.get('AudioCodec',''))
                liz.setProperty('AudioChannels', extraData.get('AudioChannels',''))
                liz.setProperty('VideoAspect', extraData.get('VideoAspect',''))

                video_codec={}
                if extraData.get('xbmc_VideoCodec'): video_codec['codec'] = extraData.get('xbmc_VideoCodec')
                if extraData.get('xbmc_VideoAspect') : video_codec['aspect'] = float(extraData.get('xbmc_VideoAspect'))
                if extraData.get('xbmc_height') : video_codec['height'] = int(extraData.get('xbmc_height'))
                if extraData.get('xbmc_width') : video_codec['width'] = int(extraData.get('xbmc_width'))
                if extraData.get('duration') : video_codec['duration'] = int(extraData.get('duration'))

                audio_codec={}
                if extraData.get('xbmc_AudioCodec') : audio_codec['codec'] = extraData.get('xbmc_AudioCodec')
                if extraData.get('xbmc_AudioChannels') : audio_codec['channels'] = int(extraData.get('xbmc_AudioChannels'))

                liz.addStreamInfo('video', video_codec )
                liz.addStreamInfo('audio', audio_codec )

    if extraData.get('source') == 'tvshows' or extraData.get('source') =='tvseasons':
        #Then set the number of watched and unwatched, which will be displayed per season
        liz.setProperty('TotalEpisodes', str(extraData['TotalEpisodes']))
        liz.setProperty('WatchedEpisodes', str(extraData['WatchedEpisodes']))
        liz.setProperty('UnWatchedEpisodes', str(extraData['UnWatchedEpisodes']))

        #Hack to show partial flag for TV shows and seasons
        if extraData.get('partialTV') == 1:
            liz.setProperty('TotalTime', '100')
            liz.setProperty('ResumeTime', '50')

    #fanart is nearly always available, so exceptions are rare.
    try:
        liz.setProperty('fanart_image', extraData.get('fanart_image'))
        printDebug.debug("Setting fan art as %s" % extraData.get('fanart_image'))
    except:
        printDebug.debug("Skipping fanart as None found")

    if extraData.get('banner'):
        liz.setProperty('banner', '%s' % extraData.get('banner', ''))
        printDebug.debug("Setting banner as %s" % extraData.get('banner', ''))

    if extraData.get('season_thumb'):
        liz.setProperty('seasonThumb', '%s' % extraData.get('season_thumb', ''))
        printDebug.debug("Setting season Thumb as %s" % extraData.get('season_thumb', ''))

    if context is not None:
        if not folder and extraData.get('type','video').lower() == "video":
            #Play Transcoded
            context.insert(0,('Play Transcoded', "XBMC.PlayMedia(%s&transcode=1)" % link_url , ))
            printDebug.debug("Setting transcode options to [%s&transcode=1]" % link_url)
        printDebug.debug("Building Context Menus")
        liz.addContextMenuItems( context, settings.get_setting('contextreplace') )

    return xbmcplugin.addDirectoryItem(handle=pluginhandle,url=link_url,listitem=liz,isFolder=folder)

def displaySections( filter=None, display_shared=False ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'files')

    server_list=plex_network.get_server_list()
    printDebug.debug( "Using list of %s servers: %s" % ( len(server_list), server_list))

    for server in server_list:

        server.discover_sections()

        for section in server.get_sections():

            if display_shared and server.is_owned():
                continue

            details={'title' : section.get_title() }

            if len(server_list) > 1:
                details['title']="%s: %s" % (server.get_name(), details['title'])

            extraData={ 'fanart_image' : server.get_fanart(section),
                        'type'         : "Video"}

            #Determine what we are going to do process after a link is selected by the user, based on the content we find

            path=section.get_path()

            if section.is_show():
                mode=Mode.TVSHOWS
                if (filter is not None) and (filter != "tvshows"):
                    continue

            elif section.is_movie():
                mode=Mode.MOVIES
                if (filter is not None) and (filter != "movies"):
                    continue

            elif section.is_artist():
                mode=Mode.ARTISTS
                if (filter is not None) and (filter != "music"):
                    continue

            elif section.is_photo():
                mode=Mode.PHOTOS
                if (filter is not None) and (filter != "photos"):
                    continue
            else:
                printDebug.debug("Ignoring section %s of type %s as unable to process" % ( details['title'], section.get_type() ) )
                continue

            if settings.get_setting('secondary'):
                mode=Mode.GETCONTENT
            else:
                path=path+'/all'

            extraData['mode']=mode
            section_url='%s%s' % ( server.get_url_location(), path)

            if not settings.get_setting('skipcontextmenus'):
                context=[]
                context.append(('Refresh library section', 'RunScript(plugin.video.plexbmc, update, %s, %s)' % (server.get_uuid(), section.get_key()) ))
            else:
                context=None

            #Build that listing..
            addGUIItem(section_url, details,extraData, context)

    if display_shared:
        xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=settings.get_setting('kodicache'))
        return

    #For each of the servers we have identified
    if plex_network.is_myplex_signedin():
        addGUIItem('http://myplexqueue', {'title': 'myplex Queue'}, {'type': 'Video', 'mode': Mode.MYPLEXQUEUE})

    for server in server_list:

        if server.is_offline() or server.is_secondary():
            continue

        #Plex plugin handling
        if (filter is not None) and (filter != "plugins"):
            continue

        if len(server_list) > 1:
            prefix=server.get_name()+": "
        else:
            prefix=""

        details={'title' : prefix+"Channels" }
        extraData={'type' : "Video"}

        extraData['mode']=Mode.CHANNELVIEW
        u="%s/channels/all" % server.get_url_location()
        addGUIItem(u,details,extraData)

        #Create plexonline link
        details['title']=prefix+"Plex Online"
        extraData['type'] = "file"
        extraData['mode'] = Mode.PLEXONLINE

        u="%s/system/plexonline" % server.get_url_location()
        addGUIItem(u,details,extraData)

        #create playlist link
        details['title']=prefix+"Playlists"
        extraData['type'] = "file"
        extraData['mode'] = Mode.PLAYLISTS

        u="%s/playlists" % server.get_url_location()
        addGUIItem(u,details,extraData)

    if plex_network.is_myplex_signedin():

        if plex_network.is_plexhome_enabled():
            details = {'title' : "Switch User"}
            extraData = {'type' : 'file'}

            u="cmd:switchuser"
            addGUIItem(u,details,extraData)

        details = {'title' : "Sign Out"}
        extraData = {'type' : 'file'}

        u="cmd:signout"
        addGUIItem(u,details,extraData)
    else:
        details = {'title' : "Sign In"}
        extraData = {'type' : 'file'}

        u="cmd:signintemp"
        addGUIItem(u,details,extraData)

    if settings.get_setting('cache'):
        details = {'title' : "Refresh Data"}
        extraData = {}
        extraData['type']="file"

        extraData['mode']= Mode.DELETE_REFRESH

        u="http://nothing"
        addGUIItem(u,details,extraData)

    #All XML entries have been parsed and we are ready to allow the user to browse around.  So end the screen listing.
    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=settings.get_setting('kodicache'))

def enforceSkinView(mode):

    """
    Ensure that the views are consistance across plugin usage, depending
    upon view selected by user
    @input: User view selection
    @return: view id for skin
    """

    printDebug.debug("== ENTER ==")

    if not settings.get_setting('skinoverride'):
        return None

    skinname = settings.get_setting('skinname')

    current_skin_name = xbmc.getSkinDir()

    skin_map = { '2' : 'skin.confluence' ,
                 '0' : 'skin.quartz' ,
                 '1' : 'skin.quartz3' ,
                 '3' : 'skin.amber',
                 '4' : 'skin.aeon.nox.5' }

    if skin_map[skinname] not in current_skin_name:
        printDebug.debug("Do not have the correct skin [%s] selected in settings [%s] - ignoring" % (current_skin_name, skin_map[skinname]))
        return None

    if mode == "movie":
        printDebug.debug("Looking for movie skin settings")
        viewname = settings.get_setting('mo_view_%s' % skinname)

    elif mode == "tv":
        printDebug.debug("Looking for tv skin settings")
        viewname = settings.get_setting('tv_view_%s' % skinname)

    elif mode == "music":
        printDebug.debug("Looking for music skin settings")
        viewname = settings.get_setting('mu_view_%s' % skinname)

    elif mode == "episode":
        printDebug.debug("Looking for music skin settings")
        viewname = settings.get_setting('ep_view_%s' % skinname)

    elif mode == "season":
        printDebug.debug("Looking for music skin settings")
        viewname = settings.get_setting('se_view_%s' % skinname)

    else:
        viewname = "None"

    printDebug.debug("view name is %s" % viewname)

    if viewname == "None":
        return None

    QuartzV3_views={ 'List' : 50,
                     'Big List' : 51,
                     'MediaInfo' : 52,
                     'MediaInfo 2' : 54,
                     'Big Icons' : 501,
                     'Icons': 53,
                     'Panel' : 502,
                     'Wide' : 55,
                     'Fanart 1' : 57,
                     'Fanart 2' : 59,
                     'Fanart 3' : 500 }

    Quartz_views={ 'List' : 50,
                   'MediaInfo' : 51,
                   'MediaInfo 2' : 52,
                   'Icons': 53,
                   'Wide' : 54,
                   'Big Icons' : 55,
                   'Icons 2' : 56 ,
                   'Panel' : 57,
                   'Fanart' : 58,
                   'Fanart 2' : 59 }

    Confluence_views={ 'List' : 50,
                       'Big List' : 51,
                       'Thumbnail' : 500,
                       'Poster Wrap': 501,
                       'Fanart' : 508,
                       'Media Info' : 504,
                       'Media Info 2' : 503,
                       'Media Info 3' : 515,
                       'Wide Icons' : 505 }

    Amber_views = {  'List' : 50,
                       'Big List' : 52,
                       'Panel': 51,
                       'Low List' : 54,
                       'Icons' : 53,
                       'Big Panel' : 55,
                       'Fanart' : 59 }

    aeon_nox_views = { 'List'       : 50  ,
                       'InfoWall'   : 51  ,
                       'Landscape'  : 52  ,
                       'ShowCase1'  : 53  ,
                       'ShowCase2'  : 54  ,
                       'TriPanel'   : 55  ,
                       'Posters'    : 56  ,
                       'Shift'      : 57  ,
                       'BannerWall' : 58  ,
                       'Logo'       : 59  ,
                       'Wall'       : 500 ,
                       'LowList'    : 501 ,
                       'Episode'    : 502 ,
                       'Wall'       : 503 ,
                       'BigList'    : 510 }

    skin_list={"0" : Quartz_views ,
               "1" : QuartzV3_views,
               "2" : Confluence_views,
               "3" : Amber_views,
               "4" : aeon_nox_views }

    printDebug.debug("Using skin view: %s" % skin_list[skinname][viewname])

    try:
        return skin_list[skinname][viewname]
    except:
        print "PleXBMC -> skin name or view name error"
        return None

def Movies( url, tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'movies')

    xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    xbmcplugin.addSortMethod(pluginhandle, 25 ) #video title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 19 )  #date added
    xbmcplugin.addSortMethod(pluginhandle, 3 )  #date
    xbmcplugin.addSortMethod(pluginhandle, 18 ) #rating
    xbmcplugin.addSortMethod(pluginhandle, 17 ) #year
    xbmcplugin.addSortMethod(pluginhandle, 29 ) #runtime
    xbmcplugin.addSortMethod(pluginhandle, 28 ) #by MPAA

    #get the server name from the URL, which was passed via the on screen listing..

    server=plex_network.get_server_from_url(url)

    tree=getXML(url,tree)
    if tree is None:
        return

    setWindowHeading(tree)
    randomNumber=str(random.randint(1000000000,9999999999))

    #Find all the video tags, as they contain the data we need to link to a file.
    start_time=time.time()
    count=0
    for movie in tree:

        if movie.tag == "Video":
            movieTag(url, server, tree, movie, randomNumber)
            count+=1

    printDebug.info("PROCESS: It took %s seconds to process %s items" % (time.time()-start_time, count))
    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('movie')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=settings.get_setting('kodicache'))

def buildContextMenu( url, itemData, server ):
    context=[]
    url_parts = urlparse.urlparse(url)
    section=url_parts.path.split('/')[3]
    ID=itemData.get('ratingKey','0')

    #Mark media unwatched
    context.append(('Mark as Unwatched', 'RunScript(plugin.video.plexbmc, watch, %s, %s, %s)' % ( server.get_uuid(), ID, 'unwatch' ) ))
    context.append(('Mark as Watched', 'RunScript(plugin.video.plexbmc, watch, %s, %s, %s)' % ( server.get_uuid(), ID, 'watch' ) ))
    context.append(('Rescan library section', 'RunScript(plugin.video.plexbmc, update, %s, %s)' % ( server.get_uuid(), section ) ))
    context.append(('Delete media', "RunScript(plugin.video.plexbmc, delete, %s, %s)" % ( server.get_uuid(), ID) ))
    context.append(('Reload Section', 'RunScript(plugin.video.plexbmc, refresh)' ))
    context.append(('Select Audio', "RunScript(plugin.video.plexbmc, audio, %s, %s)" % ( server.get_uuid(), ID) ))
    context.append(('Select Subtitle', "RunScript(plugin.video.plexbmc, subs, %s, %s)" % ( server.get_uuid(), ID) ))

    printDebug.debug("Using context menus: %s" % context)

    return context

def TVShows( url, tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'tvshows')
    xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    xbmcplugin.addSortMethod(pluginhandle, 25 ) #video title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 3 )  #date
    xbmcplugin.addSortMethod(pluginhandle, 18 ) #rating
    xbmcplugin.addSortMethod(pluginhandle, 17 ) #year
    xbmcplugin.addSortMethod(pluginhandle, 28 ) #by MPAA

    #Get the URL and server name.  Get the XML and parse
    tree=getXML(url,tree)
    if tree is None:
        return

    server=plex_network.get_server_from_url(url)

    setWindowHeading(tree)
    #For each directory tag we find
    ShowTags=tree.findall('Directory')
    for show in ShowTags:

        tempgenre=[]

        for child in show:
            if child.tag == "Genre":
                        tempgenre.append(child.get('tag',''))

        watched = int(show.get('viewedLeafCount',0))

        #Create the basic data structures to pass up
        details={'title'      : show.get('title','Unknown').encode('utf-8') ,
                 'sorttitle'  : show.get('titleSort', show.get('title','Unknown')).encode('utf-8') ,
                 'tvshowname' : show.get('title','Unknown').encode('utf-8') ,
                 'studio'     : show.get('studio','').encode('utf-8') ,
                 'plot'       : show.get('summary','').encode('utf-8') ,
                 'season'     : 0 ,
                 'episode'    : int(show.get('leafCount',0)) ,
                 'mpaa'       : show.get('contentRating','') ,
                 'aired'      : show.get('originallyAvailableAt','') ,
                 'genre'      : " / ".join(tempgenre) }

        extraData={'type'              : 'video' ,
                   'source'            : 'tvshows',
                   'UnWatchedEpisodes' : int(details['episode']) - watched,
                   'WatchedEpisodes'   : watched,
                   'TotalEpisodes'     : details['episode'],
                   'thumb'             : get_thumb(show, server) ,
                   'fanart_image'      : getFanart(show, server) ,
                   'key'               : show.get('key','') ,
                   'ratingKey'         : str(show.get('ratingKey',0)) }

        #banner art
        if show.get('banner') is not None:
            extraData['banner'] = server.get_url_location()+show.get('banner')
        else:
            extraData['banner'] = GENERIC_THUMBNAIL

        #Set up overlays for watched and unwatched episodes
        if extraData['WatchedEpisodes'] == 0:
            details['playcount'] = 0
        elif extraData['UnWatchedEpisodes'] == 0:
            details['playcount'] = 1
        else:
            extraData['partialTV'] = 1

        #Create URL based on whether we are going to flatten the season view
        if settings.get_setting('flatten') == "2":
            printDebug.debug("Flattening all shows")
            extraData['mode']=Mode.TVEPISODES
            u='%s%s'  % ( server.get_url_location(), extraData['key'].replace("children","allLeaves"))
        else:
            extraData['mode']=Mode.TVSEASONS
            u='%s%s'  % ( server.get_url_location(), extraData['key'])

        if not settings.get_setting('skipcontextmenus'):
            context=buildContextMenu(url, extraData, server)
        else:
            context=None

        addGUIItem(u,details,extraData, context)

    printDebug ("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('tv')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=settings.get_setting('kodicache'))

def TVSeasons( url ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'seasons')

    #Get URL, XML and parse
    server=plex_network.get_server_from_url(url)
    tree=getXML(url)
    if tree is None:
        return

    willFlatten=False
    if settings.get_setting('flatten') == "1":
        #check for a single season
        if int(tree.get('size',0)) == 1:
            printDebug.debug("Flattening single season show")
            willFlatten=True

    sectionart=getFanart(tree, server)
    banner=tree.get('banner')
    setWindowHeading(tree)
    #For all the directory tags
    SeasonTags=tree.findall('Directory')
    plot=tree.get('summary','').encode('utf-8')
    for season in SeasonTags:

        if willFlatten:
            url=server.get_url_location()+season.get('key')
            TVEpisodes(url)
            return

        if settings.get_setting('disable_all_season') and season.get('index') is None:
            continue

        watched=int(season.get('viewedLeafCount',0))

        #Create the basic data structures to pass up
        details={'title'      : season.get('title','Unknown').encode('utf-8') ,
                 'tvshowname' : season.get('title','Unknown').encode('utf-8') ,
                 'sorttitle'  : season.get('titleSort', season.get('title','Unknown')).encode('utf-8') ,
                 'studio'     : season.get('studio','').encode('utf-8') ,
                 'plot'       : plot ,
                 'season'     : 0 ,
                 'episode'    : int(season.get('leafCount',0)) ,
                 'mpaa'       : season.get('contentRating','') ,
                 'aired'      : season.get('originallyAvailableAt','') }

        if season.get('sorttitle'): details['sorttitle'] = season.get('sorttitle')

        extraData={'type'              : 'video' ,
                   'source'            : 'tvseasons',
                   'TotalEpisodes'     : details['episode'],
                   'WatchedEpisodes'   : watched ,
                   'UnWatchedEpisodes' : details['episode'] - watched ,
                   'thumb'             : get_thumb(season, server) ,
                   'fanart_image'      : getFanart(season, server) ,
                   'key'               : season.get('key','') ,
                   'ratingKey'         : str(season.get('ratingKey',0)) ,
                   'mode'              : Mode.TVEPISODES }

        if banner:
            extraData['banner']=server.get_url_location()+banner

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=sectionart

        #Set up overlays for watched and unwatched episodes
        if extraData['WatchedEpisodes'] == 0:
            details['playcount'] = 0
        elif extraData['UnWatchedEpisodes'] == 0:
            details['playcount'] = 1
        else:
            extraData['partialTV'] = 1

        url='%s%s' % ( server.get_url_location() , extraData['key'] )

        if not settings.get_setting('skipcontextmenus'):
            context=buildContextMenu(url, season, server)
        else:
            context=None

        #Build the screen directory listing
        addGUIItem(url,details,extraData, context)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('season')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def TVEpisodes( url, tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'episodes')

    tree=getXML(url,tree)
    if tree is None:
        return

    setWindowHeading(tree)

    #get banner thumb
    banner = tree.get('banner')

    #get season thumb for SEASON NODE
    season_thumb = tree.get('thumb', '')

    ShowTags=tree.findall('Video')
    server=plex_network.get_server_from_url(url)

    if not settings.get_setting('skipimages'):
        sectionart=getFanart(tree, server)

    randomNumber=str(random.randint(1000000000,9999999999))

    if tree.get('mixedParents') == '1':
        printDebug.info('Setting plex sort')
        xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    else:
        printDebug.info('Setting KODI sort')
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE )  #episode

    xbmcplugin.addSortMethod(pluginhandle, 3 )  #date
    xbmcplugin.addSortMethod(pluginhandle, 25 ) #video title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 19 )  #date added
    xbmcplugin.addSortMethod(pluginhandle, 18 ) #rating
    xbmcplugin.addSortMethod(pluginhandle, 17 ) #year
    xbmcplugin.addSortMethod(pluginhandle, 29 ) #runtime
    xbmcplugin.addSortMethod(pluginhandle, 28 ) #by MPAA

    for episode in ShowTags:

        printDebug.debug("---New Item---")
        tempgenre=[]
        tempcast=[]
        tempdir=[]
        tempwriter=[]

        for child in episode:
            if child.tag == "Media":
                mediaarguments = dict(child.items())
            elif child.tag == "Genre" and not settings.get_setting('skipmetadata'):
                tempgenre.append(child.get('tag'))
            elif child.tag == "Writer"  and not settings.get_setting('skipmetadata'):
                tempwriter.append(child.get('tag'))
            elif child.tag == "Director"  and not settings.get_setting('skipmetadata'):
                tempdir.append(child.get('tag'))
            elif child.tag == "Role"  and not settings.get_setting('skipmetadata'):
                tempcast.append(child.get('tag'))

        printDebug.debug("Media attributes are %s" % mediaarguments)

        #Gather some data
        view_offset=episode.get('viewOffset',0)
        duration=int(mediaarguments.get('duration',episode.get('duration',0)))/1000

        #Required listItem entries for XBMC
        details={'plot'        : episode.get('summary','').encode('utf-8') ,
                 'title'       : episode.get('title','Unknown').encode('utf-8') ,
                 'sorttitle'   : episode.get('titleSort', episode.get('title','Unknown')).encode('utf-8')  ,
                 'rating'      : float(episode.get('rating',0)) ,
                 'studio'      : episode.get('studio',tree.get('studio','')).encode('utf-8') ,
                 'mpaa'        : episode.get('contentRating', tree.get('grandparentContentRating','')) ,
                 'year'        : int(episode.get('year',0)) ,
                 'tagline'     : episode.get('tagline','').encode('utf-8') ,
                 'episode'     : int(episode.get('index',0)) ,
                 'aired'       : episode.get('originallyAvailableAt','') ,
                 'tvshowtitle' : episode.get('grandparentTitle',tree.get('grandparentTitle','')).encode('utf-8') ,
                 'season'      : int(episode.get('parentIndex',tree.get('parentIndex',0))) }

        if episode.get('sorttitle'):
            details['sorttitle'] = episode.get('sorttitle').encode('utf-8')

        if tree.get('mixedParents') == '1':
            if tree.get('parentIndex') == '1':
                details['title'] = "%sx%s %s" % ( details['season'], str(details['episode']).zfill(2), details['title'] )
            else:
                details['title'] = "%s - %sx%s %s" % ( details['tvshowtitle'], details['season'], str(details['episode']).zfill(2), details['title'] )

        #Extra data required to manage other properties
        extraData={'type'         : "Video" ,
                   'source'       : 'tvepisodes',
                   'thumb'        : get_thumb(episode, server) ,
                   'fanart_image' : getFanart(episode, server) ,
                   'key'          : episode.get('key',''),
                   'ratingKey'    : str(episode.get('ratingKey',0)),
                   'duration'     : duration,
                   'resume'       : int(int(view_offset)/1000) }

        if extraData['fanart_image'] == "" and not settings.get_setting('skipimages'):
            extraData['fanart_image'] = sectionart

        if season_thumb:
            extraData['season_thumb'] = server.get_url_location() + season_thumb

        #get ALL SEASONS thumb
        if not season_thumb and episode.get('parentThumb', ""):
            extraData['season_thumb'] = "%s%s" % (server.get_url_location(), episode.get('parentThumb', ""))

        if banner:
            extraData['banner'] = "%s%s" % (server.get_url_location(), banner)

        #Determine what tupe of watched flag [overlay] to use
        if int(episode.get('viewCount',0)) > 0:
            details['playcount'] = 1
        else:
            details['playcount'] = 0

        #Extended Metadata
        if not settings.get_setting('skipmetadata'):
            details['cast']     = tempcast
            details['director'] = " / ".join(tempdir)
            details['writer']   = " / ".join(tempwriter)
            details['genre']    = " / ".join(tempgenre)

        #Add extra media flag data
        if not settings.get_setting('skipflags'):
            extraData.update(getMediaData(mediaarguments))

        #Build any specific context menu entries
        if not settings.get_setting('skipcontextmenus'):
            context=buildContextMenu(url, extraData,server)
        else:
            context=None

        extraData['mode']=Mode.PLAYLIBRARY
        separator = "?"
        if "?" in extraData['key']:
            separator = "&"
        u="%s%s%st=%s" % (server.get_url_location(), extraData['key'], separator, randomNumber)

        addGUIItem(u,details,extraData, context, folder=False)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('episode')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def getAudioSubtitlesMedia( server, tree, full=False ):
    """
        Cycle through the Parts sections to find all "selected" audio and subtitle streams
        If a stream is marked as selected=1 then we will record it in the dict
        Any that are not, are ignored as we do not need to set them
        We also record the media locations for playback decision later on
    """
    printDebug.debug("== ENTER ==")
    printDebug.debug("Gather media stream info" )

    parts=[]
    partsCount=0
    subtitle={}
    subCount=0
    audio={}
    audioCount=0
    media={}
    subOffset=-1
    audioOffset=-1
    selectedSubOffset=-1
    selectedAudioOffset=-1
    full_data={}
    contents="type"
    media_type="unknown"
    extra={}

    timings = tree.find('Video')
    if timings is not None:
        media_type="video"
        extra['path']=timings.get('key')
    else:
        timings = tree.find('Track')
        if timings:
            media_type="music"
            extra['path']=timings.get('key')
        else:
            timings = tree.find('Photo')
            if timings:
                media_type="picture"
                extra['path']=timings.get('key')
            else:
                printDebug.debug("No Video data found")
                return {}

    media['viewOffset']=timings.get('viewOffset',0)
    media['duration']=timings.get('duration',12*60*60)

    if full:
        if media_type == "video":
            full_data={ 'plot'      : timings.get('summary','').encode('utf-8') ,
                        'title'     : timings.get('title','Unknown').encode('utf-8') ,
                        'sorttitle' : timings.get('titleSort', timings.get('title','Unknown')).encode('utf-8') ,
                        'rating'    : float(timings.get('rating',0)) ,
                        'studio'    : timings.get('studio','').encode('utf-8'),
                        'mpaa'      : timings.get('contentRating', '').encode('utf-8'),
                        'year'      : int(timings.get('year',0)) ,
                        'tagline'   : timings.get('tagline','') ,
                        'thumbnailImage': get_thumb(timings,server) }

            if timings.get('type') == "episode":
                full_data['episode']     = int(timings.get('index',0))
                full_data['aired']       = timings.get('originallyAvailableAt','')
                full_data['tvshowtitle'] = timings.get('grandparentTitle',tree.get('grandparentTitle','')).encode('utf-8')
                full_data['season']      = int(timings.get('parentIndex',tree.get('parentIndex',0)))

        elif media_type == "music":

            full_data={'TrackNumber' : int(timings.get('index',0)) ,
                       'title'       : str(timings.get('index',0)).zfill(2)+". "+timings.get('title','Unknown').encode('utf-8') ,
                       'rating'      : float(timings.get('rating',0)) ,
                       'album'       : timings.get('parentTitle', tree.get('parentTitle','')).encode('utf-8') ,
                       'artist'      : timings.get('grandparentTitle', tree.get('grandparentTitle','')).encode('utf-8') ,
                       'duration'    : int(timings.get('duration',0))/1000 ,
                       'thumbnailImage': get_thumb(timings,server) }

            extra['album']=timings.get('parentKey')
            extra['index']=timings.get('index')

    details = timings.findall('Media')

    media_details_list=[]
    for media_details in details:

        resolution=""
        try:
            if media_details.get('videoResolution') == "sd":
                resolution="SD"
            elif int(media_details.get('videoResolution',0)) >= 1080:
                resolution="HD 1080"
            elif int(media_details.get('videoResolution',0)) >= 720:
                resolution="HD 720"
            elif int(media_details.get('videoResolution',0)) < 720:
                resolution="SD"
        except:
            pass

        media_details_temp = { 'bitrate'          : round(float(media_details.get('bitrate',0))/1000,1) ,
                               'videoResolution'  : resolution ,
                               'container'        : media_details.get('container','unknown') }

        options = media_details.findall('Part')

        #Get the media locations (file and web) for later on
        for stuff in options:

            try:
                bits=stuff.get('key'), stuff.get('file')
                parts.append(bits)
                media_details_list.append(media_details_temp)
                partsCount += 1
            except: pass

    #if we are deciding internally or forcing an external subs file, then collect the data
    if media_type == "video" and settings.get_setting('streamControl') == SubAudioControl.PLEX_CONTROL:

        contents="all"
        tags=tree.getiterator('Stream')

        for bits in tags:
            stream=dict(bits.items())

            #Audio Streams
            if stream['streamType'] == '2':
                audioCount += 1
                audioOffset += 1
                if stream.get('selected') == "1":
                    printDebug.debug("Found preferred audio id: %s " % stream['id'] )
                    audio=stream
                    selectedAudioOffset=audioOffset

            #Subtitle Streams
            elif stream['streamType'] == '3':

                if subOffset == -1:
                    subOffset = int(stream.get('index',-1))
                elif stream.get('index',-1) > 0 and stream.get('index',-1) < subOffset:
                    subOffset = int(stream.get('index',-1))

                if stream.get('selected') == "1":
                    printDebug.debug( "Found preferred subtitles id : %s " % stream['id'])
                    subCount += 1
                    subtitle=stream
                    if stream.get('key'):
                        subtitle['key'] = server.get_formatted_url(stream['key'])
                    else:
                        selectedSubOffset=int( stream.get('index') ) - subOffset

    else:
            printDebug.debug( "Stream selection is set OFF")

    streamData={'contents'   : contents ,                #What type of data we are holding
                'audio'      : audio ,                   #Audio data held in a dict
                'audioCount' : audioCount ,              #Number of audio streams
                'subtitle'   : subtitle ,                #Subtitle data (embedded) held as a dict
                'subCount'   : subCount ,                #Number of subtitle streams
                'parts'      : parts ,                   #The differet media locations
                'partsCount' : partsCount ,              #Number of media locations
                'media'      : media ,                   #Resume/duration data for media
                'details'    : media_details_list ,      #Bitrate, resolution and container for each part
                'subOffset'  : selectedSubOffset ,       #Stream index for selected subs
                'audioOffset': selectedAudioOffset ,     #STream index for select audio
                'full_data'  : full_data ,               #Full metadata extract if requested
                'type'       : media_type ,              #Type of metadata
                'extra'      : extra }                   #Extra data

    printDebug.debug( streamData )
    return streamData

def playPlaylist ( server, data ):
    printDebug.debug("== ENTER ==")
    printDebug.debug("Creating new playlist")
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()

    tree = getXML(server.get_url_location()+data['extra'].get('album')+"/children")

    if tree is None:
        return

    TrackTags=tree.findall('Track')
    for track in TrackTags:

        printDebug.debug("Adding playlist item")

        url, item = trackTag(server, tree, track, listing = False)

        liz=xbmcgui.ListItem(item.get('title','Unknown'), iconImage=data['full_data'].get('thumbnailImage','') , thumbnailImage=data['full_data'].get('thumbnailImage',''))

        liz.setInfo( type='music', infoLabels=item )
        playlist.add(url, liz)

    index = int(data['extra'].get('index',0)) - 1
    printDebug.debug("Playlist complete.  Starting playback from track %s [playlist index %s] " % (data['extra'].get('index',0), index ))
    xbmc.Player().playselected( index )



    return

def playLibraryMedia( vids, override=False, force=None, full_data=False, shelf=False ):

    session=None
    if settings.get_setting('transcode'):
        override=True

    if override:
        full_data = True

    server=plex_network.get_server_from_url(vids)

    id=vids.split('?')[0].split('&')[0].split('/')[-1]

    tree=getXML(vids)
    if tree is None:
        return

    if force:
        full_data = True

    streams=getAudioSubtitlesMedia(server,tree, full_data)

    if force and streams['type'] == "music":
        playPlaylist(server, streams)
        return

    url=selectMedia(streams, server)

    if url is None:
        return

    protocol=url.split(':',1)[0]

    if protocol == "file":
        printDebug.debug( "We are playing a local file")
        playurl=url.split(':',1)[1]
    elif protocol == "http":
        printDebug.debug( "We are playing a stream")
        if override:
            printDebug.debug( "We will be transcoding the stream")
            if settings.get_setting('transcode_type') == "universal":
                session, playurl=server.get_universal_transcode(streams['extra']['path'])
            elif settings.get_setting('transcode_type') == "legacy":
                session, playurl=server.get_legacy_transcode(id,url)

        else:
            playurl=server.get_formatted_url(url)
    else:
        playurl=url

    resume=int(int(streams['media']['viewOffset'])/1000)
    duration=int(int(streams['media']['duration'])/1000)

    if not resume == 0 and shelf:
        printDebug.debug("Shelf playback: display resume dialog")
        displayTime = str(datetime.timedelta(seconds=resume))
        display_list = [ "Resume from %s" % displayTime , "Start from beginning"]
        resumeScreen = xbmcgui.Dialog()
        result = resumeScreen.select('Resume',display_list)
        if result == -1:
            return False

        if result == 1:
           resume=0

    printDebug.debug("Resume has been set to %s " % resume)

    item = xbmcgui.ListItem(path=playurl)

    if streams['full_data']:
        item.setInfo( type=streams['type'], infoLabels=streams['full_data'] )
        item.setThumbnailImage(streams['full_data'].get('thumbnailImage',''))
        item.setIconImage(streams['full_data'].get('thumbnailImage',''))

    if force:

        if int(force) > 0:
            resume=int(int(force)/1000)
        else:
            resume=force

    if force or shelf or session is not None:
        if resume:
            item.setProperty('ResumeTime', str(resume) )
            item.setProperty('TotalTime', str(duration) )
            printDebug.info("Playback from resume point: %s" % resume)

    if streams['type'] == "picture":
        import json
        request=json.dumps({ "id"      : 1,
                             "jsonrpc" : "2.0",
                             "method"  : "Player.Open",
                             "params"  : { "item"  :  {"file": playurl } } } )
        html=xbmc.executeJSONRPC(request)
        return
    else:
        start = xbmcplugin.setResolvedUrl(pluginhandle, True, item)

    # record the playing file and server in the home window
    # so that plexbmc helper can find out what is playing
    WINDOW = xbmcgui.Window( 10000 )
    WINDOW.setProperty('plexbmc.nowplaying.server', server.get_location())
    WINDOW.setProperty('plexbmc.nowplaying.id', id)

    #Set a loop to wait for positive confirmation of playback
    count = 0
    while not xbmc.Player().isPlaying():
        printDebug.debug( "Not playing yet...sleep for 2")
        count = count + 2
        if count >= 20:
            return
        else:
            time.sleep(2)

    if not override:
        setAudioSubtitles(streams)

    if streams['type'] == "video" or streams['type'] == "music":
        monitorPlayback(id,server, playurl, session)

    return

def setAudioSubtitles( stream ):
    """
        Take the collected audio/sub stream data and apply to the media
        If we do not have any subs then we switch them off
    """

    printDebug.debug("== ENTER ==")

    #If we have decided not to collect any sub data then do not set subs
    if stream['contents'] == "type":
        printDebug.info("No audio or subtitle streams to process.")

        #If we have decided to force off all subs, then turn them off now and return
        if settings.get_setting('streamControl') == SubAudioControl.NEVER_SHOW :
            xbmc.Player().showSubtitles(False)
            printDebug ("All subs disabled")

        return True

    #Set the AUDIO component
    if settings.get_setting('streamControl') == SubAudioControl.PLEX_CONTROL:
        printDebug.debug("Attempting to set Audio Stream")

        audio = stream['audio']

        if stream['audioCount'] == 1:
            printDebug.info("Only one audio stream present - will leave as default")

        elif audio:
            printDebug.debug("Attempting to use selected language setting: %s" % audio.get('language',audio.get('languageCode','Unknown')).encode('utf8'))
            printDebug.info("Found preferred language at index %s" % stream['audioOffset'])
            try:
                xbmc.Player().setAudioStream(stream['audioOffset'])
                printDebug.debug("Audio set")
            except:
                printDebug.info("Error setting audio, will use embedded default stream")

    #Set the SUBTITLE component
    if settings.get_setting('streamControl') == SubAudioControl.PLEX_CONTROL:
        printDebug.debug("Attempting to set preferred subtitle Stream")
        subtitle=stream['subtitle']
        if subtitle:
            printDebug.debug("Found preferred subtitle stream" )
            try:
                xbmc.Player().showSubtitles(False)
                if subtitle.get('key'):
                    xbmc.Player().setSubtitles(subtitle['key'])
                else:
                    printDebug.info("Enabling embedded subtitles at index %s" % stream['subOffset'])
                    xbmc.Player().setSubtitleStream(int(stream['subOffset']))

                xbmc.Player().showSubtitles(True)
                return True
            except:
                printDebug.info("Error setting subtitle")

        else:
            printDebug.info("No preferred subtitles to set")
            xbmc.Player().showSubtitles(False)

    return False

def selectMedia( data, server ):
    printDebug.debug("== ENTER ==")
    #if we have two or more files for the same movie, then present a screen
    result=0
    dvdplayback=False

    count=data['partsCount']
    options=data['parts']
    details=data['details']

    if count > 1:

        dialogOptions=[]
        dvdIndex=[]
        indexCount=0
        for items in options:

            if items[1]:
                name=items[1].split('/')[-1]
                #name="%s %s %sMbps" % (items[1].split('/')[-1], details[indexCount]['videoResolution'], details[indexCount]['bitrate'])
            else:
                name="%s %s %sMbps" % (items[0].split('.')[-1], details[indexCount]['videoResolution'], details[indexCount]['bitrate'])

            if settings.get_setting('forcedvd'):
                if '.ifo' in name.lower():
                    printDebug.debug( "Found IFO DVD file in " + name )
                    name="DVD Image"
                    dvdIndex.append(indexCount)

            dialogOptions.append(name)
            indexCount+=1

        printDebug.debug("Create selection dialog box - we have a decision to make!")
        startTime = xbmcgui.Dialog()
        result = startTime.select('Select media to play',dialogOptions)
        if result == -1:
            return None

        if result in dvdIndex:
            printDebug.debug( "DVD Media selected")
            dvdplayback=True

    else:
        if settings.get_setting('forcedvd'):
            if '.ifo' in options[result]:
                dvdplayback=True

    newurl = media_type({'key': options[result][0], 'file': options[result][1]}, server, dvdplayback)

    printDebug.debug("We have selected media at %s" % newurl)
    return newurl

def monitorPlayback( id, server, playurl, session=None ):
    printDebug.debug("== ENTER ==")

    if session:
        printDebug.debug("We are monitoring a transcode session")

    if settings.get_setting('monitoroff'):
        return

    playedTime = 0
    totalTime = 0
    currentTime = 0
    #Whilst the file is playing back
    while xbmc.Player().isPlaying():

        try:
            if not ( playurl == xbmc.Player().getPlayingFile() ):
                printDebug.info("File stopped being played")
                break
        except: pass

        currentTime = int(xbmc.Player().getTime())
        totalTime = int(xbmc.Player().getTotalTime())

        try:
            progress = int(( float(currentTime) / float(totalTime) ) * 100)
        except:
            progress = 0

        if playedTime == currentTime:
            printDebug.debug( "Movies paused at: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress) )
            server.report_playback_progress(id,currentTime*1000, state="paused", duration=totalTime*1000)
        else:

            printDebug.debug( "Movies played time: %s secs of %s @ %s%%" % ( currentTime, totalTime, progress) )
            server.report_playback_progress(id,currentTime*1000, state="playing", duration=totalTime*1000)
            playedTime = currentTime

        xbmc.sleep(2000)

    #If we get this far, playback has stopped
    printDebug.debug("Playback Stopped")
    server.report_playback_progress(id,playedTime*1000, state='stopped', duration=totalTime*1000)

    if session is not None:
        printDebug.debug("Stopping PMS transcode job with session %s" % session)
        server.stop_transcode_session(session)

    return

def PLAY( url ):
    printDebug.debug("== ENTER ==")

    if url.startswith('file'):
        printDebug.debug( "We are playing a local file")
        #Split out the path from the URL
        playurl=url.split(':',1)[1]
    elif url.startswith('http'):
        printDebug.debug( "We are playing a stream")
        if '?' in url:
            server=plex_network.get_server_from_url(url)
            playurl=server.get_formatted_url(url)
    else:
        playurl=url

    item = xbmcgui.ListItem(path=playurl)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

def videoPluginPlay(vids, prefix=None, indirect=None, transcode=False ):
    server=plex_network.get_server_from_url(vids)
    if "node.plexapp.com" in vids:
        server=get_master_server()

    if indirect:
        #Probably should transcode this
        if vids.startswith('http'):
            vids='/'+vids.split('/',3)[3]
            transcode=True

        session, vids=server.get_universal_transcode(vids)

    '''#If we find the url lookup service, then we probably have a standard plugin, but possibly with resolution choices
    if '/services/url/lookup' in vids:
        printDebug.debug("URL Lookup service")
        tree=getXML(vids)
        if not tree:
            return

        mediaCount=0
        mediaDetails=[]
        for media in tree.getiterator('Media'):
            mediaCount+=1
            tempDict={'videoResolution' : media.get('videoResolution',"Unknown")}

            for child in media:
                tempDict['key']=child.get('key','')

            tempDict['identifier']=tree.get('identifier','')
            mediaDetails.append(tempDict)

        printDebug.debug( str(mediaDetails) )

        #If we have options, create a dialog menu
        result=0
        if mediaCount > 1:
            printDebug ("Select from plugin video sources")
            dialogOptions=[x['videoResolution'] for x in mediaDetails ]
            videoResolution = xbmcgui.Dialog()

            result = videoResolution.select('Select resolution..',dialogOptions)

            if result == -1:
                return

        videoPluginPlay(getLinkURL('',mediaDetails[result],server))
        return

    #Check if there is a further level of XML required
    if indirect or '&indirect=1' in vids:
        printDebug.debug("Indirect link")
        tree=getXML(vids)
        if not tree:
            return

        for bits in tree.getiterator('Part'):
            videoPluginPlay(getLinkURL(vids,bits,server))
            break

        return
    '''
    #if we have a plex URL, then this is a transcoding URL
    if 'plex://' in vids:
        printDebug.debug("found webkit video, pass to transcoder")
        if not (prefix):
            prefix="system"
            if settings.get_setting('transcode_type') == "universal":
                session, vids=server.get_universal_transcode(vids)
            elif settings.get_setting('transcode_type') == "legacy":
                session, vids=server.get_legacy_transcode(0,vids,prefix)

        #Workaround for XBMC HLS request limit of 1024 byts
        if len(vids) > 1000:
            printDebug.debug("XBMC HSL limit detected, will pre-fetch m3u8 playlist")

            playlist = getXML(vids)

            if not playlist or not "#EXTM3U" in playlist:

                printDebug.debug("Unable to get valid m3u8 playlist from transcoder")
                return

            server=plex_network.get_server_from_url(vids)
            session=playlist.split()[-1]
            vids="%s/video/:/transcode/segmented/%s?t=1" % (server.get_url_location(), session)

    printDebug.debug("URL to Play: %s " % vids)
    printDebug.debug("Prefix is: %s" % prefix)

    #If this is an Apple movie trailer, add User Agent to allow access
    if 'trailers.apple.com' in vids:
        url=vids+"|User-Agent=QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
    else:
        url=vids

    printDebug.debug("Final URL is: %s" % url)

    item = xbmcgui.ListItem(path=url)
    start = xbmcplugin.setResolvedUrl(pluginhandle, True, item)

    if transcode:
        try:
            pluginTranscodeMonitor(session,server)
        except:
            printDebug.debug("Unable to start transcode monitor")
    else:
        printDebug.debug("Not starting monitor")

    return

def pluginTranscodeMonitor( sessionID, server ):
    printDebug.debug("== ENTER ==")

    #Logic may appear backward, but this does allow for a failed start to be detected
    #First while loop waiting for start

    if settings.get_setting('monitoroff'):
        return

    count=0
    while not xbmc.Player().isPlaying():
        printDebug.debug( "Not playing yet...sleep for 2")
        count = count + 2
        if count >= 40:
            #Waited 20 seconds and still no movie playing - assume it isn't going to..
            return
        else:
            xbmc.sleep(2000)

    while xbmc.Player().isPlaying():
        printDebug.debug("Waiting for playback to finish")
        xbmc.sleep(4000)

    printDebug.debug("Playback Stopped")
    printDebug.debug("Stopping PMS transcode job with session: %s" % sessionID)
    server.stop_transcode_session(sessionID)

    return

def get_params( paramstring ):
    printDebug.debug("== ENTER ==")
    printDebug.debug("Parameter string: %s" % paramstring)
    param={}
    if len(paramstring)>=2:
            params=paramstring

            if params[0] == "?":
                cleanedparams=params[1:]
            else:
                cleanedparams=params

            if (params[len(params)-1]=='/'):
                    params=params[0:len(params)-2]

            pairsofparams=cleanedparams.split('&')
            for i in range(len(pairsofparams)):
                    splitparams={}
                    splitparams=pairsofparams[i].split('=')
                    if (len(splitparams))==2:
                            param[splitparams[0]]=splitparams[1]
                    elif (len(splitparams))==3:
                            param[splitparams[0]]=splitparams[1]+"="+splitparams[2]
    print "PleXBMC -> Detected parameters: " + str(param)
    return param

def channelSearch (url, prompt):
    """
        When we encounter a search request, branch off to this function to generate the keyboard
        and accept the terms.  This URL is then fed back into the correct function for
        onward processing.
    """
    printDebug.debug("== ENTER ==")

    if prompt:
        prompt=urllib.unquote(prompt)
    else:
        prompt="Enter Search Term..."

    kb = xbmc.Keyboard('', 'heading')
    kb.setHeading(prompt)
    kb.doModal()
    if (kb.isConfirmed()):
        text = kb.getText()
        printDebug.debug("Search term input: %s" % text)
        url=url+'&query='+urllib.quote(text)
        PlexPlugins( url )
    return

def getContent( url ):
    """
        This function takes teh URL, gets the XML and determines what the content is
        This XML is then redirected to the best processing function.
        If a search term is detected, then show keyboard and run search query
        @input: URL of XML page
        @return: nothing, redirects to another function
    """
    printDebug.debug("== ENTER ==")

    server=plex_network.get_server_from_url(url)
    lastbit=url.split('/')[-1]
    printDebug.debug("URL suffix: %s" % lastbit)

    #Catch search requests, as we need to process input before getting results.
    if lastbit.startswith('search'):
        printDebug.debug("This is a search URL.  Bringing up keyboard")
        kb = xbmc.Keyboard('', 'heading')
        kb.setHeading('Enter search term')
        kb.doModal()
        if (kb.isConfirmed()):
            text = kb.getText()
            printDebug.debug("Search term input: %s" % text)
            url=url+'&query='+urllib.quote(text)
        else:
            return

    tree = server.processed_xml(url)

    setWindowHeading(tree)

    if lastbit == "folder" or lastbit == "playlists":
        processXML(url,tree)
        return

    view_group=tree.get('viewGroup')

    if view_group == "movie":
        printDebug.debug( "This is movie XML, passing to Movies")
        Movies(url, tree)
    elif view_group == "show":
        printDebug.debug( "This is tv show XML")
        TVShows(url,tree)
    elif view_group == "episode":
        printDebug.debug("This is TV episode XML")
        TVEpisodes(url,tree)
    elif view_group == 'artist':
        printDebug.debug( "This is music XML")
        artist(url, tree)
    elif view_group== 'album' or view_group == 'albums':
        albums(url,tree)
    elif view_group == 'track':
        printDebug.debug("This is track XML")
        tracks(url, tree) #sorthing is handled here
    elif view_group =="photo":
        printDebug.debug("This is a photo XML")
        photo(url,tree)
    else:
        processDirectory(url,tree)

    return

def processDirectory( url, tree=None ):
    printDebug.debug("== ENTER ==")
    printDebug.debug("Processing secondary menus")
    xbmcplugin.setContent(pluginhandle, "")

    server = plex_network.get_server_from_url(url)
    setWindowHeading(tree)
    for directory in tree:
        details={'title' : directory.get('title','Unknown').encode('utf-8') }
        extraData={'thumb'        : get_thumb(tree, server) ,
                   'fanart_image' : getFanart(tree, server) }

        extraData['mode'] = Mode.GETCONTENT
        u='%s' % (get_link_url(url, directory, server))

        addGUIItem(u, details, extraData)

    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=settings.get_setting('kodicache'))

def artist( url, tree=None ):
    """
        Process artist XML and display data
        @input: url of XML page, or existing tree of XML page
        @return: nothing
    """
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'artists')
    xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    xbmcplugin.addSortMethod(pluginhandle, 12 ) #artist title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 34 ) #last played
    xbmcplugin.addSortMethod(pluginhandle, 17 ) #year

    #Get the URL and server name.  Get the XML and parse
    tree=getXML(url,tree)
    if tree is None:
        return

    server=plex_network.get_server_from_url(url)
    setWindowHeading(tree)
    ArtistTag=tree.findall('Directory')
    for artist in ArtistTag:

        details={'artist'  : artist.get('title','').encode('utf-8') }

        details['title']=details['artist']

        extraData={'type'         : "Music" ,
                   'thumb'        : get_thumb(artist, server) ,
                   'fanart_image' : getFanart(artist, server) ,
                   'ratingKey'    : artist.get('title','') ,
                   'key'          : artist.get('key','') ,
                   'mode'         : Mode.ALBUMS ,
                   'plot'         : artist.get('summary','') }

        url='%s%s' % (server.get_url_location(), extraData['key'] )

        addGUIItem(url,details,extraData)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('music')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def albums( url, tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'albums')
    xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    xbmcplugin.addSortMethod(pluginhandle, 24 ) #album title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 12 )  #artist ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 34 ) #last played
    xbmcplugin.addSortMethod(pluginhandle, 17 ) #year

    #Get the URL and server name.  Get the XML and parse
    tree=getXML(url,tree)
    if tree is None:
        return

    server=plex_network.get_server_from_url(url)
    sectionart=getFanart(tree, server)
    setWindowHeading(tree)
    AlbumTags=tree.findall('Directory')
    recent = True if 'recentlyAdded' in url else False
    for album in AlbumTags:

        details={'album'   : album.get('title','').encode('utf-8') ,
                 'year'    : int(album.get('year',0)) ,
                 'artist'  : tree.get('parentTitle', album.get('parentTitle','')).encode('utf-8') }

        if recent:
            details['title']="%s - %s" % ( details['artist'], details['album'])
        else:
            details['title']=details['album']

        extraData={'type'         : "Music" ,
                   'thumb'        : get_thumb(album, server) ,
                   'fanart_image' : getFanart(album, server) ,
                   'key'          : album.get('key',''),
                   'mode'         : Mode.TRACKS ,
                   'plot'         : album.get('summary','')}

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=sectionart

        url='%s%s' % (server.get_url_location(), extraData['key'] )

        addGUIItem(url,details,extraData)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('music')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def tracks( url,tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'songs')
    xbmcplugin.addSortMethod(pluginhandle, 37 ) #maintain original plex sorted
    xbmcplugin.addSortMethod(pluginhandle, 10 ) #title title ignore THE
    xbmcplugin.addSortMethod(pluginhandle, 8 ) #duration
    xbmcplugin.addSortMethod(pluginhandle, 27 ) #song rating
    xbmcplugin.addSortMethod(pluginhandle, 7 ) #track number

    tree=getXML(url,tree)
    if tree is None:
        return

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()

    server=plex_network.get_server_from_url(url)
    sectionart=getFanart(tree, server)
    sectionthumb=get_thumb(tree, server)
    setWindowHeading(tree)
    TrackTags=tree.findall('Track')
    for track in TrackTags:
        if track.get('thumb'):
            sectionthumb=get_thumb(track, server)

        trackTag(server, tree, track, sectionart, sectionthumb)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('music')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def getXML (url, tree=None):
    printDebug.debug("== ENTER ==")

    if tree is None:
        tree=plex_network.get_processed_xml(url)

    if tree.get('message'):
        xbmcgui.Dialog().ok(tree.get('header','Message'),tree.get('message',''))
        return None

    return tree

def PlexPlugins(url, tree=None):
    """
        Main function to parse plugin XML from PMS
        Will create dir or item links depending on what the
        main tag is.
        @input: plugin page URL
        @return: nothing, creates XBMC GUI listing
    """
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'addons')
    server=plex_network.get_server_from_url(url)
    tree = getXML(url,tree)
    if tree is None:
        return

    myplex_url=False
    if (tree.get('identifier') != "com.plexapp.plugins.myplex") and ( "node.plexapp.com" in url ) :
        myplex_url=True
        printDebug.debug("This is a myplex URL, attempting to locate master server")
        server=get_master_server()

    for plugin in tree:

        details={'title'   : plugin.get('title','Unknown').encode('utf-8') }

        if details['title'] == "Unknown":
            details['title']=plugin.get('name',"Unknown").encode('utf-8')

        if plugin.get('summary'):
            details['plot']=plugin.get('summary')

        extraData={'thumb'        : get_thumb(plugin, server) ,
                   'fanart_image' : getFanart(plugin, server) ,
                   'identifier'   : tree.get('identifier','') ,
                   'type'         : "Video" ,
                   'key'          : plugin.get('key','') }

        if myplex_url:
            extraData['key']=extraData['key'].replace('node.plexapp.com:32400',server.get_location())

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=getFanart(tree, server)

        p_url=get_link_url(url, extraData, server)

        if plugin.tag == "Directory" or plugin.tag == "Podcast":

            if plugin.get('search') == '1':
                extraData['mode']=Mode.CHANNELSEARCH
                extraData['parameters']={'prompt' : plugin.get('prompt',"Enter Search Term").encode('utf-8') }
            else:
                extraData['mode']=Mode.PLEXPLUGINS

            addGUIItem(p_url, details, extraData)

        elif plugin.tag == "Video":
            extraData['mode']=Mode.VIDEOPLUGINPLAY

            for child in plugin:
                if child.tag == "Media":
                    extraData['parameters'] = {'indirect' : child.get('indirect','0')}

            addGUIItem(p_url, details, extraData, folder=False)

        elif plugin.tag == "Setting":

            if plugin.get('option') == 'hidden':
                value="********"
            elif plugin.get('type') == "text":
                value=plugin.get('value')
            elif plugin.get('type') == "enum":
                value=plugin.get('values').split('|')[int(plugin.get('value',0))]
            else:
                value=plugin.get('value')

            details['title']= "%s - [%s]" % (plugin.get('label','Unknown').encode('utf-8'), value)
            extraData['mode']=Mode.CHANNELPREFS
            extraData['parameters']={'id' : plugin.get('id') }
            addGUIItem(url, details, extraData)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def channelSettings ( url, settingID ):
    """
        Take the setting XML and parse it to create an updated
        string with the new settings.  For the selected value, create
        a user input screen (text or list) to update the setting.
        @ input: url
        @ return: nothing
    """
    printDebug.debug("== ENTER ==")
    printDebug.debug("Setting preference for ID: %s" % settingID )

    if not settingID:
        printDebug.debug("ID not set")
        return

    tree=getXML(url)
    if tree is None:
        return

    setWindowHeading(tree)
    setString=None
    for plugin in tree:

        if plugin.get('id') == settingID:
            printDebug.debug("Found correct id entry for: %s" % settingID)
            id=settingID

            label=plugin.get('label',"Enter value")
            option=plugin.get('option')
            value=plugin.get('value')

            if plugin.get('type') == "text":
                printDebug.debug("Setting up a text entry screen")
                kb = xbmc.Keyboard(value, 'heading')
                kb.setHeading(label)

                if option == "hidden":
                    kb.setHiddenInput(True)
                else:
                    kb.setHiddenInput(False)

                kb.doModal()
                if (kb.isConfirmed()):
                    value = kb.getText()
                    printDebug.debug("Value input: %s " % value)
                else:
                    printDebug.debug("User cancelled dialog")
                    return False

            elif plugin.get('type') == "enum":
                printDebug.debug("Setting up an enum entry screen")

                values=plugin.get('values').split('|')

                settingScreen = xbmcgui.Dialog()
                value = settingScreen.select(label,values)
                if value == -1:
                    printDebug.debug("User cancelled dialog")
                    return False
            else:
                printDebug.debug('Unknown option type: %s' % plugin.get('id') )

        else:
            value=plugin.get('value')
            id=plugin.get('id')

        if setString is None:
            setString='%s/set?%s=%s' % (url, id, value)
        else:
            setString='%s&%s=%s' % (setString, id, value)

    printDebug.debug("Settings URL: %s" % setString )
    plex_network.talk_to_server(setString)
    xbmc.executebuiltin("Container.Refresh")

    return False

def processXML( url, tree=None ):
    """
        Main function to parse plugin XML from PMS
        Will create dir or item links depending on what the
        main tag is.
        @input: plugin page URL
        @return: nothing, creates XBMC GUI listing
    """
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'movies')
    server=plex_network.get_server_from_url(url)
    tree=getXML(url,tree)
    if tree is None:
        return
    setWindowHeading(tree)
    for plugin in tree:

        details={'title'   : plugin.get('title','Unknown').encode('utf-8') }

        if details['title'] == "Unknown":
            details['title']=plugin.get('name',"Unknown").encode('utf-8')

        extraData={'thumb'        : get_thumb(plugin, server) ,
                   'fanart_image' : getFanart(plugin, server) ,
                   'identifier'   : tree.get('identifier','') ,
                   'type'         : "Video" }

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=getFanart(tree, server)

        p_url=get_link_url(url, plugin, server)

        if plugin.tag == "Directory" or plugin.tag == "Podcast":
            extraData['mode']=Mode.PROCESSXML
            addGUIItem(p_url, details, extraData)

        elif plugin.tag == "Track":
            trackTag(server, tree, plugin)

        elif plugin.tag == "Playlist":
            playlistTag(url, server, tree, plugin)

        elif tree.get('viewGroup') == "movie":
            Movies(url, tree)
            return

        elif tree.get('viewGroup') == "episode":
            TVEpisodes(url, tree)
            return

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def movieTag(url, server, tree, movie, randomNumber):

    printDebug.debug("---New Item---")
    tempgenre=[]
    tempcast=[]
    tempdir=[]
    tempwriter=[]

    #Lets grab all the info we can quickly through either a dictionary, or assignment to a list
    #We'll process it later
    for child in movie:
        if child.tag == "Media":
            mediaarguments = dict(child.items())
        elif child.tag == "Genre" and not settings.get_setting('skipmetadata'):
            tempgenre.append(child.get('tag'))
        elif child.tag == "Writer"  and not settings.get_setting('skipmetadata'):
            tempwriter.append(child.get('tag'))
        elif child.tag == "Director"  and not settings.get_setting('skipmetadata'):
            tempdir.append(child.get('tag'))
        elif child.tag == "Role"  and not settings.get_setting('skipmetadata'):
            tempcast.append(child.get('tag'))

    printDebug.debug("Media attributes are %s" % mediaarguments)

    #Gather some data
    view_offset=movie.get('viewOffset',0)
    duration=int(mediaarguments.get('duration',movie.get('duration',0)))/1000
    #if movie.get('originallyAvailableAt') is not None:
    #    release_date = time.strftime('%d.%m.%Y',(time.strptime(movie.get('originallyAvailableAt'), '%Y-%m-%d')))
    #else:
    #    release_date = ""

    #Required listItem entries for XBMC
    details={'plot'      : movie.get('summary','').encode('utf-8') ,
             'title'     : movie.get('title','Unknown').encode('utf-8') ,
             'sorttitle' : movie.get('titleSort', movie.get('title','Unknown')).encode('utf-8') ,
             'rating'    : float(movie.get('rating',0)) ,
             'studio'    : movie.get('studio','').encode('utf-8'),
             'mpaa'      : movie.get('contentRating', '').encode('utf-8'),
             'year'      : int(movie.get('year',0)),
             'date'      : movie.get('originallyAvailableAt','1970-01-01'),
             'tagline'   : movie.get('tagline',''),
             'DateAdded' : str(datetime.datetime.fromtimestamp(int(movie.get('addedAt',0))))}

    #Extra data required to manage other properties
    extraData={'type'         : "Video" ,
               'source'       : 'movies',
               'thumb'        : get_thumb(movie, server) ,
               'fanart_image' : getFanart(movie, server) ,
               'key'          : movie.get('key',''),
               'ratingKey'    : str(movie.get('ratingKey',0)),
               'duration'     : duration,
               'resume'       : int (int(view_offset)/1000) }

    #Determine what type of watched flag [overlay] to use
    if int(movie.get('viewCount',0)) > 0:
        details['playcount'] = 1
    elif int(movie.get('viewCount',0)) == 0:
        details['playcount'] = 0

    #Extended Metadata
    if not settings.get_setting('skipmetadata'):
        details['cast']     = tempcast
        details['director'] = " / ".join(tempdir)
        details['writer']   = " / ".join(tempwriter)
        details['genre']    = " / ".join(tempgenre)

    if movie.get('primaryExtraKey') is not None:
        details['trailer'] = "plugin://plugin.video.plexbmc/?url=%s%s?t=%s&mode=%s" % (server.get_url_location(), movie.get('primaryExtraKey', ''), randomNumber, Mode.PLAYLIBRARY)
        printDebug.debug('Trailer plugin url added: %s' % details['trailer'])

    #Add extra media flag data
    if not settings.get_setting('skipflags'):
        extraData.update(getMediaData(mediaarguments))

    #Build any specific context menu entries
    if not settings.get_setting('skipcontextmenus'):
        context=buildContextMenu(url, extraData, server)
    else:
        context=None
    # http:// <server> <path> &mode=<mode> &t=<rnd>
    extraData['mode']=Mode.PLAYLIBRARY
    separator = "?"
    if "?" in extraData['key']:
        separator = "&"
    u="%s%s%st=%s" % (server.get_url_location(), extraData['key'], separator, randomNumber)

    addGUIItem(u,details,extraData,context,folder=False)
    return

def getMediaData ( tag_dict ):
    """
        Extra the media details from the XML
        @input: dict of <media /> tag attributes
        @output: dict of required values
    """
    printDebug.debug("== ENTER ==")

    return     {'VideoResolution'    : tag_dict.get('videoResolution','') ,
                'VideoCodec'         : tag_dict.get('videoCodec','') ,
                'AudioCodec'         : tag_dict.get('audioCodec','') ,
                'AudioChannels'      : tag_dict.get('audioChannels','') ,
                'VideoAspect'        : tag_dict.get('aspectRatio','') ,
                'xbmc_height'        : tag_dict.get('height') ,
                'xbmc_width'         : tag_dict.get('width') ,
                'xbmc_VideoCodec'    : tag_dict.get('videoCodec') ,
                'xbmc_AudioCodec'    : tag_dict.get('audioCodec') ,
                'xbmc_AudioChannels' : tag_dict.get('audioChannels') ,
                'xbmc_VideoAspect'   : tag_dict.get('aspectRatio') }

def trackTag( server, tree, track, sectionart="", sectionthumb="", listing=True ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'songs')

    for child in track:
        for babies in child:
            if babies.tag == "Part":
                partDetails=(dict(babies.items()))

    printDebug.debug( "Part is %s" % partDetails)

    details={'TrackNumber' : int(track.get('index',0)) ,
             'title'       : str(track.get('index',0)).zfill(2)+". "+track.get('title','Unknown').encode('utf-8') ,
             'rating'      : float(track.get('rating',0)) ,
             'album'       : track.get('parentTitle', tree.get('parentTitle','')).encode('utf-8') ,
             'artist'      : track.get('grandparentTitle', tree.get('grandparentTitle','')).encode('utf-8') ,
             'duration'    : int(track.get('duration',0))/1000 }

    extraData={'type'          : "music" ,
               'fanart_image'  : sectionart ,
               'thumb'         : sectionthumb ,
               'key'           : track.get('key','') }

    #If we are streaming, then get the virtual location
    extraData['mode']=Mode.PLAYLIBRARY
    u="%s%s" % (server.get_url_location(), extraData['key'])

    if listing:
        addGUIItem(u,details,extraData,folder=False)
    else:
        return ( u, details )

def playlistTag(url, server, tree, track, sectionart="", sectionthumb="", listing=True ):
    printDebug.debug("== ENTER ==")

    details={'title'       : track.get('title','Unknown').encode('utf-8') ,
             'duration'    : int(track.get('duration',0))/1000
             }

    extraData={'type'         : track.get('playlistType', ''),
               'thumb'      : get_thumb({'thumb' : track.get('composite', '')},server)}

    if extraData['type'] == "video":
        extraData['mode'] = Mode.MOVIES
    elif extraData['type'] == "audio":
        extraData['mode'] = Mode.TRACKS
    else:
        extraData['mode']=Mode.GETCONTENT

    u=get_link_url(url, track, server)

    if listing:
        addGUIItem(u,details,extraData,folder=True)
    else:
        return ( url, details )

def photo( url,tree=None ):
    printDebug.debug("== ENTER ==")
    server=plex_network.get_server_from_url(url)

    xbmcplugin.setContent(pluginhandle, 'photo')

    tree=getXML(url,tree)
    if tree is None:
        return

    sectionArt=getFanart(tree,server)
    setWindowHeading(tree)
    for picture in tree:

        details={'title' : picture.get('title',picture.get('name','Unknown')).encode('utf-8') }

        if not details['title']:
            details['title'] = "Unknown"

        extraData={'thumb'        : get_thumb(picture, server) ,
                   'fanart_image' : getFanart(picture, server) ,
                   'type'         : "image" }

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=sectionArt

        u=get_link_url(url, picture, server)

        if picture.tag == "Directory":
            extraData['mode']=Mode.PHOTOS
            addGUIItem(u,details,extraData)

        elif picture.tag == "Photo":

            if tree.get('viewGroup','') == "photo":
                for photo in picture:
                    if photo.tag == "Media":
                        for images in photo:
                            if images.tag == "Part":
                                extraData['key']=server.get_url_location()+images.get('key','')
                                details['size']=int(images.get('size',0))
                                u=extraData['key']

            addGUIItem(u,details,extraData,folder=False)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def music( url, tree=None ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'artists')

    server=plex_network.get_server_from_url(url)

    tree=getXML(url,tree)
    if tree is None:
        return

    setWindowHeading(tree)
    for grapes in tree:

        if grapes.get('key') is None:
            continue

        details={'genre'       : grapes.get('genre','').encode('utf-8') ,
                 'artist'      : grapes.get('artist','').encode('utf-8') ,
                 'year'        : int(grapes.get('year',0)) ,
                 'album'       : grapes.get('album','').encode('utf-8') ,
                 'tracknumber' : int(grapes.get('index',0)) ,
                 'title'       : "Unknown" }

        extraData={'type'        : "Music" ,
                   'thumb'       : get_thumb(grapes, server) ,
                   'fanart_image': getFanart(grapes, server) }

        if extraData['fanart_image'] == "":
            extraData['fanart_image']=getFanart(tree, server)

        u=get_link_url(url, grapes, server)

        if grapes.tag == "Track":
            printDebug.debug("Track Tag")
            xbmcplugin.setContent(pluginhandle, 'songs')

            details['title']=grapes.get('track',grapes.get('title','Unknown')).encode('utf-8')
            details['duration']=int(int(grapes.get('totalTime',0))/1000)

            extraData['mode']=Mode.BASICPLAY
            addGUIItem(u,details,extraData,folder=False)

        else:

            if grapes.tag == "Artist":
                printDebug.debug("Artist Tag")
                xbmcplugin.setContent(pluginhandle, 'artists')
                details['title']=grapes.get('artist','Unknown').encode('utf-8')

            elif grapes.tag == "Album":
                printDebug.debug("Album Tag")
                xbmcplugin.setContent(pluginhandle, 'albums')
                details['title']=grapes.get('album','Unknown').encode('utf-8')

            elif grapes.tag == "Genre":
                details['title']=grapes.get('genre','Unknown').encode('utf-8')

            else:
                printDebug.debug("Generic Tag: %s" % grapes.tag)
                details['title']=grapes.get('title','Unknown').encode('utf-8')

            extraData['mode']=Mode.MUSIC
            addGUIItem(u,details,extraData)

    printDebug.debug("Skin override is: %s" % settings.get_setting('skinoverride'))
    view_id = enforceSkinView('music')
    if view_id:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def getFanart(data, server, width=1280, height=720):
    """
        Simply take a URL or path and determine how to format for fanart
        @ input: elementTree element, server name
        @ return formatted URL for photo resizing
    """
    if settings.get_setting('skipimages'):
        return ''

    fanart=data.get('art','').encode('utf-8')

    if fanart.startswith('http') :
        return fanart

    elif fanart.startswith('/'):
        if settings.get_setting('fullres_fanart'):
            return server.get_kodi_header_formatted_url(fanart)
        else:
            return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' % (urllib.quote_plus('http://localhost:32400' + fanart), width, height))

    return ''

def plexOnline( url ):
    printDebug.debug("== ENTER ==")
    xbmcplugin.setContent(pluginhandle, 'addons')

    server=plex_network.get_server_from_url(url)

    tree=server.processed_xml(url)
    if tree is None:
        return

    for plugin in tree:

        details={'title' : plugin.get('title',plugin.get('name','Unknown')).encode('utf-8') }
        extraData={'type'      : "Video" ,
                   'installed' : int(plugin.get('installed',2)) ,
                   'key'       : plugin.get('key','') ,
                   'thumb'     : get_thumb(plugin,server)}

        extraData['mode']=Mode.CHANNELINSTALL

        if extraData['installed'] == 1:
            details['title']=details['title']+" (installed)"

        elif extraData['installed'] == 2:
            extraData['mode']=Mode.PLEXONLINE

        u=get_link_url(url, plugin, server)

        extraData['parameters']={'name' : details['title'] }

        addGUIItem(u, details, extraData)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def install( url, name ):
    printDebug.debug("== ENTER ==")
    server=plex_network.get_server_from_url(url)
    tree=server.processed_xml(url)
    if tree is None:
        return

    operations={}
    i=0
    for plums in tree.findall('Directory'):
        operations[i]=plums.get('title')

        #If we find an install option, switch to a yes/no dialog box
        if operations[i].lower() == "install":
            printDebug.debug("Not installed.  Print dialog")
            ret = xbmcgui.Dialog().yesno("Plex Online","About to install " + name)

            if ret:
                printDebug.debug("Installing....")
                tree = server.processed_xml(url+"/install")

                msg=tree.get('message','(blank)')
                printDebug.debug(msg)
                xbmcgui.Dialog().ok("Plex Online",msg)
            return

        i+=1

    #Else continue to a selection dialog box
    ret = xbmcgui.Dialog().select("This plugin is already installed..",operations.values())

    if ret == -1:
        printDebug.debug("No option selected, cancelling")
        return

    printDebug.debug("Option %s selected.  Operation is %s" % (ret, operations[ret]))
    u=url+"/"+operations[ret].lower()
    tree = server.processed_xml(u)

    msg=tree.get('message')
    printDebug.debug(msg)
    xbmcgui.Dialog().ok("Plex Online",msg)
    xbmc.executebuiltin("Container.Refresh")

    return

def channelView( url ):
    printDebug.debug("== ENTER ==")
    server=plex_network.get_server_from_url(url)
    tree=server.processed_xml(url)

    if tree is None:
        return

    setWindowHeading(tree)
    for channels in tree.getiterator('Directory'):

        if channels.get('local','') == "0":
            continue

        arguments=dict(channels.items())

        extraData={'fanart_image' : getFanart(channels, server) ,
                   'thumb'        : get_thumb(channels, server) }

        details={'title' : channels.get('title','Unknown') }

        suffix=channels.get('key').split('/')[1]

        if channels.get('unique','')=='0':
            details['title']="%s (%s)" % ( details['title'], suffix )

        #Alter data sent into getlinkurl, as channels use path rather than key
        p_url=get_link_url(url, {'key': channels.get('key'), 'identifier' : channels.get('key')} , server)

        if suffix == "photos":
            extraData['mode']=Mode.PHOTOS
        elif suffix == "video":
            extraData['mode']=Mode.PLEXPLUGINS
        elif suffix == "music":
            extraData['mode']=Mode.MUSIC
        else:
            extraData['mode']=Mode.GETCONTENT

        addGUIItem(p_url,details,extraData)

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

def myPlexQueue():
    printDebug.debug("== ENTER ==")

    if not plex_network.is_myplex_signedin():
        xbmc.executebuiltin("XBMC.Notification(myplex not configured,)")
        return

    tree=plex_network.get_myplex_queue()

    PlexPlugins('http://my.plexapp.com/playlists/queue/all', tree)
    return

def setWindowHeading(tree) :
    WINDOW = xbmcgui.Window( xbmcgui.getCurrentWindowId() )
    try:
        WINDOW.setProperty("heading", tree.get('title1'))
    except:
        WINDOW.clearProperty("heading")
    try:
        WINDOW.setProperty("heading2", tree.get('title2'))
    except:
        WINDOW.clearProperty("heading2")

def displayServers( url ):
    printDebug.debug("== ENTER ==")
    type=url.split('/')[2]
    printDebug.debug("Displaying entries for %s" % type)
    Servers = plex_network.get_server_list()
    Servers_list=len(Servers)

    #For each of the servers we have identified
    for mediaserver in Servers:

        if mediaserver.is_secondary():
            continue

        details={'title' : mediaserver.get_name() }

        extraData={}

        if type == "video":
            extraData['mode']=Mode.PLEXPLUGINS
            s_url='%s%s' % ( mediaserver.get_url_location(), '/video' )
            if Servers_list == 1:
                PlexPlugins(s_url)
                return

        elif type == "online":
            extraData['mode']=Mode.PLEXONLINE
            s_url='%s%s' % ( mediaserver.get_url_location() , '/system/plexonline')
            if Servers_list == 1:
                plexOnline(s_url)
                return

        elif type == "music":
            extraData['mode']=Mode.MUSIC
            s_url='%s%s' % ( mediaserver.get_url_location(), '/music' )
            if Servers_list == 1:
                music(s_url)
                return

        elif type == "photo":
            extraData['mode']=Mode.PHOTOS
            s_url='%s%s' % ( mediaserver.get_url_location(), '/photos' )
            if Servers_list == 1:
                photo(s_url)
                return

        addGUIItem(s_url, details, extraData )

    xbmcplugin.endOfDirectory(pluginhandle,cacheToDisc=settings.get_setting('kodicache'))

# So this is where we really start the addon
printDebug = PrintDebug("PleXBMC")

print "PleXBMC -> Running PleXBMC: %s " % GLOBAL_SETUP['__version__']

wake_servers()

if settings.get_debug() >= printDebug.DEBUG_INFO:
    print "PleXBMC -> Script argument is %s" % sys.argv
    print "PleXBMC -> Running Python: %s" % str(sys.version_info)
    print "PleXBMC -> CWD is set to: %s" % GLOBAL_SETUP['__cwd__']
    print "PleXBMC -> Platform: %s" % GLOBAL_SETUP['platform']
    print "PleXBMC -> Setting debug: %s" % printDebug.get_name(settings.get_debug())
    print "PleXBMC -> FullRes Thumbs are set to: %s" % settings.get_setting('fullres_thumbs')
    print "PleXBMC -> Settings streaming: %s" % settings.get_stream()
    print "PleXBMC -> Setting filter menus: %s" % settings.get_setting('secondary')
    print "PleXBMC -> Flatten is: %s" % settings.get_setting('flatten')
    if settings.get_setting('streamControl') == SubAudioControl.XBMC_CONTROL:
        print "PleXBMC -> Setting stream Control to : XBMC CONTROL"
    elif settings.get_setting('streamControl') == SubAudioControl.PLEX_CONTROL:
        print "PleXBMC -> Setting stream Control to : PLEX CONTROL"
    elif settings.get_setting('streamControl') == SubAudioControl.NEVER_SHOW:
        print "PleXBMC -> Setting stream Control to : NEVER SHOW"

    print "PleXBMC -> Force DVD playback: %s" % settings.get_setting('forcedvd')
    print "PleXBMC -> SMB IP Override: %s" % settings.get_setting('nasoverride')
    if settings.get_setting('nasoverride') and not settings.get_setting('nasoverrideip'):
        print "PleXBMC -> No NAS IP Specified.  Ignoring setting"
    else:
        print "PleXBMC -> NAS IP: " + settings.get_setting('nasoverrideip')
else:
    print "PleXBMC -> Debug is turned off.  Running silent"

pluginhandle = 0


def start_plexbmc():
    try:
        params = get_params(sys.argv[2])
    except:
        params = {}

    # Now try and assign some data to them
    param_url = params.get('url')
    command_name = None

    if param_url:
        if param_url.startswith('http') or param_url.startswith('file'):
            param_url = urllib.unquote(param_url)
        elif param_url.startswith('cmd'):
            command_name = urllib.unquote(param_url).split(':')[1]

    param_name = urllib.unquote_plus(params.get('name', ""))
    mode = int(params.get('mode', -1))
    play_transcode = True if int(params.get('transcode', 0)) == 1 else False
    param_identifier = params.get('identifier')
    param_indirect = params.get('indirect')
    force = params.get('force')

    if command_name is None:
        try:
            command_name = sys.argv[1]
        except:
            pass

    args = sys.argv[2:]
    command = COMMANDS.get(command_name)
    if command and issubclass(command, BaseCommand):
        printDebug.debug("executing command: %s; with args: %s" % (command, args))
        command(*args).execute()

    # nt currently used
    # elif command_name == "refreshplexbmc":
    #     plex_network.load()
    #     plex_network.discover()
    #     server_list = plex_network.get_server_list()
    #     # todo rewrite
    #     from commands.command_skin import CommandSkin
    #     command = CommandSkin(None, server_list)
    #     command.execute()
    #     # skin(server_list)
    #
    #     from commands.command_shelf import CommandShelf
    #     command = CommandShelf(server_list)
    #     command.execute()
    #     #shelf(server_list)
    #
    #     from commands.command_channel_shelf import CommandChannelShelf
    #     command = CommandChannelShelf(server_list)
    #     command.execute()
    #     # shelfChannel(server_list)

    # else move to the main code
    else:
        plex_network.load()
        global pluginhandle
        try:
            pluginhandle = int(command_name)
        except:
            pass

        WINDOW = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        WINDOW.clearProperty("heading")
        WINDOW.clearProperty("heading2")

        if settings.get_debug() >= printDebug.DEBUG_INFO:
            print "PleXBMC -> Mode: %s " % mode
            print "PleXBMC -> URL: %s" % param_url
            print "PleXBMC -> Name: %s" % param_name
            print "PleXBMC -> identifier: %s" % param_identifier

        # Run a function based on the mode variable that was passed in the URL
        if (mode is None) or (param_url is None) or (len(param_url) < 1):
            displaySections()

        elif mode == Mode.GETCONTENT:
            getContent(param_url)

        elif mode == Mode.TVSHOWS:
            TVShows(param_url)

        elif mode == Mode.MOVIES:
            Movies(param_url)

        elif mode == Mode.ARTISTS:
            artist(param_url)

        elif mode == Mode.TVSEASONS:
            TVSeasons(param_url)

        elif mode == Mode.PLAYLIBRARY:
            playLibraryMedia(param_url, force=force, override=play_transcode)

        elif mode == Mode.PLAYSHELF:
            playLibraryMedia(param_url, full_data=True, shelf=True)

        elif mode == Mode.TVEPISODES:
            TVEpisodes(param_url)

        elif mode == Mode.PLEXPLUGINS:
            PlexPlugins(param_url)

        elif mode == Mode.PROCESSXML:
            processXML(param_url)

        elif mode == Mode.BASICPLAY:
            PLAY(param_url)

        elif mode == Mode.ALBUMS:
            albums(param_url)

        elif mode == Mode.TRACKS:
            tracks(param_url)

        elif mode == Mode.PHOTOS:
            photo(param_url)

        elif mode == Mode.MUSIC:
            music(param_url)

        elif mode == Mode.VIDEOPLUGINPLAY:
            videoPluginPlay(param_url, param_identifier, param_indirect)

        elif mode == Mode.PLEXONLINE:
            plexOnline(param_url)

        elif mode == Mode.CHANNELINSTALL:
            install(param_url, param_name)

        elif mode == Mode.CHANNELVIEW:
            channelView(param_url)

        elif mode == Mode.PLAYLIBRARY_TRANSCODE:
            playLibraryMedia(param_url, override=True)

        elif mode == Mode.MYPLEXQUEUE:
            myPlexQueue()

        elif mode == Mode.CHANNELSEARCH:
            channelSearch(param_url, params.get('prompt'))

        elif mode == Mode.CHANNELPREFS:
            channelSettings(param_url, params.get('id'))

        elif mode == Mode.SHARED_MOVIES:
            displaySections(filter="movies", display_shared=True)

        elif mode == Mode.SHARED_SHOWS:
            displaySections(filter="tvshows", display_shared=True)

        elif mode == Mode.SHARED_PHOTOS:
            displaySections(filter="photos", display_shared=True)

        elif mode == Mode.SHARED_MUSIC:
            displaySections(filter="music", display_shared=True)

        elif mode == Mode.SHARED_ALL:
            displaySections(display_shared=True)

        elif mode == Mode.DELETE_REFRESH:
            plex_network.delete_cache()
            xbmc.executebuiltin("Container.Refresh")

        elif mode == Mode.PLAYLISTS:
            processXML(param_url)

        elif mode == Mode.DISPLAYSERVERS:
            displayServers(param_url)