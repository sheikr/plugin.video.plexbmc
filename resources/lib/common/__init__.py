from constants import *
from print_debug import PrintDebug
from cache_control import CacheControl
from addon_settings import AddonSettings

settings = AddonSettings('plugin.video.plexbmc')


from private_func import is_ip
from private_func import wake_servers as __wake_up_internal


def wake_servers():
    return __wake_up_internal(settings)










