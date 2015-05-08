from ..plexserver import plex_network
import xbmc
from .base_command import BaseCommand
from ..common import PrintDebug, AddonSettings

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandUpdate")


class CommandUpdate(BaseCommand):
    def __init__(self, *args):
        super(CommandUpdate, self).__init__(args)

    def execute(self):
        plex_network.load()
        # server_uuid = sys.argv[2]
        # section_id = sys.argv[3]
        _library_refresh(self.args[0], self.args[1])


def _library_refresh(server_uuid, section_id):
    printDebug.debug("== ENTER ==")

    server = plex_network.get_server_from_uuid(server_uuid)
    server.refresh_section(section_id)

    printDebug.info("Library refresh requested")
    xbmc.executebuiltin("XBMC.Notification(\"PleXBMC\",Library Refresh started,100)")
    return