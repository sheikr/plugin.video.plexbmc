import xbmc
import xbmcgui

from .base_command import BaseCommand
from ..plexserver import plex_network
from ..utils import clear_shelf, clear_skin_sections, clear_on_deck_shelf


class CommandSignout(BaseCommand):
    def __init__(self, *args):
        super(CommandSignout, self).__init__(args)

    def execute(self):
        if not plex_network.is_admin():
            return xbmcgui.Dialog().ok("Sign Out",
                                       "To sign out you must be logged in as an admin user.",
                                       "Please switch user and try again")

        ret = xbmcgui.Dialog().yesno("myplex",
                                     "You are currently signed into myPlex.",
                                     "Are you sure you want to sign out?")
        if ret:
            plex_network.signout()
            window = xbmcgui.Window(10000)
            window.clearProperty("plexbmc.plexhome_user")
            window.clearProperty("plexbmc.plexhome_avatar")
            clear_skin_sections()
            clear_on_deck_shelf()
            clear_shelf()
            xbmc.executebuiltin("ReloadSkin()")