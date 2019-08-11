import os
import time
from enum import Enum
from datetime import datetime
from malmoext.Utils import Mobs, Items, LogUtils
from malmoext.Agent import Agent

class Logger:
    '''
    Produces state and action information for agents operating in a mission.
    The results can be output to a file at the end of the mission.
    '''
    def __init__(self):
        self.__log = []                         # The log contents, split by line
        self.__currentState = Logger.State()    # Representation of the current state
        self.__logFlags = {}                    # A map of agent IDs to the logging flags for each agent

    def setLoggingLevel(self, agent, *flags):
        '''
        Set the logging level for an agent by providing any number of Logger.Flags. Normal logging
        will be applied to all agents where no flags were specified.
        '''
        self.__logFlags[agent.id] = Logger.Flags.Normal.value
        for flag in flags:
            self.__logFlags[agent.id] |= flag.value

    def __hasLoggingLevel(self, agent, flag):
        '''
        Returns true if the given bitmask was set as the logging level for a particular agent.
        '''
        return (self.__logFlags[agent.id] & flag.value) != 0

    def clear(self):
        '''
        Clear the log of all its contents.
        '''
        self.__log = []

    def __appendLine(self, line):
        '''
        Add a new statement onto the log.
        '''
        self.__log.append(line)

    def __appendNewline(self):
        '''
        Add a blank line onto the log. If the previous line was already a blank line, this method
        has no effect.
        '''
        length = len(self.__log)
        if length == 0:
            return
        if self.__log[length - 1] != "":
            self.__log.append("")

    def start(self):
        '''
        Starts up the logger by logging the initial state. This method should only be called once, after any
        preliminary settings to the logger are set and the mission is started.
        '''
        # Log out a special NoneType entity that we use as a placeholder for things not yet set
        self.__appendLine("none-None-NoneType")

        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            # Make sure logging flags have been set for this agent
            if (agent.id not in self.__logFlags):
                self.__logFlags[agent.id] = Logger.Flags.Normal.value

            # Define agent
            self.__logAgent(agent)
            agentMetadata = self.__currentState.agents[agent.id]

            # Log where agent is looking (initially None)
            self.__appendLine("looking_at-{}-None".format(agent.id))

            # Log where agent is at (initially None)
            self.__appendLine("at-{}-None".format(agent.id))
            
            # Agent inventory
            agent.inventory.sync()
            agentMetadata.inventory = agent.inventory.asMap()
            inventoryItems = agent.inventory.asList()
            for item in inventoryItems:
                self.__logItem(item)
                self.__appendLine("at-{}-{}".format(item.id, agent.id))
            equippedItem = agent.inventory.equippedItem()
            equippedID = equippedItem.id if equippedItem != None else "None"
            self.__appendLine("equipped_item-{}-{}".format(agent.id, equippedID))
            agentMetadata.equippedItem = equippedItem

            # Nearby entities to this agent
            self.__logEntities(agent.nearbyEntities())

            # Log closest mobs
            agentMetadata.closestMob[Mobs.All] = agent.closestMob()
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.All])
            agentMetadata.closestMob[Mobs.Peaceful] = agent.closestMob(Mobs.Peaceful)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Peaceful], Mobs.Peaceful)
            agentMetadata.closestMob[Mobs.Hostile] = agent.closestMob(Mobs.Hostile)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Hostile], Mobs.Hostile)
            agentMetadata.closestMob[Mobs.Food] = agent.closestMob(Mobs.Food)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Food], Mobs.Food)

            # Log closest items
            agentMetadata.closestItem[Items.All] = agent.closestItem()
            self.__logClosestItem(agent, agentMetadata.closestItem[Items.All])
            agentMetadata.closestItem[Items.Food] = agent.closestItem(Items.Food)
            self.__logClosestItem(agent, agentMetadata.closestItem[Items.Food], Items.Food)

            # Add agent metadata to the current state
            self.__currentState.agents[agent.id] = agentMetadata
        
        # Log start symbol
        self.__appendLine("START")
        self.__appendNewline()

    def stop(self):
        '''
        Shuts down the logger by logging the final state. This method should only be called once,
        after the mission has ended.
        '''
        
        self.__appendNewline()
        self.__appendLine("END")

        allAgents = list(Agent.allAgents.values())
        allItems = list(self.__currentState.items.values())
        allMobs = list(self.__currentState.mobs.values())
        allItemsInInventory = {}

        # Re-define all mobs
        for mob in allMobs:
            self.__logMob(mob, True)

        # Re-define all items
        for item in allItems:
            self.__logItem(item, True)

        for agent in allAgents:
            agentMetadata = self.__currentState.agents[agent.id]

            # Re-define agent
            self.__logAgent(agent, True)

            # Log where agent is looking (from metadata)
            self.__appendLine("looking_at-{}-{}".format(agent.id, agentMetadata.lookingAt.id if agentMetadata.lookingAt != None else "None"))

            # Log where the agent is at (from metadata)
            self.__appendLine("at-{}-{}".format(agent.id, agentMetadata.at.id if agentMetadata.at != None else "None"))

            # Log agent inventory (from metadata)
            for item in list(agentMetadata.inventory.values()):
                allItemsInInventory[item.id] = item
                self.__appendLine("at-{}-{}".format(item.id, agent.id))
            equippedItem = agentMetadata.equippedItem
            equippedId = equippedItem.id if equippedItem != None else "None"
            self.__appendLine("equipped_item-{}-{}".format(agent.id, equippedId))

            # Log closest mobs (from metadata)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.All])
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Peaceful], Mobs.Peaceful)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Hostile], Mobs.Hostile)
            self.__logClosestMob(agent, agentMetadata.closestMob[Mobs.Food], Mobs.Food)

            # Log closest items (from metadata)
            self.__logClosestItem(agent, agentMetadata.closestItem[Items.All])
            self.__logClosestItem(agent, agentMetadata.closestItem[Items.Food], Items.Food)

        # For any items that were not a part of an agent's inventory, log their location as 'None'
        for item in allItems:
            if item.id not in allItemsInInventory:
                self.__appendLine("at-{}-None".format(item.id))

    def __logIsAlive(self, entity, isAlive, force=False):
        '''
        Log that the given entity is either alive or dead. If the entity was already declared as such, this method
        has no effect unless the force argument is set to True.
        '''
        entityId = entity.id
        if isAlive:
            if force or entityId not in self.__currentState.alive:
                self.__appendLine("status-{}-alive".format(entityId))
                self.__currentState.alive.add(entityId)
                self.__currentState.dead.discard(entityId)
        else:
            if force or entityId not in self.__currentState.dead:
                self.__appendLine("status-{}-dead".format(entityId))
                self.__currentState.dead.add(entityId)
                self.__currentState.alive.discard(entityId)

    def __logAgent(self, agent, force=False):
        '''
        Define a new agent in the log. If the agent was previously defined, this method has no
        effect unless the force argument is set to True.
        '''
        if not force and agent.id in self.__currentState.agents:
            return

        # Add to log
        self.__appendLine("agents-{}-Agent".format(agent.id))
        isAlive = agent.isAlive()
        self.__logIsAlive(agent, isAlive, force)
        
        # Update current state
        self.__currentState.agents[agent.id] = Logger.AgentMetadata()
        if isAlive:
            self.__currentState.alive.add(agent.id)
        else:
            self.__currentState.dead.add(agent.id)

    def __logMob(self, mob, force=False):
        '''
        Define a new mob in the log. If the mob was previously defined, this method has no
        effect unless the force argument is set to True.
        '''
        if not force and mob.id in self.__currentState.mobs.keys():
            return

        # Add to log
        self.__appendLine("mobs-{}-{}".format(mob.id, mob.type))
        isAlive = True if mob.id not in self.__currentState.dead else False
        self.__logIsAlive(mob, isAlive, force)

        # Update current state
        self.__currentState.mobs[mob.id] = mob
        if isAlive:
            self.__currentState.alive.add(mob.id)
        else:
            self.__currentState.dead.add(mob.id)

    def __logItem(self, item, force=False):
        '''
        Define a new item in the log. If the item was previously defined, this method has no
        effect unless the force argument is set to True.
        '''
        if not force and item.id in self.__currentState.items.keys():
            return
        
        # Add to log
        self.__appendLine("items-{}-{}".format(item.id, item.type))
        
        # Update current state
        self.__currentState.items[item.id] = item

    def __logEntity(self, entity, force=False):
        '''
        Define a new entity in the log. If the entity was previously defined, this method has no
        effect unless the force argument is set to True.
        '''
        if isinstance(entity, Agent):
            self.__logAgent(entity, force)
        elif Mobs.All.isMember(entity.type):
            self.__logMob(entity, force)
        elif Items.All.isMember(entity.type):
            self.__logItem(entity, force)

    def __logEntities(self, entities, force=False):
        '''
        For each entity in the list provided, define it as a new entity in the log if it has not
        been already. If the force argument is set to True, define the entity regardless.
        '''
        for entity in entities:
            self.__logEntity(entity, force)

    def __logClosestMob(self, agent, mob, variant=Mobs.All):
        '''
        Log the closest mob to an agent. Optionally specify additional modifiers for what type of
        mob it is. 
        '''
        if variant == Mobs.All:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestMob_Any):
                return
            prefix = "closest_mob-"
        elif variant == Mobs.Peaceful:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestMob_Peaceful):
                return
            prefix = "closest_peaceful_mob-"
        elif variant == Mobs.Hostile:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestMob_Hostile):
                return
            prefix = "closest_hostile_mob-"
        elif variant == Mobs.Food:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestItem_Food):
                return
            prefix = "closest_food_mob-"
        else:
            raise Exception("Closest mob variant must be an enumerated type")

        mobID = mob.id if mob != None else "None"
        self.__appendLine("{}{}-{}".format(prefix, agent.id, mobID))

    def __logClosestItem(self, agent, item, variant=Items.All):
        '''
        Log the closest item to an agent. Optionally specify additional modifiers for what type of
        item it is.
        '''
        if variant == Items.All:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestItem_Any):
                return
            prefix = "closest_item-"
        elif variant == Items.Food:
            if not self.__hasLoggingLevel(agent, Logger.Flags.ClosestItem_Food):
                return
            prefix = "closest_food_item-"
        else:
            raise Exception("Closest item variant must be an enumerated type")

        itemID = item.id if item != None else "None"
        self.__appendLine("{}{}-{}".format(prefix, agent.id, itemID))

    def __logLookAt(self, agent, fromEntity, toEntity):
        '''
        Log the preconditions, action, and postconditions for an agent looking from a previous entity
        to a new entity.
        '''
        self.__appendNewline()
        fromID = fromEntity.id if fromEntity != None else "None"
        toID = toEntity.id if toEntity != None else "None"

        # Preconditions - None

        # Action
        self.__appendLine("!LOOKAT-{}-{}-{}".format(agent.id, fromID, toID))

        # Postconditions
        self.__appendLine("looking_at-{}-{}".format(agent.id, toID))

    def __logMoveTo(self, agent, fromEntity, toEntity):
        '''
        Log the preconditions, action, and postconditions for an agent moving from a previous entity
        to a new entity.
        '''
        self.__appendNewline()
        fromID = fromEntity.id if fromEntity != None else "None"
        toID = toEntity.id if toEntity != None else "None"

        # Preconditions
        self.__appendLine("looking_at-{}-{}".format(agent.id, toID))

        # Action
        self.__appendLine("!MOVETO-{}-{}-{}".format(agent.id, fromID, toID))

        # Postconditions
        self.__appendLine("at-{}-{}".format(agent.id, toID))

    def __logPickUpItem(self, agent, item):
        '''
        Log the preconditions, action, and postconditions for an agent having picked up an item from the ground.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("at-{}-None".format(item.id))

        # Action
        self.__appendLine("!PICKUPITEM-{}-{}".format(agent.id, item.id))

        # Postconditions
        self.__appendLine("at-{}-{}".format(item.id, agent.id))

    def __logAttack(self, agent, mob, wasKilled, itemsDropped, itemsPickedUp):
        '''
        Log the preconditions, action, and postconditions for an agent attacking (and possibly
        killing) a mob.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("looking_at-{}-{}".format(agent.id, mob.id))
        self.__appendLine("at-{}-{}".format(agent.id, mob.id))

        # Action
        self.__appendLine("!ATTACK-{}-{}".format(agent.id, mob.id))

        # Postconditions
        if wasKilled:
            self.__logIsAlive(mob, False)
            for item in itemsDropped:
                self.__logItem(item)
                self.__appendLine("at-{}-None".format(item.id))
            for item in itemsPickedUp:
                self.__logItem(item)
                self.__appendLine("at-{}-{}".format(item.id, agent.id))

    def __logCraft(self, agent, itemCrafted, itemsUsed):
        '''
        Log the preconditions, action, and postconditions for an agent having crafted an item.
        '''
        self.__appendNewline()

        # Preconditions
        for item in itemsUsed:
            self.__appendLine("at-{}-{}".format(item.id, agent.id))

        # Action
        self.__appendLine("!CRAFT-{}-{}".format(agent.id, itemCrafted.id))

        # Postconditions
        self.__logItem(itemCrafted)
        self.__appendLine("at-{}-{}".format(itemCrafted.id, agent.id))
        for item in itemsUsed:
            self.__appendLine("at-{}-None".format(item.id))

    def __logEquipItem(self, agent, item):
        '''
        Log the preconditions, action, and postconditions of an agent equipping an item from its inventory.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("at-{}-{}".format(item.id, agent.id))

        # Action
        self.__appendLine("!EQUIP-{}-{}".format(agent.id, item.id))

        # Postconditions
        self.__appendLine("equipped_item-{}-{}".format(agent.id, item.id))

    def __logGiveItem(self, fromAgent, item, toAgent):
        '''
        Log the preconditions, action, and postconditions of an agent giving an item to another agent.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("looking_at-{}-{}".format(fromAgent.id, toAgent.id))
        self.__appendLine("at-{}-{}".format(fromAgent.id, toAgent.id))
        self.__appendLine("at-{}-{}".format(item.id, fromAgent.id))
        self.__appendLine("equipped_item-{}-{}".format(fromAgent.id, item.id))

        # Action
        self.__appendLine("!GIVEITEM-{}-{}-{}".format(fromAgent.id, item.id, toAgent.id))

        # Postconditions
        self.__appendLine("equipped_item-{}-None".format(fromAgent.id))
        self.__appendLine("at-{}-{}".format(item.id, toAgent.id))

    def __handleClosestMobReport(self, agent, logReport):
        '''
        Handle a ClosestMobReport from an agent.
        '''
        oldClosest = self.__currentState.agents[agent.id].closestMob[logReport.variant]
        oldClosestID = oldClosest.id if oldClosest != None else None
        newClosestID = logReport.mob.id if logReport.mob != None else None
        if newClosestID != oldClosestID:
            self.__logClosestMob(agent, logReport.mob, logReport.variant)
            self.__currentState.agents[agent.id].closestMob[logReport.variant] = logReport.mob

    def __handleClosestItemReport(self, agent, logReport):
        '''
        Handle a ClosestItemReport from an agent.
        '''
        oldClosest = self.__currentState.agents[agent.id].closestItem[logReport.variant]
        oldClosestID = oldClosest.id if oldClosest != None else None
        newClosestID = logReport.item.id if logReport.item != None else None
        if newClosestID != oldClosestID:
            self.__logClosestItem(agent, logReport.item, logReport.variant)
            self.__currentState.agents[agent.id].closestItem[logReport.variant] = logReport.item

    def __handleLookAtReport(self, agent, logReport):
        '''
        Handle a LookAtReport from an agent.
        '''
        oldLookAt = self.__currentState.agents[agent.id].lookingAt
        oldLookAtID = oldLookAt.id if oldLookAt != None else None
        newLookAtID = logReport.entity.id if logReport.entity != None else None
        if newLookAtID != oldLookAtID:
            self.__logLookAt(agent, oldLookAt, logReport.entity)
            self.__currentState.agents[agent.id].lookingAt = logReport.entity

    def __handleMoveToReport(self, agent, logReport):
        '''
        Handle a MoveToReport from an agent.
        '''
        oldMoveTo = self.__currentState.agents[agent.id].at
        oldMoveToID = oldMoveTo.id if oldMoveTo != None else None
        newMoveToID = logReport.entity.id if logReport.entity != None else None
        if newMoveToID != oldMoveToID:
            self.__logMoveTo(agent, oldMoveTo, logReport.entity)
            self.__currentState.agents[agent.id].at = logReport.entity

    def __handlePickUpItemReport(self, agent, logReport):
        '''
        Handle a PickUpItemReport from an agent.
        '''
        if logReport.item.id not in self.__currentState.agents[agent.id].inventory:
            self.__logPickUpItem(agent, logReport.item)
            self.__currentState.agents[agent.id].inventory[logReport.item.id] = logReport.item

    def __handleCraftReport(self, agent, logReport):
        '''
        Handle a CraftReport from an agent.
        '''
        self.__logCraft(agent, logReport.itemCrafted, logReport.itemsUsed)
        self.__currentState.agents[agent.id].inventory[logReport.itemCrafted.id] = logReport.itemCrafted
        for itemUsed in logReport.itemsUsed:
            self.__currentState.agents[agent.id].inventory.pop(logReport.itemUsed.id, None)

    def __handleAttackReport(self, agent, logReport):
        '''
        Handle an AttackReport from an agent.
        '''
        self.__logAttack(agent, logReport.mob, logReport.didKill, logReport.itemsDropped, logReport.itemsPickedUp)
        for itemDropped in logReport.itemsDropped:
            self.__currentState.items[itemDropped.id] = itemDropped
        for itemPickup in logReport.itemsPickedUp:
            self.__currentState.items[itemPickup.id] = itemPickup
            self.__currentState.agents[agent.id].inventory[itemPickup.id] = itemPickup

    def __handleEquipReport(self, agent, logReport):
        '''
        Handle an EquipReport from an agent.
        '''
        oldEquipped = self.__currentState.agents[agent.id].equippedItem
        oldEquippedID = oldEquipped.id if oldEquipped != None else None
        newEquippedID = logReport.item.id if logReport.item != None else None
        if newEquippedID != oldEquippedID:
            self.__logEquipItem(agent, logReport.item)
            self.__currentState.agents[agent.id].equippedItem = logReport.item

    def __handleGiveItemReport(self, agent, logReport):
        '''
        Handle a GiveItemReport from an agent.
        '''
        self.__logGiveItem(agent, logReport.item, logReport.agent)
        self.__currentState.agents[agent.id].equippedItem = None
        self.__currentState.agents[agent.id].inventory.pop(logReport.item.id, None)
        self.__currentState.agents[logReport.agent.id].inventory[logReport.item.id] = logReport.item

    def __handleAgentLogReports(self, agent):
        '''
        Produce a log for any agent log reports that are not repeats from the last iteration.
        '''
        logReports = agent.getAndClearLogReports()
        for logReport in logReports:
            logReportType = type(logReport).__name__
            if logReportType == "ClosestMobReport":
                self.__handleClosestMobReport(agent, logReport)
            elif logReportType == "ClosestItemReport":
                self.__handleClosestItemReport(agent, logReport)
            elif logReportType == "LookAtReport":
                self.__handleLookAtReport(agent, logReport)
            elif logReportType == "MoveToReport":
                self.__handleMoveToReport(agent, logReport)
            elif logReportType == "PickUpItemReport":
                self.__handlePickUpItemReport(agent, logReport)
            elif logReportType == "CraftReport":
                self.__handleCraftReport(agent, logReport)
            elif logReportType == "AttackReport":
                self.__handleAttackReport(agent, logReport)
            elif logReportType == "EquipReport":
                self.__handleEquipReport(agent, logReport)
            elif logReportType == "GiveItemReport":
                self.__handleGiveItemReport(agent, logReport)
            else:
                raise Exception("Unhandled log report type: {}".format(logReportType))

    def update(self):
        '''
        Produce logs for all agents where changes/actions have occurred. This function should be called at the
        beginning of each mission loop iteration.
        '''
        for agent in list(Agent.allAgents.values()):
            self.__handleAgentLogReports(agent)

    def export(self):
        '''
        Output the log contents to a file in a 'logs' directory. The file is named with the
        current timestamp.
        '''
        directory = "logs"
        if not os.path.isdir(directory):
            os.mkdir(directory)

        filename = datetime.fromtimestamp(time.time()).strftime("%m_%d_%Y_%H_%M_%S") + ".log"
        filepath = os.path.join(directory, filename)
        with open(filepath, "w+") as f:
            f.write("\n".join(self.__log))
        print("Mission log output has been saved to: " + filepath)

    class State:
        '''
        Internal logger representation of any instantaneous state of the mission.
        '''
        def __init__(self):
            self.agents = {}        # A map of previously defined agent IDs to agent metadata
            self.mobs = {}          # A map of all previously defined mob IDs to mob objects
            self.items = {}         # A map of all previously defined item IDs to item objects
            self.alive = set()      # A set of agent and mob IDs that are currently alive
            self.dead = set()       # A set of agent and mob IDs that are currently dead

    class AgentMetadata:
        '''
        Internal logger representation of an Agent at any instantaneous state of the mission.
        Used as a cache by the logger to determine if log records produced by an agent actually represent
        a change in state.
        '''
        def __init__(self):
            self.lookingAt = None                                  # The ID of the entity that the agent is looking at
            self.at = None                                         # The ID of the entity that the agent is at
            self.equippedItem = None                               # The ID of the item that the agent has equipped
            self.closestMob = {}                                   # A map of mob types to the closest mob of each type to the agent
            self.closestItem = {}                                  # A map of item types to the closest item of each type to the agent
            self.inventory = {}                                    # A map of item IDs to items in the agent's inventory

    class Flags(Enum):
        '''
        Enumerated type for specifying additional logging output for each agent.
        '''
        Normal              = 0x0
        ClosestMob_Any      = 0x2
        ClosestMob_Peaceful = 0x4
        ClosestMob_Hostile  = 0x8
        ClosestMob_Food     = 0x10
        ClosestItem_Any     = 0x20
        ClosestItem_Food    = 0x40
