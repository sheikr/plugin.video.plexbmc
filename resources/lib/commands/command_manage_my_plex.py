import xbmc
import xbmcgui

from .base_command import BaseCommand
from ..plexserver import plex_network


class CommandManageMyPlex(BaseCommand):
    def __init__(self):
        super(CommandManageMyPlex, self).__init__()

    def execute(self):
        if not plex_network.is_myplex_signedin():
            ret = xbmcgui.Dialog().yesno("Manage myplex",
                                         "You are not currently logged into myplex.\
                                         Please continue to sign in, or cancel to return")
            if ret:
                xbmc.executebuiltin('XBMC.RunScript(plugin.video.plexbmc, signin)')
            else:
                return
        elif not plex_network.is_admin():
            return xbmcgui.Dialog().ok("Manage myplex",
                                       "To access these screens you must be logged in as an admin user.\
                                       Please switch user and try again")

        from myplex_dialogs import PlexManageDialog

        manage_window = PlexManageDialog('Manage myplex')
        manage_window.set_authentication_target(plex_network)
        manage_window.start()
        del manage_window