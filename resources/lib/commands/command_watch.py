from ..plexserver import plex_network
import xbmc
from .base_command import BaseCommand
from ..common import PrintDebug, AddonSettings

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandWatch")


class CommandWatch(BaseCommand):
    def __init__(self, *args):
        super(CommandWatch, self).__init__(args)

    def execute(self):
        plex_network.load()
        # server_uuid = sys.argv[2]
        # metadata_id = sys.argv[3]
        # watch_status = sys.argv[4]
        _watched(self.args[0], self.args[1], self.args[2])


def _watched(server_uuid, metadata_id, watched='watch'):
    printDebug.debug("== ENTER ==")

    server = plex_network.get_server_from_uuid(server_uuid)

    if watched == 'watch':
        printDebug.info("Marking %s as watched" % metadata_id)
        server.mark_item_watched(metadata_id)
    else:
        printDebug.info("Marking %s as unwatched" % metadata_id)
        server.mark_item_unwatched(metadata_id)

    xbmc.executebuiltin("Container.Refresh")

    return