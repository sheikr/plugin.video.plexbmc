import xbmc
import xbmcgui

from .base_command import BaseCommand
from ..common import PrintDebug, AddonSettings
settings = AddonSettings()
printDebug = PrintDebug("commands")


class CommandSettings(BaseCommand):
    def __init__(self):
        super(CommandSettings, self).__init__()

    def execute(self):
        settings.open_settings()
        if xbmcgui.getCurrentWindowId() == 10000:
            printDebug.debug("Currently in home - refreshing to allow new settings to be taken")
            xbmc.executebuiltin("ReloadSkin()")