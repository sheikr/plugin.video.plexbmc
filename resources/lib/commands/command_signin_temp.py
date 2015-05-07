from .base_command import BaseCommand
import xbmc


class CommandSigninTemp(BaseCommand):
    def __init__(self):
        super(CommandSigninTemp, self).__init__()

    def execute(self):
        # Awful hack to get around running a script from a listitem..
        xbmc.executebuiltin('XBMC.RunScript(plugin.video.plexbmc, signin)')