from .command_cache_refresh import CommandCacheRefresh

COMMAND_CACHE_REFRESH = "cacherefresh"


COMMAND_LIST = {
    COMMAND_CACHE_REFRESH: CommandCacheRefresh()
}