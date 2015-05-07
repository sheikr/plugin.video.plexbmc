import xbmc
import xbmcgui

from .base_command import BaseCommand
from ..plexserver import plex_network
from ..common import PrintDebug, AddonSettings

settings = AddonSettings()
printDebug = PrintDebug("commands")


class CommandSwitchUser(BaseCommand):
    def __init__(self):
        super(CommandSwitchUser, self).__init__()

    def execute(self):
        if self.switch_user():
            clear_skin_sections()
            clearOnDeckShelf()
            clearShelf()
            WINDOW = xbmcgui.Window(10000)
            WINDOW.setProperty("plexbmc.plexhome_user", str(plex_network.get_myplex_user()))
            WINDOW.setProperty("plexbmc.plexhome_avatar", str(plex_network.get_myplex_avatar()))
            if xbmcgui.getCurrentWindowId() == 10000:
                printDebug.debug("Currently in home - refreshing to allow new settings to be taken")
                xbmc.executebuiltin("ReloadSkin()")
            else:
                xbmc.executebuiltin("Container.Refresh")
        else:
            printDebug.info("Switch User Failed")

    @staticmethod
    def switch_user():
        # Get list of users
        user_list = plex_network.get_plex_home_users()
        # zero means we are not plexHome'd up
        if user_list is None or len(user_list) == 1:
            printDebug("No users listed or only one user, plexHome not enabled")
            return False

        printDebug("found %s users: %s" % (len(user_list), user_list.keys()))

        # Get rid of currently logged in user.
        user_list.pop(plex_network.get_myplex_user(), None)

        select_screen = xbmcgui.Dialog()
        result = select_screen.select('Switch User', user_list.keys())
        if result == -1:
            printDebug("Dialog cancelled")
            return False

        printDebug("user [%s] selected" % user_list.keys()[result])
        user = user_list[user_list.keys()[result]]

        pin = None
        if user['protected'] == '1':
            printDebug("Protected user [%s], requesting password" % user['title'])
            pin = select_screen.input("Enter PIN", type=xbmcgui.INPUT_NUMERIC, option=xbmcgui.ALPHANUM_HIDE_INPUT)

        success, msg = plex_network.switch_plex_home_user(user['id'], pin)

        if not success:
            xbmcgui.Dialog().ok("Switch Failed",msg)
            return False

        return True