import xbmc
from .base_command import BaseCommand


class CommandRefresh(BaseCommand):
    def __init__(self):
        super(CommandRefresh, self).__init__()

    def execute(self):
        xbmc.executebuiltin("Container.Refresh")