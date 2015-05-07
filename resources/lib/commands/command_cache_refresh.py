from .base_command import BaseCommand
from ..plexserver import plex_network
import xbmc

__author__ = 'oburdun'


class CommandCacheRefresh(BaseCommand):
    def __init__(self):
        super(CommandCacheRefresh, self).__init__()

    def execute(self):
        plex_network.delete_cache()
        xbmc.executebuiltin("ReloadSkin()")