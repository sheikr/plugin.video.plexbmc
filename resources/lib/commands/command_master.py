from .base_command import BaseCommand
from ..plexserver import plex_network, get_master_server
from ..common import PrintDebug, AddonSettings
import xbmcgui

settings = AddonSettings()
printDebug = PrintDebug("PleXBMC", "CommandMaster")


class CommandMaster(BaseCommand):
    def __init__(self, *args):
        super(CommandMaster, self).__init__(args)

    def execute(self):
        plex_network.load()
        _set_master_server()


def _set_master_server():
    printDebug.debug("== ENTER ==")

    servers = get_master_server(True)
    printDebug.debug(str(servers))

    current_master = settings.get_setting('masterServer')

    display_list = []
    for address in servers:
        found_server = address.get_name()
        if found_server == current_master:
            found_server += "*"
        display_list.append(found_server)

    audio_screen = xbmcgui.Dialog()
    result = audio_screen.select('Select master server', display_list)
    if result == -1:
        return False

    printDebug.debug("Setting master server to: %s" % servers[result].get_name())
    settings.update_master_server(servers[result].get_name())
    return