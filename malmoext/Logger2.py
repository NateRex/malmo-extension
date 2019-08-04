import os
import time
from datetime import datetime
from malmoext.Utils import Mobs, Items
from malmoext.Agent import Agent

class Logger:
    '''
    Singleton class that produces state and action information for agents operating in a mission.
    The results are output to a file at the end of the mission.
    '''
    __instance  = None

    @staticmethod
    def getInstance():
        '''
        Return the global instance of the Logger class.
        '''
        if Logger.__instance == None:
            Logger()
        return Logger.__instance

    def __init__(self):
        if Logger.__instance != None:
            raise Exception('Attempt to create second instance of Logger')
        Logger.__instance = self
        
        self.__log = []                  # The log contents, split by line
        self.__currentState = State()    # Representation of the current state

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

    def __logInitialState(self):
        '''
        Log the starting state of the mission.
        '''
        print("TODO")

    def __logFinalState(self):
        '''
        Log the final state of the mission
        '''
        print("TODO")

    def __logIsAlive(self, entity, isAlive):
        '''
        Log that the given entity is either alive or dead.
        '''
        entityId = entity.id
        if isAlive:
            if entityId not in self.__currentState.alive:
                self.__appendLine("status-{}-alive".format(entityId))
                self.__currentState.alive.add(entityId)
                self.__currentState.dead.discard(entityId)
        else:
            if entityId not in self.__currentState.dead:
                self.__appendLine("status-{}-dead".format(entityId))
                self.__currentState.dead.add(entityId)
                self.__currentState.dead.discard(entityId)

    def __logAgent(self, agent):
        '''
        Define a new agent in the log. If the agent was previously defined, this method has no
        effect.
        '''
        agentId = agent.id
        if agent.id in self.__currentState.agents:
            return

        # Add to log
        self.__appendLine("agents-{}-{}".format(agentId, agentId[:-1]))
        self.__logIsAlive(agent, agent.isAlive())
        
        # Update current state
        self.__currentState.agents[agentId] = agent.metadata
        self.__currentState.alive.add(agentId)

    def __logMob(self, mob):
        '''
        Define a new mob in the log. If the mob was previously defined, this method has no
        effect.
        '''
        mobId = mob.id
        if mobId in self.__currentState.mobs:
            return

        # Add to log
        self.__appendLine("mobs-{}-{}".format(mobId, mob.type))
        self.__logIsAlive(mob, True)    # assume is alive

        # Update current state
        self.__currentState.mobs.add(mobId)
        self.__currentState.alive.add(mobId)

    def __logItem(self, item):
        '''
        Define a new item in the log. If the item was previously defined, this method has no
        effect.
        '''
        itemId = item.id
        if itemId in self.__currentState.items:
            return
        
        # Add to log
        self.__appendLine("items-{}-{}".format(itemId, item.type))
        
        # Update current state
        self.__currentState.items.add(itemId)

    def __logEntity(self, entity):
        '''
        Define a new entity in the log. If the entity was previously defined, this method has no
        effect.
        '''
        if isinstance(entity, Agent):
            self.__lognewAgent(entity)
        elif Mobs.isMob(entity.type):
            self.__logMob(entity)
        elif Items.isItem(entity.type):
            self.__logItem(entity)

    def __logEntities(self, *entities):
        '''
        For each entity in the list provided, define it as a new entity in the log if it has not
        been already.
        '''
        for entity in entities:
            self.__logEntity(entity)

    def __logClosestMob(self, agent, mob, variant=""):
        '''
        Log the closest mob to an agent. Optionally specify additional modifiers for what type of
        mob it is. 
        '''
        print("TODO")

    def __logClosestItem(self, agent, item, variant=""):
        '''
        Log the closest item to an agent. Optionally specify additional modifiers for what type of
        item it is.
        '''
        print("TODO")

    def __logLookAt(self, agent, fromEntity, toEntity):
        '''
        Log the preconditions, action, and postconditions for an agent looking from a previous entity
        to a new entity.
        '''
        self.__appendNewline()

        # Preconditions - None

        # Action
        self.__appendLine("!LOOKAT-{}-{}-{}".format(agent.id, fromEntity.id, toEntity.id))

        # Postconditions
        self.__appendLine("looking_at-{}-{}".format(agent.id, toEntity.id))

    def __logMoveTo(self, agent, fromEntity, toEntity):
        '''
        Log the preconditions, action, and postconditions for an agent moving from a previous entity
        to a new entity.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("looking_at-{}-{}".format(agent.id, toEntity.id))

        # Action
        self.__appendLine("!MOVETO-{}-{}-{}".format(agent.id, fromEntity.id, toEntity.id))

        # Postconditions
        self.__appendLine("at-{}-{}".format(agent.id, toEntity.id))

    def __logAttack(self, agent, mob, wasKilled):
        '''
        Log the preconditions, action, and postconditions for an agent attacking (and possibly
        killing) a mob.
        '''
        print("TODO")

    def __logPickUpItem(self, agent, item):
        '''
        Log the preconditions, action, and postconditions of an agent going to pick up a nearby item.
        '''
        self.__appendNewline()

        # Preconditions
        self.__appendLine("at-{}-None".format(item.id))

        # Action
        self.__appendLine("!PICKUPITEM-{}-{}".format(agent.id, item.id))

        # Postconditions
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

    def exportToFile(self):
        '''
        Output the log contents to a file in the 'logs' directory. The file is named with the
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
            self.agents = {}     # A map of previously defined agent IDs to agent metadata
            self.mobs = set()    # A set of all previously defined mob IDs
            self.items = set()   # A set of all previously defined item IDs
            self.alive = set()   # A set of agent and mob IDs that are currently alive
            self.dead = set()    # A set of agent and mob IDs that are currently dead

    class Flags(Enum):
        '''
        Enumerated type for specifying additional output for each agent.
        '''
        ClosestMob          = 0x1
        ClosestPeacefulMob  = 0x2
        ClosestHostileMob   = 0x4
        ClosestFoodMob      = 0x8
        ClosestFoodItem     = 0x10
        Inventory           = 0x20

