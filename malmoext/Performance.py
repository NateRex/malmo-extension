# ==============================================================================================
# This file contains methods used to record statistics on agents as they perform
# in a mission scenario.
# ==============================================================================================
import json
import math
import time
import pandas
import matplotlib.pyplot as plt
import sys
import random
from malmoext.Utils import *
from malmoext.Logger import *

# A named tuple that contains an attribute name, as well as the handler and argument list for obtaining the attribute
SpecialAttribute = namedtuple("SpecialAttribute", "name function args")

class Performance:
    """
    Static class for logging and exporting performance data of agents.
    """
    agentList = []                  # A list of all agents we are recording the performance of
    updateInterval = 100            # How often each Agent's performance should be updated
    filenameOverride = None         # An override to the suffix of the filename exported, rather than use the default timestamp
    defaultAttributes = ["SysTime", "DamageDealt", "MobsKilled", "PlayersKilled", "CurrentHealth", "HealthLost", "IsAlive", "TimeAlive", "Hunger", "Score", "XP", "DistanceTravelled"]
    specialAttributes = []          # A list of specific performance metrics for a particular mission beyond just the defaults

    def __init__(self, agent):
        self.startTime = time.time()    # The starting time that the agent came into existence
        self.agent = agent              # Store a reference to the Agent that owns this performance data (we will query for information from the agent)
        self.counter = 0                # Counter for determining when an update is required
        self.currentHealth = 20.0       # Current health (assume agent starts at full health)
        self.healthLost = 0.0           # Total amount of health lost
        self.isAlive = True             # Whether or not the agent is alive

        # A pandas dataframe storing all of the data over time in CSV format
        self.data = pandas.DataFrame(columns= (Performance.defaultAttributes + [i.name for i in Performance.specialAttributes]))
        self.dataIdx = 0

    @staticmethod
    def trackAgents(agents):
        """
        Add the given agents to the list of agents for which we are recording performance data.
        """
        for agent in agents:
            Performance.agentList.append(agent)
            agent.performance = Performance(agent)

    @staticmethod
    def update():
        """
        Update the performance data on all tracked agents.
        """
        for agent in Performance.agentList:
            agent.performance.__updateAgentPerformance__()

    @staticmethod
    def export():
        """
        Export the performance data for all tracked agents.
        """
        for agent in Performance.agentList:
            agent.performance.__exportAgentPerformance__()

    @staticmethod
    def trackItems(items):
        """
        Specify items you want to track across agent inventories.
        """
        for item in items:
            Performance.specialAttributes.append(SpecialAttribute(item.value, Performance.__trackItemHandler__, [item]))

    @staticmethod
    def __trackItemHandler__(agent, item):
        return agent.inventory.amountOfItem(item)

    def __updateAgentHealth__(self):
        """
        Checks if the agent has lost health and if so, adds to the healthLost stat. If health is gained, currentHealth is adjusted.
        If health reaches 0, agent is dead and isDead is changed to true.
        Should be checked frequently throughout an Agent's mission.
        """
        health = self.agent.getHealth()
        if health == None:
            return
        if health < self.currentHealth:
            self.healthLost += self.currentHealth - health
        if health == 0.0:
            self.isAlive = False
        self.currentHealth = health

    def __adjustSystemTimes__(self):
        """
        Adjust the system time values in the performance Dataframe to start at 0 for index 1.
        """
        timeLabel = Performance.defaultAttributes[0]
        initialTime = self.data.iloc[0][timeLabel]
        self.data.loc[:, timeLabel] -= initialTime

    def __updateAgentPerformance__(self):
        """
        Update the log of this agent's performance to contain the most recent data.
        """
        # If this agent is a human agent, there are things that are not automatically updated (such as inventory). Handle this on every update.
        if self.agent.agentType == AgentType.Human:
            self.agent.inventory.update()

        if self.counter == 100:
            self.__updateAgentHealth__()
            defaultData = [
                time.time() - self.startTime,       # Time passed since start of mission
                self.agent.getDamageDealt(),        # Amount of damage dealt
                self.agent.getMobsKilled(),         # The number of mobs this agent killed
                self.agent.getPlayersKilled(),      # The number of players this agent killed
                self.currentHealth,                 # The current health
                self.healthLost,                    # The total amount of health lost over time
                self.isAlive,                       # Whether or not this agent is alive
                self.agent.getTimeAlive(),          # The total amount of time this agent has been alive
                self.agent.getHunger(),             # The current hunger level of this agent
                self.agent.getScore(),              # The current score
                self.agent.getXP(),                 # The current experience point level
                self.agent.getDistanceTravelled()]  # The total amount of distance travelled over time
            specialData = []
            for specialAttrib in Performance.specialAttributes:
                specialData.append(specialAttrib.function(self.agent, *specialAttrib.args))
            self.data.loc[self.dataIdx] = defaultData + specialData
            self.counter = 0
            self.dataIdx += 1
        else:
            self.counter += 1

    def __exportAgentPerformance__(self):
        """
        Export all of this agent's performance data over time to a CSV file.
        """
        self.__adjustSystemTimes__()
    
        agentId = self.agent.getId()
        fileNameSuffix = Performance.filenameOverride if Performance.filenameOverride != None else datetime.fromtimestamp(time.time()).strftime('%m_%d_%Y_%H_%M_%S')
        fileName = agentId + "_" + fileNameSuffix + ".csv"
        filePath = "performance"
        if not os.path.isdir(filePath):
            os.mkdir(filePath)

        filePath = os.path.join(filePath, fileName)
        self.data.to_csv(filePath, index=False)
        print("{} performance output has been saved to: {}".format(agentId, filePath))



# ===========================================================================================================
# Standalone Functions for Interpreting Previously Recorded Data
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