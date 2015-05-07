import xbmc
from .base_command import BaseCommand


class CommandRefresh(BaseCommand):
    def __init__(self, *args):
        super(CommandRefresh, self).__init__(args)

    def execute(self):
        xbmc.executebuiltin("Container.Refresh")