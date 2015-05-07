import xbmc
from .base_command import BaseCommand
from ..plexserver import plex_network


class CommandCacheRefresh(BaseCommand):
    def __init__(self, *args):
        super(CommandCacheRefresh, self).__init__(args)
        return

    def execute(self):
        plex_network.delete_cache()
        xbmc.executebuiltin("ReloadSkin()")
        return