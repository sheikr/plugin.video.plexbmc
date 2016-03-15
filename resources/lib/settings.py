import os
import xbmcaddon


class AddonSettings:

    def __init__(self, name):
        print "PleXBMC -> Reading settings configuration"
        self.settings = xbmcaddon.Addon(name)
        self.stream = self.settings.getSetting('streaming')

    def open_settings(self):
        return self.settings.openSettings()

    def get_setting(self, name):
        value = self.settings.getSetting(name)

        if value is None or value == '':
            print "setting: %s is : %s" % (name, value)

        if value == "true":
            return True
        elif value == "false":
            return False
        else:
            return value

    def get_debug(self):
        if self.settings.getSetting('debug') == 'true':
            print "PLEXBMC < 3.6 debug setting detected - settings must be re-saved"
            self.settings.setSetting('debug', '2')
            return 2
        elif self.settings.getSetting('debug') == 'false':
            print "PLEXBMC < 3.6 debug setting detected - settings must be re-saved"
            self.settings.setSetting('debug', '1')
            return 0

        return int(self.settings.getSetting('debug'))

    def set_setting(self, name, value):
        if value:
            value = "true"
        else:
            value = "false"

        self.settings.setSetting(name, value)

    def get_wakeservers(self):
        wakeserver = []
        for servers in range(1, 12):
            wakeserver.append(self.settings.getSetting('wol%s' % servers))
        return wakeserver

    def get_stream(self):
        return self.stream

    def set_stream(self, value):
        self.stream = value

    def dump_settings(self):
        return self.__dict__

    def update_master_server(self, value):
        print "Updating master server to%s" % value
        self.settings.setSetting('masterServer', '%s' % value)
