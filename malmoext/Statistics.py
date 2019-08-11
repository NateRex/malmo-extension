import time
from datetime import datetime
import pandas
import matplotlib.pyplot as plt
import sys
import os
import random
from malmoext.Agent import Agent
from malmoext.Utils import AgentType

# ===========================================================================================================
# FUNCTIONALITY FOR USING THIS FILE AS A MODULE (for generating new data)
# ===========================================================================================================

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

    def setItemTracking(self, itemType):
        '''
        Specify a type of item to be tracked (in quantity) across agent inventories.
        '''
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





# ===========================================================================================================
# FUNCTIONALITY FOR RUNNING THIS FILE AS A SCRIPT (for interpreting past data)
# ===========================================================================================================

def __getCSVFiles__():
    """
    Repeatedly asks the user to input the name of a performance CSV file in the performance directory, until the empty string is received.
    Returns the list of csv filenames.
    """
    filenames = []
    shouldGetInput = True
    while shouldGetInput:
        filename = input("Enter CSV file name: ")
        if len(filename) == 0:
            shouldGetInput = False
        else:
            filepath = os.path.join("performance", filename)
            if os.path.isfile(filepath):
                filenames.append(filename)
            else:
                print("'{}' could not be found.".format(filepath))
    return filenames

def __getGraphAttributes__(dataframe):
    """
    Gets all available attributes from a sample dataframe, then repeatedly collects attributes to plot from the user until an empty string is received.
    Returns the list of attributes.
    """
    print("Plottable Attributes ==============================")
    for col in dataframe.columns:
        print("- " + col)
    print("===================================================\n")
    
    attributes = []
    shouldGetInput = True
    while shouldGetInput:
        attribute = input("Attribute: ")
        if len(attribute) == 0:
            shouldGetInput = False
        else:
            attributes.append(attribute)
    return attributes

def main():
    """
    Main method allowing this file to be ran as a script for nicely outputting statistical data from a csv file in
    various forms.
    """
    filenames = __getCSVFiles__()
    if len(filenames) == 0:
        print("No CSV files entered")
        return

    # These have a 1:1 mapping to the filepaths gathered above
    agentIds = []
    agentData = []
    for filepath in filenames:
        agentIds.append(filepath.split("_")[0])
        agentData.append(pandas.read_csv(os.path.join("performance", filepath)))

    # Collect the attributes of interest in each AgentData object
    attributes = __getGraphAttributes__(agentData[0])

    # Plot each attribute against SysTime
    fig = plt.figure()
    fig.canvas.set_window_title("Agent Statistics Over Time")
    for i in range(len(agentIds)):
        for attribute in attributes:
            r = random.random()
            g = random.random()
            b = random.random()
            plt.plot(agentData[i]["SysTime"], agentData[i][attribute], markeredgecolor=(r, g, b, 1), linestyle="solid", label="{} {}".format(agentIds[i], attribute))

    # Show the plot on-screen
    plt.legend(loc="best")
    plt.xlabel("Time")
    plt.ylabel("Amount")
    plt.show()


if __name__ == "__main__":
    main()