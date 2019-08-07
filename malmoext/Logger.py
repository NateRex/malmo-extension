# ==============================================================================================
# This file exposes functionality for logging traces containing both state and action
# information of a particular agent at regular intervals.
# ==============================================================================================
from datetime import datetime
import os
import time
from malmoext.Utils import *
from malmoext.AgentInventory import *

class LogFlags(Enum):
    """
    Enumerated type for setting the flags of the Logger class on which state information to track in the initial and final state.
    """
    ClosestMob          = 0x1
    ClosestPeacefulMob  = 0x2
    ClosestHostileMob   = 0x4
    ClosestFoodMob      = 0x8
    ClosestFoodItem     = 0x10
    Inventory           = 0x20

class Logger:
    """
    Purely static class containing functionality for logging traces containing state and action information
    as a result of actions performed by a companion agent. All of the methods in this class should be called
    from a corresponding action method, such that the trace output is produced as a direct result of performing
    an action.
    """
    __contents = []                 # The string containing the entire log
    __currentState = []             # A list of atom strings defining the current environment state as a whole
    __declaredEntityIds = []        # A list of entity ids for entities that have already been declared in the log
    __stateFlags = [0] * 5          # A list of flag values for determining what information to write out to the initial and final state for EACH AGENT (maximum of 5)

    @staticmethod
    def clearTrackingFlags():
        """
        Clears the flags denoting what state information to track in the initial and final states for all agents.
        """
        for i in range(0, len(Logger.__stateFlags)):
            Logger.__stateFlags[i] = 0

    @staticmethod
    def addAgentLogging(*agentMaskList):
        '''
        For each agent that requires additional/verbose logging, list the agent, followed by a mask consisting of LogFlags.
        '''
        i = 0
        listLen = len(agentMaskList)
        while i < listLen:
            if i + 1 >= listLen:
                raise Exception("expected LogFlags mask for given agent")
            mask = agentMaskList[i + 1]
            if not isinstance(mask, int):
                raise Exception("expected LogFlags mask for given agent")
            Logger.__stateFlags[agentMaskList[i].getIndex()] = mask
            i += 2

    @staticmethod
    def isTrackingClosestMob(agent):
        """
        Returns true if the Logger is set to track the closest mob of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.ClosestMob.value) != 0

    @staticmethod
    def isTrackingClosestPeacefulMob(agent):
        """
        Returns true if the Logger is set to track the closest peaceful mob of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.ClosestPeacefulMob.value) != 0

    @staticmethod
    def isTrackingClosestHostileMob(agent):
        """
        Returns true if the Logger is set to track the closest hostile mob of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.ClosestHostileMob.value) != 0

    @staticmethod
    def isTrackingClosestFoodMob(agent):
        """
        Returns true if the Logger is set to track the closest food mob of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.ClosestFoodMob.value) != 0

    @staticmethod
    def isTrackingClosestFoodItem(agent):
        """
        Returns true if the Logger is set to track the closest food item of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.ClosestFoodItem.value) != 0

    @staticmethod
    def isTrackingInventory(agent):
        """
        Returns true if the Logger is set to track the inventory of an agent in the initial and final states.
        """
        return (Logger.__stateFlags[agent.getIndex()] & LogFlags.Inventory.value) != 0

    @staticmethod
    def getCurrentState(agents):
        """
        Returns a list of string atoms that define the current environment state from all agent perspectives.
        """
        # For each agent, update any information we are tracking that could potentially change on each function call
        for agent in agents:
            if Logger.isTrackingClosestMob(agent):
                agent.getClosestMob()
            if Logger.isTrackingClosestPeacefulMob(agent):
                agent.getClosestPeacefulMob()
            if Logger.isTrackingClosestHostileMob(agent):
                agent.getClosestHostileMob()
            if Logger.isTrackingClosestFoodMob(agent):
                agent.getClosestFoodMob()
            if Logger.isTrackingClosestFoodItem(agent):
                agent.getClosestFoodItem()
        return Logger.__currentState

    @staticmethod
    def __getTime__():
        """
        Internal method for getting a string containing the current time and date.
        """
        return datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y %H:%M:%S.%f')


    @staticmethod
    def isEntityDefined(entity):
        """
        Returns true if this entity was already previously defined in the log. Returns false otherwise.
        """
        if entity.id in Logger.__declaredEntityIds:
            return True
        return False

    @staticmethod
    def __logAt__(entity, landmark):
        """
        Logs that an entity is located at a specific landmark (which is another entity in the world).
        """
        Logger.__pushStatement__("at-{}-{}".format(entity.id, landmark.id))

        # Fix up current state
        didChangeCurrentState = False
        for i in range(0, len(Logger.__currentState)):
            if Logger.__currentState[i].startswith("at-{}".format(entity.id)):
                Logger.__currentState[i] = "at-{}-{}".format(entity.id, landmark.id)
                didChangeCurrentState = True
                break
        if not didChangeCurrentState:
            Logger.__currentState.append("at-{}-{}".format(entity.id, landmark.id))

    @staticmethod
    def logInitialState(agents):
        """
        Given the list of agents for a mission, log the starting state for the environment in the log.
        """
        # Log the None entity to define a placeholder for anything not yet set in the trace file (we shove this into the mobs section)
        # TODO: This should really be some kind of universal thing, and not just a mob (what if we have closest_food_item-None?...)
        Logger.__pushStatement__("none-None-NoneType")
        Logger.__currentState.append("none-None-NoneType")

        for agent in agents:
            agentId = agent.getId()

            # Log the definition of this agent
            Logger.__logAgentDefinition__(agent)

            # Log all entities that the agent has identified nearby
            entities = agent.getNearbyEntities()
            if entities != None:
                for entity in entities:
                    Logger.logEntityDefinition(entity)
                    
            # Log starting inventory and equipped item
            if Logger.isTrackingInventory(agent):
                agent.inventory.update()
                inventoryItems = agent.inventory.allItems()
                for item in inventoryItems:
                    Logger.logItemDefinition(item)
                    Logger.__logAt__(item, agent)
                equippedItem = agent.currentlyEquipped()
                equippedItemId = "None" if equippedItem == None else equippedItem.id
                Logger.__pushStatement__("equipped_item-{}-{}".format(agentId, equippedItemId))
                agent.lastEquippedItem = equippedItemId     # Hacky way of making sure we don't re-log equipping the item after the START symbol

            # Log additional starting data dependent on the Logger flags set (getClosestXXX automatically logs)
            Logger.__pushStatement__("looking_at-{}-None".format(agentId))
            Logger.__currentState.append("looking_at-{}-None".format(agentId))
            Logger.__pushStatement__("at-{}-None".format(agentId))
            Logger.__currentState.append("at-{}-None".format(agentId))
            if Logger.isTrackingClosestMob(agent):
                agent.getClosestMob()
            if Logger.isTrackingClosestPeacefulMob(agent):
                agent.getClosestPeacefulMob()
            if Logger.isTrackingClosestHostileMob(agent):
                agent.getClosestHostileMob()
            if Logger.isTrackingClosestFoodMob(agent):
                agent.getClosestFoodMob()
            if Logger.isTrackingClosestFoodItem(agent):
                agent.getClosestFoodItem()

        Logger.__pushStatement__("START")
        Logger.__pushNewline__()

    @staticmethod
    def logFinalState(agents):
        """
        Log the end state for the environment in the log.
        """
        Logger.__pushNewline__()
        Logger.__pushStatement__("END")

        # Log the current state (ignore closestXXX information, as we will manually refresh and print out each)
        for statement in Logger.__currentState:
            if not statement.startswith("closest_"):
                Logger.__pushStatement__(statement)

        # Refresh and log closest entity information (calling getClosestXXX automatically logs)
        # TODO: It might be better to pull this from the _currentState instead for better accuracy...
        for agent in agents:
            agent.resetClosestEntityRecords()
            if Logger.isTrackingClosestMob(agent):
                agent.getClosestMob()
            if Logger.isTrackingClosestPeacefulMob(agent):
                agent.getClosestPeacefulMob()
            if Logger.isTrackingClosestHostileMob(agent):
                agent.getClosestHostileMob()
            if Logger.isTrackingClosestFoodMob(agent):
                agent.getClosestFoodMob()
            if Logger.isTrackingClosestFoodItem(agent):
                agent.getClosestFoodItem()


    @staticmethod
    def logClosestMob(agent, mob):
        """
        Log the closest mob to the agent given.
        """
        agentId = agent.getId()

        # Special case, where there is no closest mob
        if mob == None:
            if "None" != agent.lastClosestMob:
                closestLog = "closest_mob-{}-None".format(agentId)
                Logger.__pushStatement__(closestLog)
                didModifyCurrentState = False
                for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                    if Logger.__currentState[i].startswith("closest_mob-{}".format(agentId)):
                        Logger.__currentState[i] = closestLog
                        didModifyCurrentState = True
                        break
                if not didModifyCurrentState:
                    Logger.__currentState.append(closestLog)
            return

        if not isMob(mob.type):
            return

        # This might be an entity not previously declared in the log. Log its definition if so.
        Logger.logMobDefinition(mob)

        if mob.id != agent.lastClosestMob:
            closestLog = "closest_mob-{}-{}".format(agentId, mob.id)
            Logger.__pushStatement__(closestLog)
            didModifyCurrentState = False
            for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                if Logger.__currentState[i].startswith("closest_mob-{}".format(agentId)):
                    Logger.__currentState[i] = closestLog
                    didModifyCurrentState = True
                    break
            if not didModifyCurrentState:
                Logger.__currentState.append(closestLog)


    @staticmethod
    def logClosestPeacefulMob(agent, mob):
        """
        Log the closest peaceful entity to the agent given.
        """
        agentId = agent.getId()

        # Special case, where there is no closest peaceful mob
        if mob == None:
            if "None" != agent.lastClosestPeacefulMob:
                closestLog = "closest_peaceful_mob-{}-None".format(agentId)
                Logger.__pushStatement__(closestLog)
                didModifyCurrentState = False
                for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                    if Logger.__currentState[i].startswith("closest_peaceful_mob-{}".format(agentId)):
                        Logger.__currentState[i] = closestLog
                        didModifyCurrentState = True
                        break
                if not didModifyCurrentState:
                    Logger.__currentState.append(closestLog)
            return

        if not isPeacefulMob(mob.type):
            return

        # This might be an entity not previously declared in the log. Log its definition if so.
        Logger.logMobDefinition(mob)

        if mob.id != agent.lastClosestPeacefulMob:
            closestLog = "closest_peaceful_mob-{}-{}".format(agentId, mob.id)
            Logger.__pushStatement__(closestLog)
            didModifyCurrentState = False
            for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                if Logger.__currentState[i].startswith("closest_peaceful_mob-{}".format(agentId)):
                    Logger.__currentState[i] = closestLog
                    didModifyCurrentState = True
                    break
            if not didModifyCurrentState:
                Logger.__currentState.append(closestLog)

    @staticmethod
    def logClosestHostileMob(agent, mob):
        """
        Log the closest hostile entity to the agent given.
        """
        agentId = agent.getId()

        # Special case, where there is no closest hostile mob
        if mob == None:
            if "None" != agent.lastClosestHostileMob:
                closestLog = "closest_hostile_mob-{}-None".format(agentId)
                Logger.__pushStatement__(closestLog)
                didModifyCurrentState = False
                for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                    if Logger.__currentState[i].startswith("closest_hostile_mob-{}".format(agentId)):
                        Logger.__currentState[i] = closestLog
                        didModifyCurrentState = True
                        break
                if not didModifyCurrentState:
                    Logger.__currentState.append(closestLog)
            return

        if not isHostileMob(mob.type):
            return

        # This might be an entity not previously declared in the log. Log its definition if so.
        Logger.logMobDefinition(mob)

        if mob.id != agent.lastClosestHostileMob:
            closestLog = "closest_hostile_mob-{}-{}".format(agentId, mob.id)
            Logger.__pushStatement__(closestLog)
            didModifyCurrentState = False
            for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                if Logger.__currentState[i].startswith("closest_hostile_mob-{}".format(agentId)):
                    Logger.__currentState[i] = closestLog
                    didModifyCurrentState = True
                    break
            if not didModifyCurrentState:
                Logger.__currentState.append(closestLog)

    @staticmethod
    def logClosestFoodMob(agent, mob):
        """
        Log the closest food mob to the agent given.
        """
        agentId = agent.getId()

        # Special case, where there is no closest food mob
        if mob == None:
            if "None" != agent.lastClosestFoodMob:
                closestLog = "closest_food_mob-{}-None".format(agentId)
                Logger.__pushStatement__(closestLog)
                didModifyCurrentState = False
                for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                    if Logger.__currentState[i].startswith("closest_food_mob-{}".format(agentId)):
                        Logger.__currentState[i] = closestLog
                        didModifyCurrentState = True
                        break
                if not didModifyCurrentState:
                    Logger.__currentState.append(closestLog)
            return

        if not isMob(mob.type):
            return
        
        # This might be an entity not previously declared in the log. Log its definition if so.
        Logger.logMobDefinition(mob)

        if mob.id != agent.lastClosestFoodMob:
            closestLog = "closest_food_mob-{}-{}".format(agentId, mob.id)
            Logger.__pushStatement__(closestLog)
            didModifyCurrentState = False
            for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                if Logger.__currentState[i].startswith("closest_food_mob-{}".format(agentId)):
                    Logger.__currentState[i] = closestLog
                    didModifyCurrentState = True
                    break
            if not didModifyCurrentState:
                Logger.__currentState.append(closestLog)

    @staticmethod
    def logClosestFoodItem(agent, item):
        """
        Log the closest food item to the agent given.
        """
        agentId = agent.getId()

        # Special case, where there is no closest food item
        if item == None:
            if "None" != agent.lastClosestFoodItem:
                closestLog = "closest_food_item-{}-None".format(agentId)
                Logger.__pushStatement__(closestLog)
                didModifyCurrentState = False
                for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                    if Logger.__currentState[i].startswith("closest_food_item-{}".format(agentId)):
                        Logger.__currentState[i] = closestLog
                        didModifyCurrentState = True
                        break
                if not didModifyCurrentState:
                    Logger.__currentState.append(closestLog)
            return

        if not isFoodItem(item.type):
            return

        # This might be an entity not previously declared in the log. Log its definition if so.
        Logger.logItemDefinition(item)

        if item.id != agent.lastClosestFoodItem:
            closestLog = "closest_food_item-{}-{}".format(agentId, item.id)
            Logger.__pushStatement__(closestLog)
            didModifyCurrentState = False
            for i in range(0, len(Logger.__currentState)):  # Fix-up current state
                if Logger.__currentState[i].startswith("closest_food_item-{}".format(agentId)):
                    Logger.__currentState[i] = closestLog
                    didModifyCurrentState = True
                    break
            if not didModifyCurrentState:
                Logger.__currentState.append(closestLog)

    __lastLookAtDidFinish = False   # Keep track of whether or not lookAt has finished to log post-conditions ONCE

    __lastMoveToDidFinish = False   # Keep track of whether or not moveTo has finished to log post-conditions ONCE
        

    __lastAttack = None     # Keep track of the last entity we attacked to avoid unnecessary repeat logs

    @staticmethod
    def logAttack(agent, entity, didKill):
        """
        Log the preconditions, action, and possible postconditions for the Attack command.
        """
        agentId = agent.getId()
        Logger.__pushNewline__()

        # Preconditions
        Logger.__pushStatement__("looking_at-{}-{}".format(agentId, entity.id))
        Logger.__pushStatement__("at-{}-{}".format(agentId, entity.id))

        # Action
        Logger.__pushStatement__("!ATTACK-{}-{}".format(agentId, entity.id))

        # Postconditions
        if didKill:
            Logger.logEntityIsAlive(entity, False)

            # Sleep to give time for item to appear in inventory if one was immediately picked up
            time.sleep(0.5)
            
            # If we did immediately pick up an item, log the item definitions as postconditions of the attack, and then fake a call to PickUpItem
            newItems, _ = agent.inventory.update()
            if len(newItems) > 0:
                for item in newItems:
                    Logger.logItemDefinition(item)
                    Logger.__pushStatement__("at-{}-None".format(item.id))
                for item in newItems:
                    Logger.logPickUpItem(agent, item)
            # If we did NOT pick up an item, there are probably one or more lying closeby... define any items lying on the ground as post-conditions
            else:
                nearbyItems = agent.getAllNearbyItems()
                for item in nearbyItems:
                    newItem = Item("{}{}".format(item.type, agent.inventory.getId()), item.type)
                    if not Logger.isEntityDefined(newItem):
                        AgentInventory.enqueueItem(newItem)    # We will most likely be picking up the item and so we will queue up the id to preserve it
                        for i in range(0, item.quantity):      # Items from a JSON observation have a stack quantity
                            Logger.logItemDefinition(newItem)
                            Logger.__pushStatement__("at-{}-None".format(item.id))
                            AgentInventory.enqueueItem(newItem)
                            if i < item.quantity - 1:
                                newItem = Item("{}{}".format(item.type, agent.inventory.getId()), item.type)
    
        Logger.__pushNewline__()
