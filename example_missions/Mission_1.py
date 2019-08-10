#!/usr/bin/python
# ===============================================================================================
# Name: Mission1
# Description: Two-agent mission where a 'defender' agent protects a 'player' agent using a sword
# ===============================================================================================

import sys              # <--- Delete this line if you installed malmoext using pip
sys.path.append("..")   # <--- Delete this line if you installed malmoext using pip
from malmoext import *

# CREATE THE MISSION ==============================================================================================

# Initialize Malmo for 2 agents, and create each agent using the mission builder
malmoutils.initializeMalmo(2)
builder = MissionBuilder("Defend Player", 30000, TimeOfDay.Midnight)
player_agent = builder.addAgent("Player", AgentType.Hardcoded, Vector(0, 4, 0), Direction.North)
defender_agent = builder.addAgent("Defender", AgentType.Hardcoded, Vector(0, 4, 2), Direction.South)

# Add items to the player agent's inventory using the mission builder
builder.agents["Player"].addInventory(Items.All.diamond_helmet, InventorySlot.Armor.Helmet)
builder.agents["Player"].addInventory(Items.All.diamond_chestplate, InventorySlot.Armor.Chestplate)
builder.agents["Player"].addInventory(Items.All.diamond_leggings, InventorySlot.Armor.Leggings)
builder.agents["Player"].addInventory(Items.All.diamond_boots, InventorySlot.Armor.Boots)

# Add items to the defender agent's inventory using the mission builder
builder.agents["Defender"].addInventory(Items.All.diamond_helmet, InventorySlot.Armor.Helmet)
builder.agents["Defender"].addInventory(Items.All.diamond_chestplate, InventorySlot.Armor.Chestplate)
builder.agents["Defender"].addInventory(Items.All.diamond_leggings, InventorySlot.Armor.Leggings)
builder.agents["Defender"].addInventory(Items.All.diamond_boots, InventorySlot.Armor.Boots)
builder.agents["Defender"].addInventory(Items.All.diamond_sword, InventorySlot.HotBar._0)

# Create structures in the environment using the mission builder
builder.environment.addCube(Blocks.Stone, Vector(-100, 3, -100), Vector(100, 30, 100))
builder.environment.addCube(Blocks.Air, Vector(-99, 4, -99), Vector(99, 29, 99))
for i in range(-99, 99):
    for j in range(-99, 99):
        if i % 4 == 0 and j % 4 == 0:
            builder.environment.addBlock(Blocks.Torch, Vector(i, 4, j))

# Add attackers to the environment using the mission builder
builder.environment.addMob(Mobs.Hostile.Zombie, Vector(2, 4, 4))
builder.environment.addMob(Mobs.Hostile.Zombie, Vector(-20, 4, 20))
builder.environment.addMob(Mobs.Hostile.Zombie, Vector(5, 4, -11))


# START THE MISSION ==============================================================================================

# Set up loggers
logger = Logger()
logger.setLoggingLevel(player_agent, Logger.Flags.ClosestMob_Hostile)

# Start mission
malmoutils.loadMission(builder)
malmoutils.startMission()

# Start loggers
logger.start()

# DEFINE AGENT ACTIONS ===========================================================================================

while malmoutils.isMissionActive():
    logger.update()         # update the log
    Performance.update()    # update performance data

    defender_agent.equip(Items.All.diamond_sword)   # ensure sword is equipped

    zombie = player_agent.getClosestHostileMob()    # target closest zombie to the player
    if zombie != None:
        isLookingAt = defender_agent.lookAtEntity(zombie)
        if not isLookingAt:
            continue
        isAt = defender_agent.moveToEntity(zombie)
        if not isAt:
            continue
        defender_agent.attackMob(zombie)
        continue

    isLookingAt = defender_agent.lookAtAgent(player_agent)     # no zombies.. move to player
    if not isLookingAt:
        continue
    isAt = defender_agent.moveToAgent(player_agent)
    if not isAt:
        continue

    # Nothing to do...
    defender_agent.stopAllMovement()



# FINISH ==========================================================================================================
logger.export()
Performance.export()