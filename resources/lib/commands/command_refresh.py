__author__ = 'Dukobpa3'
from .base_command import BaseCommand
import xbmc


class CommandRefresh(BaseCommand):
    def __init__(self):
        super(CommandRefresh, self).__init__()

    def execute(self):
        xbmc.executebuiltin("Container.Refresh")