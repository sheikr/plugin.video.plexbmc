from .command_cache_refresh import CommandCacheRefresh
from .command_settings import CommandSettings
from .command_refresh import CommandRefresh
from .command_switch_user import CommandSwitchUser
from .command_signout import CommandSignout
from .command_signin import CommandSignin
from .command_signin_temp import CommandSigninTemp
from .command_manage_my_plex import CommandManageMyPlex


COMMAND_CACHE_REFRESH = "cacherefresh"
COMMAND_SETTINGS = "setting"
COMMAND_REFRESH = "refresh"
COMMAND_SWITCH_USER = "switchuser"
COMMAND_SIGNOUT = "signout"
COMMAND_SIGNIN = "signin"
COMMAND_SIGNIN_TEMP = "signintemp"
COMMAND_MANAGE_MY_PLEX = "managemyplex"


COMMANDS = {
    COMMAND_CACHE_REFRESH: CommandCacheRefresh,
    COMMAND_SETTINGS: CommandSettings,
    COMMAND_REFRESH: CommandRefresh,
    COMMAND_SWITCH_USER: CommandSwitchUser,
    COMMAND_SIGNOUT: CommandSignout,
    COMMAND_SIGNIN: CommandSignin,
    COMMAND_SIGNIN_TEMP: CommandSigninTemp,
    COMMAND_MANAGE_MY_PLEX: CommandManageMyPlex
}