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
companion_agent = builder.addAgent("Defender", AgentType.Hardcoded, Vector(0, 4, 2), Direction.South)

# Add items to the player agent's inventory using the mission builder
builder.agents["Player"].addInventory(ItemType.All.diamond_helmet, ItemSlot.Armor.Helmet)
builder.agents["Player"].addInventory(ItemType.All.diamond_chestplate, ItemSlot.Armor.Chestplate)
builder.agents["Player"].addInventory(ItemType.All.diamond_leggings, ItemSlot.Armor.Leggings)
builder.agents["Player"].addInventory(ItemType.All.diamond_boots, ItemSlot.Armor.Boots)

# Add items to the defender agent's inventory using the mission builder
builder.agents["Defender"].addInventory(ItemType.All.diamond_helmet, ItemSlot.Armor.Helmet)
builder.agents["Defender"].addInventory(ItemType.All.diamond_chestplate, ItemSlot.Armor.Chestplate)
builder.agents["Defender"].addInventory(ItemType.All.diamond_leggings, ItemSlot.Armor.Leggings)
builder.agents["Defender"].addInventory(ItemType.All.diamond_boots, ItemSlot.Armor.Boots)
builder.agents["Defender"].addInventory(ItemType.All.diamond_sword, ItemSlot.HotBar._0)

# Create structures in the environment using the mission builder
builder.environment.addCube(BlockType.Stone, Vector(-100, 3, -100), Vector(100, 30, 100))
builder.environment.addCube(BlockType.Air, Vector(-99, 4, -99), Vector(99, 29, 99))
for i in range(-99, 99):
    for j in range(-99, 99):
        if i % 4 == 0 and j % 4 == 0:
            builder.environment.addBlock(BlockType.Torch, Vector(i, 4, j))

# Add attackers to the environment using the mission builder
builder.environment.addMob(MobType.Hostile.Zombie, Vector(2, 4, 4))
builder.environment.addMob(MobType.Hostile.Zombie, Vector(-20, 4, 20))
builder.environment.addMob(MobType.Hostile.Zombie, Vector(5, 4, -11))


# START THE MISSION ==============================================================================================

malmoutils.loadMission(builder)
malmoutils.startMission()
malmoutils.startLogging(
    player_agent, LogFlags.ClosestHostileMob.value  # want verbose output for zombies close to player
)



# DEFINE AGENT ACTIONS ===========================================================================================

while player_agent.isMissionActive() or companion_agent.isMissionActive():
    Performance.update()    # update performance data

    companion_agent.equip(ItemType.All.diamond_sword)   # ensure sword is equipped

    zombie = player_agent.getClosestHostileMob()    # target closest zombie to the player
    if zombie != None:
        isLookingAt = companion_agent.lookAtEntity(zombie)
        if not isLookingAt:
            continue
        isAt = companion_agent.moveToEntity(zombie)
        if not isAt:
            continue
        companion_agent.attackMob(zombie)
        continue

    isLookingAt = companion_agent.lookAtAgent(player_agent)     # no zombies.. move to player
    if not isLookingAt:
        continue
    isAt = companion_agent.moveToAgent(player_agent)
    if not isAt:
        continue

    # Nothing to do...
    companion_agent.stopAllMovement()



# CLEANUP =========================================================================================

malmoutils.finish()