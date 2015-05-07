from .command_cache_refresh import CommandCacheRefresh
from .command_settings import CommandSettings
from .command_refresh import CommandRefresh
from .command_switch_user import CommandSwitchUser

COMMAND_CACHE_REFRESH = "cacherefresh"
COMMAND_SETTINGS = "settings"
COMMAND_REFRESH = "refresh"
COMMAND_SWITCH_USER = "switchuser"


COMMANDS = {
    COMMAND_CACHE_REFRESH: CommandCacheRefresh,
    COMMAND_SETTINGS: CommandSettings,
    COMMAND_REFRESH: CommandRefresh,
    COMMAND_SWITCH_USER: CommandSwitchUser
}