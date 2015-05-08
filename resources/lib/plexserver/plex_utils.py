from ..common import PrintDebug, AddonSettings
from .plex import plex_network

printDebug = PrintDebug("PleXBMC", "plexserver.plex_utils")
settings = AddonSettings()


def get_master_server(all=False):
    printDebug.debug("== ENTER ==")

    possibleServers = []
    current_master = settings.get_setting('masterServer')
    for serverData in plex_network.get_server_list():
        printDebug.debug(str(serverData))
        if serverData.get_master() == 1:
            possibleServers.append(serverData)
    printDebug.debug("Possible master servers are: %s" % possibleServers)

    if all:
        return possibleServers

    if len(possibleServers) > 1:
        preferred = "local"
        for serverData in possibleServers:
            if serverData.get_name == current_master:
                printDebug.debug("Returning current master")
                return serverData
            if preferred == "any":
                printDebug.debug("Returning 'any'")
                return serverData
            else:
                if serverData.get_discovery() == preferred:
                    printDebug.debug("Returning local")
                    return serverData
    elif len(possibleServers) == 0:
        return

    return possibleServers[0]