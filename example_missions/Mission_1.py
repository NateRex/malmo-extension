#!/usr/bin/python
# ===============================================================================================
# Name: Mission1
# Description: Two-agent mission where a 'companion' agent defends a 'player' agent using a sword
# ===============================================================================================

import sys              # <--- Delete this line if you installed malmoext using pip
sys.path.append("..")   # <--- Delete this line if you installed malmoext using pip
from malmoext import *

# CREATE AGENTS ==================================================================================
malmoutils.initializeMalmo(2)
player_agent = Agent("Player", AgentType.Hardcoded)
companion_agent = Agent("Companion", AgentType.Hardcoded)

# CREATE THE ENVIRONMENT =========================================================================
scenarioBuilder = ScenarioBuilder("Defend Player", 30000, player_agent.getId(), Vector(0, 4, 0), Direction.North)
scenarioBuilder.addAgent(companion_agent.getId(), Vector(0, 4, 2), Direction.South)
scenarioBuilder.setTimeOfDay(TimeOfDay.Midnight)

# Player inventory
scenarioBuilder.agents[0].addInventoryItem(ItemType.All.diamond_helmet, ItemSlot.Armor.Helmet)
scenarioBuilder.agents[0].addInventoryItem(ItemType.All.diamond_chestplate, ItemSlot.Armor.Chestplate)
scenarioBuilder.agents[0].addInventoryItem(ItemType.All.diamond_leggings, ItemSlot.Armor.Leggings)
scenarioBuilder.agents[0].addInventoryItem(ItemType.All.diamond_boots, ItemSlot.Armor.Boots)

# Companion inventory
scenarioBuilder.agents[1].addInventoryItem(ItemType.All.diamond_helmet, ItemSlot.Armor.Helmet)
scenarioBuilder.agents[1].addInventoryItem(ItemType.All.diamond_chestplate, ItemSlot.Armor.Chestplate)
scenarioBuilder.agents[1].addInventoryItem(ItemType.All.diamond_leggings, ItemSlot.Armor.Leggings)
scenarioBuilder.agents[1].addInventoryItem(ItemType.All.diamond_boots, ItemSlot.Armor.Boots)
scenarioBuilder.agents[1].addInventoryItem(ItemType.All.diamond_sword, ItemSlot.HotBar._0)

# Structures (cobblestone arena and ground torches)
scenarioBuilder.environment.addCube(Vector(-100, 3, -100), Vector(100, 30, 100), BlockType.Stone)
scenarioBuilder.environment.addCube(Vector(-99, 4, -99), Vector(99, 29, 99), BlockType.Air)
for i in range(-99, 99):
    for j in range(-99, 99):
        if i % 4 == 0 and j % 4 == 0:
            scenarioBuilder.environment.addBlock(Vector(i, 4, j), BlockType.Torch)

# Zombies
scenarioBuilder.environment.addMob(Vector(2, 4, 4), MobType.Hostile.Zombie)
scenarioBuilder.environment.addMob(Vector(-20, 4, 20), MobType.Hostile.Zombie)
scenarioBuilder.environment.addMob(Vector(5, 4, -11), MobType.Hostile.Zombie)

# START THE MISSION ==============================================================================
malmoutils.loadEnvironment(scenarioBuilder.finish())
malmoutils.loadAgents(player_agent, companion_agent)
malmoutils.startMission()
malmoutils.startLogging(player_agent, LogFlags.ClosestHostileMob.value)   # want verbose output for zombies close to player

# AGENT ACTIONS ==================================================================================
while player_agent.isMissionActive() or companion_agent.isMissionActive():
    # Update the performance of each agent
    Performance.update()

    # Ensure we have our diamond sword equipped (should be by default)
    companion_agent.equip(ItemType.All.diamond_sword)

    # If there is a zombie close to the player, target it for attack
    zombie = player_agent.getClosestHostileMob()
    if zombie != None:
        isLookingAt = companion_agent.lookAtEntity(zombie)
        if not isLookingAt:
            continue
        isAt = companion_agent.moveToEntity(zombie)
        if not isAt:
            continue
        companion_agent.attackMob(zombie)
        continue

    # No zombies nearby... return to player
    isLookingAt = companion_agent.lookAtAgent(player_agent)
    if not isLookingAt:
        continue
    isAt = companion_agent.moveToAgent(player_agent)
    if not isAt:
        continue

    # Nothing to do...
    companion_agent.stopAllMovement()

# CLEANUP =========================================================================================
malmoutils.finish()