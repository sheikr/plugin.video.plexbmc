from .base_command import BaseCommand
from ..plexserver import plex_network
from ..common import PrintDebug, AddonSettings
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandAudio")


class CommandAudio(BaseCommand):
    def __init__(self, *args):
        super(CommandAudio, self).__init__(*args)

    def execute(self):
        plex_network.load()
        # server_uuid = sys.argv[2]
        # metadata_id = sys.argv[3]
        _alter_audio(self.args[0], self.args[1])


def _alter_audio(server_uuid, metadata_id):
    """
        Display a list of available audio streams and allow a user to select one.
        The currently selected stream will be annotated with a *
    """
    printDebug.debug("== ENTER ==")

    server = plex_network.get_server_from_uuid(server_uuid)
    tree = server.get_metadata(metadata_id)

    audio_list = []
    display_list = []
    for parts in tree.getiterator('Part'):

        part_id = parts.get('id')

        for streams in parts:

            if streams.get('streamType', '') == "2":

                stream_id = streams.get('id')
                audio_list.append(stream_id)
                lang = streams.get('languageCode', "Unknown")

                printDebug.debug("Detected Audio stream [%s] [%s] " % ( stream_id, lang))

                if streams.get('channels', 'Unknown') == '6':
                    channels = "5.1"
                elif streams.get('channels', 'Unknown') == '7':
                    channels = "6.1"
                elif streams.get('channels', 'Unknown') == '2':
                    channels = "Stereo"
                else:
                    channels = streams.get('channels', 'Unknown')

                if streams.get('codec', 'Unknown') == "ac3":
                    codec = "AC3"
                elif streams.get('codec', 'Unknown') == "dca":
                    codec = "DTS"
                else:
                    codec = streams.get('codec', 'Unknown')

                language = "%s (%s %s)" % ( streams.get('language', 'Unknown').encode('utf-8'), codec, channels )

                if streams.get('selected') == '1':
                    language += "*"

                display_list.append(language)
        break

    audio_screen = xbmcgui.Dialog()
    result = audio_screen.select('Select audio', display_list)
    if result == -1:
        return False

    printDebug.debug("User has selected stream %s" % audio_list[result])

    server.set_audio_stream(part_id, audio_list[result])

    return True