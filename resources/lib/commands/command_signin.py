from .base_command import BaseCommand
from ..plexserver import plex_network
from ..myplex_dialogs import PlexSigninDialog


class CommandSignin(BaseCommand):
    def __init__(self):
        super(CommandSignin, self).__init__()

    def execute(self):
        signin_window = PlexSigninDialog('Myplex Login')
        signin_window.set_authentication_target(plex_network)
        signin_window.start()
        del signin_window