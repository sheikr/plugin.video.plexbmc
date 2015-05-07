import sys
import time

plexbmc_start = time.time()
print "===== PlexBMC START [id: %s] =====" % plexbmc_start

from resources.lib import plexbmc
plexbmc.start_plexbmc()

print "===== PlexBMC STOP [id: %s]: %s seconds =====" % (plexbmc_start, (time.time() - plexbmc_start))
sys.modules.clear()