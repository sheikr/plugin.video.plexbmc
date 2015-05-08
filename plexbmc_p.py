import sys
import time

plexbmc_start = time.time()
print "===== PlexBMC START [id: %s] =====" % plexbmc_start
print " >> PlexBMC Processing request: [%s] =====" % sys.argv

from resources.lib import plexbmc
plexbmc.start_plexbmc()

print "===== PlexBMC STOP [id: %s]: %s seconds =====" % (plexbmc_start, (time.time() - plexbmc_start))
sys.modules.clear()