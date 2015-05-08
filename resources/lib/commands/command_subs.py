from .base_command import BaseCommand
from ..plexserver import plex_network
from ..common import PrintDebug, AddonSettings
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandSubs")


class CommandSubs(BaseCommand):
    def __init__(self, *args):
        super(CommandSubs, self).__init__(args)

    def execute(self):
        plex_network.load()
        # server_uuid = sys.argv[2]
        # metadata_id = sys.argv[3]
        _alter_subs(self.args[0], self.args[1])


def _alter_subs(server_uuid, metadata_id):
    """
        Display a list of available Subtitle streams and allow a user to select one.
        The currently selected stream will be annotated with a *
    """
    printDebug.debug("== ENTER ==")

    server = plex_network.get_server_from_uuid(server_uuid)
    tree = server.get_metadata(metadata_id)

    sub_list = ['']
    display_list = ["None"]
    fl_select = False
    for parts in tree.getiterator('Part'):

        part_id = parts.get('id')

        for streams in parts:

            if streams.get('streamType', '') == "3":

                stream_id = streams.get('id')
                lang = streams.get('languageCode', "Unknown").encode('utf-8')
                printDebug.debug("Detected Subtitle stream [%s] [%s]" % ( stream_id, lang ))

                if streams.get('format', streams.get('codec')) == "idx":
                    printDebug.debug("Stream: %s - Ignoring idx file for now" % stream_id)
                    continue
                else:
                    sub_list.append(stream_id)

                    if streams.get('selected') == '1':
                        fl_select = True
                        language = streams.get('language', 'Unknown') + "*"
                    else:
                        language = streams.get('language', 'Unknown')

                    display_list.append(language)
        break

    if not fl_select:
        display_list[0] = display_list[0] + "*"

    subScreen = xbmcgui.Dialog()
    result = subScreen.select('Select subtitle', display_list)
    if result == -1:
        return False

    printDebug.debug("User has selected stream %s" % sub_list[result])
    server.set_subtitle_stream(part_id, sub_list[result])

    return True