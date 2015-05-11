from .command_cache_refresh import CommandCacheRefresh
from .command_settings import CommandSettings
from .command_refresh import CommandRefresh
from .command_switch_user import CommandSwitchUser
from .command_signout import CommandSignout
from .command_signin import CommandSignin
from .command_signin_temp import CommandSigninTemp
from .command_manage_my_plex import CommandManageMyPlex

from .command_skin import CommandSkin
from .command_amberskin import CommandAmberSkin
from .command_shelf import CommandShelf
from .command_channel_shelf import CommandChannelShelf
from .command_update import CommandUpdate
from .command_watch import CommandWatch
from .command_delete import CommandDelete
from .command_subs import CommandSubs
from .command_audio import CommandAudio
from .command_master import CommandMaster


COMMAND_CACHE_REFRESH = "cacherefresh"
COMMAND_SETTINGS = "setting"
COMMAND_REFRESH = "refresh"
COMMAND_SWITCH_USER = "switchuser"
COMMAND_SIGNOUT = "signout"
COMMAND_SIGNIN = "signin"
COMMAND_SIGNIN_TEMP = "signintemp"
COMMAND_MANAGE_MY_PLEX = "managemyplex"

COMMAND_SKIN = "skin"
COMMAND_AMBERSKIN = "amberskin"
COMMAND_SHELF = "shelf"
COMMAND_CHANNEL_SHELF = "channelShelf"
COMMAND_UPDATE = "update"
COMMAND_WATCH = "watch"
COMMAND_DELETE = "delete"
COMMAND_SUBS = "subs"
COMMAND_AUDIO = "audio"
COMMAND_MASTER = "master"

COMMANDS = {
    COMMAND_CACHE_REFRESH: CommandCacheRefresh,
    COMMAND_SETTINGS: CommandSettings,
    COMMAND_REFRESH: CommandRefresh,
    COMMAND_SWITCH_USER: CommandSwitchUser,
    COMMAND_SIGNOUT: CommandSignout,
    COMMAND_SIGNIN: CommandSignin,
    COMMAND_SIGNIN_TEMP: CommandSigninTemp,
    COMMAND_MANAGE_MY_PLEX: CommandManageMyPlex,

    COMMAND_SKIN: CommandSkin,
    COMMAND_AMBERSKIN: CommandAmberSkin,
    COMMAND_SHELF: CommandShelf,
    COMMAND_CHANNEL_SHELF: CommandChannelShelf,
    COMMAND_UPDATE: CommandUpdate,
    COMMAND_WATCH: CommandWatch,
    COMMAND_DELETE: CommandDelete,
    COMMAND_SUBS: CommandSubs,
    COMMAND_AUDIO: CommandAudio,
    COMMAND_MASTER: CommandMaster
}