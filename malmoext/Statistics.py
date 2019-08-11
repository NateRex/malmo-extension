import time
from datetime import datetime
import pandas
import sys
import os
import random
from malmoext.Agent import Agent
from malmoext.Utils import AgentType

class Statistics:
    """
    Produces statistical information for each agent over the course of a mission. Results can be output to a file at the
    end of the mission.
    """
    __updateInterval = 100            # How often agent statistics should be updated (in mission loop iterations)

    # Lists of statistic attributes to keep track of for each agent
    __defaultAttributes = ["SysTime", "DamageDealt", "MobsKilled",      # List of statistical attributes to track for each agent
        "PlayersKilled", "CurrentHealth", "HealthLost",
        "HealthGained", "IsAlive", "TimeAlive", "Hunger",
        "Score", "XP", "DistanceTravelled"]
    __trackedItems = []                                                 # List of item quantities to track for each agent

    def __init__(self):
        self.__startTime = time.time()    # The mission start time
        self.__updateCounter = 0          # Counter for determining when an update is required
        self.__updateIndex = 0            # The next row index to fill with data for all agent dataframes
        self.__stats = {}                 # A map of agent IDs to the Pandas dataframe containing each agent's data over time
        self.__metadata = {}              # A map of agent IDs to metadata for each agent used for future calculations

    def setItemTracking(self, *itemTypes):
        '''
        Specify any number of item types to be tracked across agent inventories.
        '''
        for itemType in itemTypes:
            self.__trackedItems.append(itemType.value)

    def start(self):
        '''
        Starts up the statistics generator by creating the matrix for each agent. This method should only be called once, after
        any preliminary settings to the statistics generator have been set and the mission is started.
        '''
        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            # Create a metadata object for the agent
            self.__metadata[agent.id] = Statistics.AgentMetadata()

            # Create the pandas dataframe
            self.__stats[agent.id] = pandas.DataFrame(columns= (Statistics.__defaultAttributes + Statistics.__trackedItems))

    def stop(self):
        '''
        Shuts down the statistics generator by doing post-mission cleanup on each matrix. This method should only be called once,
        after the mission has ended.
        '''
        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            # Adjust times to start at 0
            timeLabel = Statistics.__defaultAttributes[0]
            initialTime = self.__stats[agent.id].iloc[0][timeLabel]
            self.__stats[agent.id].loc[:, timeLabel] -= initialTime
    
    def __updateHealth(self, agent):
        '''
        Checks if the agent has lost or gained any health, updating the metadata and dataframe objects respectively.
        '''
        previousHealth = self.__metadata[agent.id].health
        currentHealth = agent.toJSON()["Life"]
        if currentHealth < previousHealth:
            self.__metadata[agent.id].healthLost += previousHealth - currentHealth
        elif currentHealth > previousHealth:
            self.__metadata[agent.id].healthGained += currentHealth - previousHealth
        self.__metadata[agent.id].health = currentHealth

    def update(self):
        '''
        Update the statistical data for all agents.
        '''
        # Check whether it is time for an update
        if self.__updateCounter == Statistics.__updateInterval:
            self.__updateCounter = 0
        else:
            self.__updateCounter += 1
            return

        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            # For human agents, some things are not updated automatically. Manually trigger these updates here
            if agent.type == AgentType.Human:
                agent.inventory.sync()
            
            # Update any metadata stored in this object
            self.__updateHealth(agent)

            # Create the new row in the dataframe
            json = agent.toJSON()
            metadata = self.__metadata[agent.id]
            defaultData = [
                time.time() - self.__startTime,         # Time passed since start of the mission
                json["DamageDealt"],                    # Amount of damage dealt
                json["MobsKilled"],                     # Number of mobs killed
                json["PlayersKilled"],                  # Number of players killed
                metadata.health,                        # Current health
                metadata.healthLost,                    # Total health lost over time
                metadata.healthGained,                  # Total health gained over time
                json["IsAlive"],                        # Whether or not the agent is alive
                json["TimeAlive"],                      # Total time the agent has spent alive
                json["Food"],                           # Hunger level
                json["Score"],                          # Score
                json["XP"],                             # Experience points
                json["DistanceTravelled"]               # Total distance traveled over time
            ]
            itemData = [agent.inventory.amountOfItem(item) for item in self.__trackedItems]

            # Insert the data
            self.__stats[agent.id].loc[self.__updateIndex] = defaultData + itemData
            self.__updateIndex += 1

    def export(self):
        '''
        Output the statistic contents to a file in a 'stats' directory. The file is named with the
        current timestamp.
        '''
        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            filename = agent.id + "_" + datetime.fromtimestamp(time.time()).strftime('%m_%d_%Y_%H_%M_%S') + ".csv"
            directory = "stats"
            if not os.path.isdir(directory):
                os.mkdir(directory)
            filepath = os.path.join(directory, filename)
            self.__stats[agent.id].to_csv(filepath, index=False)
            print("{} statistics have been saved to: {}".format(agent.id, filepath))

    class AgentMetadata:
        '''
        Internal statistical representation of an Agent at any instantaneous state of the mission.
        Used as a cache of data by the statistics class to perform future calculations.
        '''
        def __init__(self):
            self.health = 20.0         # Current health of the agent
            self.healthLost = 0.0      # Total amount of health lost over time
            self.healthGained = 0.0    # Total amount of health regenerated over time
