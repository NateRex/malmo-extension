#!/usr/bin/python
# ===============================================================================================
# Name: Mission_2
# Description: Two-agent mission where a 'Farmer' agent kills cows and returns beef to a
#              'Player' agent
# ===============================================================================================

import sys              # <--- Delete this line if you installed malmoext using pip
sys.path.append("..")   # <--- Delete this line if you installed malmoext using pip
from malmoext import *



# CREATE THE MISSION ==============================================================================================

# Initialize Malmo for 2 agents, and create each agent
malmoutils.initializeMalmo(2)
builder = MissionBuilder("Farm Food for Player", 30000, TimeOfDay.Noon)
player_agent = builder.addAgent("Player", AgentType.Hardcoded, Vector(-15, 4, -16), Direction.North)
farmer_agent = builder.addAgent("Farmer", AgentType.Hardcoded, Vector(-15, 4, -15), Direction.South)

# Add items to the farmer agent's inventory
builder.agents["Farmer"].addInventory(Items.All.diamond_sword, InventorySlot.HotBar._0)

# Create structures in the environment
builder.environment.addLine(Blocks.Fence, Vector(-20, 4, -1), Vector(-20, 4, -20))
builder.environment.addLine(Blocks.Fence, Vector(3, 4, -1), Vector(3, 4, -20))
builder.environment.addLine(Blocks.Fence, Vector(-19, 4, -2), Vector(2, 4, -2))
builder.environment.addLine(Blocks.Fence, Vector(-19, 4, -20), Vector(2, 4, -20))

# Add cows to the environment
builder.environment.addMob(Mobs.Peaceful.Cow, Vector(-10, 4, -10))
builder.environment.addMob(Mobs.Peaceful.Cow, Vector(-10, 4, -15))



# START THE MISSION ==============================================================================================

# Set up loggers
logger = Logger()
logger.setLoggingLevel(farmer_agent,
    Logger.Flags.ClosestMob_Food,
    Logger.Flags.ClosestItem_Food)

# Start mission
malmoutils.loadMission(builder)
malmoutils.startMission()

# Start loggers
logger.start()



# DEFINE AGENT ACTIONS ===========================================================================================

while malmoutils.isMissionActive():
    logger.update()         # update the log
    #Performance.update()    # update performance data

    if farmer_agent.inventory.amountOfItem(Items.Food.beef) > 0:  # Give any held beef to the player
        if not farmer_agent.lookAt(player_agent):
            continue
        if not farmer_agent.moveTo(player_agent):
            continue
        farmer_agent.equip(Items.Food.beef)
        farmer_agent.giveItem(Items.Food.beef, player_agent)
        continue

    closestFood = farmer_agent.closestItem(Items.Food)  # Collect any beef laying on the ground nearby
    if closestFood != None:
        if not farmer_agent.lookAt(closestFood):
            continue
        if not farmer_agent.moveTo(closestFood):
            continue
        continue

    farmer_agent.equip(Items.All.diamond_sword)     # Harvest any nearby cows
    closestCow = farmer_agent.closestMob(Mobs.Food)
    if closestCow != None:
        if not farmer_agent.lookAt(closestCow):
            continue
        if not farmer_agent.moveTo(closestCow):
            continue
        if not farmer_agent.attackMob(closestCow):
            continue
        continue

    farmer_agent.stopMoving()   # Nothing to do...

# Stop the loggers
logger.stop()



# FINISH ==========================================================================================================
logger.export()
#Performance.export()