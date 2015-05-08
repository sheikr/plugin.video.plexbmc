from resources.lib.plexserver import plex_network
import xbmc
from .base_command import BaseCommand
from ..common import PrintDebug, AddonSettings
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandDelete")


class CommandDelete(BaseCommand):
    def __init__(self, *args):
        super(CommandDelete, self).__init__(args)

    def execute(self):
        plex_network.load()
        # server_uuid = sys.argv[2]
        # metadata_id = sys.argv[3]
        _delete_media(self.args[0], self.args[1])


def _delete_media(server_uuid, metadata_id):
    printDebug.debug("== ENTER ==")
    printDebug.info("Deleting media at: %s" % metadata_id)

    return_value = xbmcgui.Dialog().yesno("Confirm file delete?",
                                          "Delete this item? This action will delete media and associated data files.")

    if return_value:
        printDebug.debug("Deleting....")
        server = plex_network.get_server_from_uuid(server_uuid)
        server.delete_metadata(metadata_id)
        xbmc.executebuiltin("Container.Refresh")

    return True