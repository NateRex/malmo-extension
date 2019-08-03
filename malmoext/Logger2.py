from datetime import datetime
import os
import time

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

    def __logNewAgent(self, agent):
        '''
        Define a new agent in the log. If the agent was previously defined, this method has no
        effect.
        '''
        agentId = agent.id
        if agentId in self.__currentState.agents:
            return

        self.__appendLine("agents-{}-{}".format(agentId, agentId[:-1]))
        self.__logIsAlive(agent, agent.isAlive())
        self.__currentState.agents[agentId] = agent.getMetadata()
        self.__currentState.alive.add(agentId)

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

