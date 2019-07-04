# ==============================================================================================
# This file contains wrapper classes and functionality relating to a Malmo agent. This combines
# several primitive commands into larger commands that can be used to acheive more complex tasks.
# Logging is also handled automatically for each command that creates a corresponding trace.
# ==============================================================================================
import MalmoPython
import json
import math
import time
from Utils import *
from Logger import *
from AgentInventory import *

class Agent:
    """
    Wrapper class for a Malmo agent for executing complex commands with corresponding logging.
    To access the Malmo AgentHost object, use the 'host' member.
    """
    agentList = []  # A list of all agents that have been created

    def __init__(self, name, agentType):
        self.host = MalmoPython.AgentHost()     # A reference to a Malmo AgentHost object
        self.agentType = agentType              # The AgentType for this agent
        self.inventory = AgentInventory(self)   # This agent's inventory
        self.performance = None                 # This agent's performance data (not collected unless this agent is manually passed to the Performance class)
        self.id = "{}1".format(name)            # The ID of this agent
        self.actionOverride = None              # An function pointer that, if present, is ran instead of any called actions
        Agent.agentList.append(self)            # Add this agent to the global list of all agents

        # Recorded information for previous state/action observations used for checking state changes and logging
        self.lastWorldState = None
        self.lastStartedLookingAt = ""
        self.lastFinishedLookingAt = "None"
        self.lastStartedMovingTo = ""
        self.lastFinishedMovingTo = "None"
        self.lastClosestMob = ""
        self.lastClosestPeacefulMob = ""
        self.lastClosestHostileMob = ""
        self.lastClosestFoodMob = ""
        self.lastClosestFoodItem = ""
        self.lastEquippedItem = "None"
        self.lastItemAmount = 0

    @staticmethod
    def findAgentById(agentId):
        """
        Searches through the list of agents that have been created, and returns an agent with the id given.
        If no agent exists with that id, returns None.
        """
        for agent in Agent.agentList:
            if agent.id == agentId:
                return agent
        return None

    def resetClosestEntityRecords(self):
        """
        Resets the information regarding the most recent entities found nearby.
        """
        self.lastClosestMob = ""
        self.lastClosestPeacefulMob = ""
        self.lastClosestHostileMob = ""
        self.lastClosestFoodMob = ""
        self.lastClosestFoodItem = ""

    def isMissionActive(self):
        """
        Returns true if this agent's mission is still running.
        """
        return self.host.peekWorldState().is_mission_running

    def getObservationJson(self):
        """
        Returns the entire world state containing the most recent observations as a JSON object.
        """
        agentState = self.host.getWorldState()
        if len(agentState.observations) > 0:
            self.lastWorldState = json.loads(agentState.observations[-1].text)
        return self.lastWorldState

    def getBlockGrid(self):
        """
        Returns a grid of block types surrounding this agent as a one-dimensional array. Returns None on error.
        """
        stateJson = self.getObservationJson()
        if stateJson != None:
            return stateJson.get(u'blockgrid', 0)
        else:
            return None

    def getIndex(self):
        """
        Return the index of this agent in the global list of agents.
        """
        return Agent.agentList.index(self)

    def getId(self):
        """
        Returns the unique identifier for this agent. Returns none if unsuccessful.
        """
        return self.id

    def getPosition(self):
        """
        Returns the Vector position of this agent.
        If no observations have occurred, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return Vector(agentState["XPos"], agentState["YPos"] + 1, agentState["ZPos"])   # Agent's head is above the agent's location

    def getDamageDealt(self):
        """
        Returns the amount of damage this agent has dealt out to other entities.
        If no observations have occurred, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["DamageDealt"]

    def getMobsKilled(self):
        """
        Returns the number of mobs this agent has killed.
        If no observations have occurred, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["MobsKilled"]

    def getPlayersKilled(self):
        """
        Returns the number of players this agent has killed.
        If no observations have occured, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["PlayersKilled"]

    def getTimeAlive(self):
        """
        Returns the time the agent has been alive for
        If no observations have occured, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["TimeAlive"]

    def getScore(self):
        """
        Returns the score of the agent.
        If no observations have occured, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["Score"]

    def getXP(self):
        """
        Returns the xp of the agent.
        If no observations have occured, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["XP"]

    def getDistanceTravelled(self):
        """
        Returns the distance travelled by the agent.
        If no observations have occured, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["DistanceTravelled"]

    def getHealth(self):
        """
        Returns the current health of the agent.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["Life"]

    def getHunger(self):
        """
        Returns the current hunger of the agent.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["Food"]

    def getInventoryJson(self):
        """
        Returns an array of JSON inventory items that this agent is currently carrying.
        If no observations have occurred, returns None.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return None
        return agentState["inventory"]

    def getCurrentHotbarIndex(self):
        """
        Returns the hotbar index (0-based) that this agent currently has selected.
        If unable to determine the currently used hotbar index, returns -1.
        """
        agentState = self.getObservationJson()
        if agentState == None:
            return -1
        return agentState["currentItemIndex"]

    def __getNextAvailableHotbarIndex__(self):
        """
        Internal method that returns the next hotbar index (0-based) that is empty.
        If there is no such slot available, returns -1.
        """
        inventory = self.getInventoryJson()
        if inventory == None:
            return -1

        # Record all used hotbar index
        usedSlots = []
        for i in range(0, len(inventory)):
            currentItem = inventory[i]
            if currentItem["index"] < 9:
                usedSlots.append(currentItem["index"])

        # Now find first hotbar index not in use
        for i in range(0, 9):
            if not i in usedSlots:
                return i
        return -1

    def __locationOfItemInInventory__(self, item):
        """
        Internal method that returns the inventory index of the specified item in this agent's inventory.
        Returns -1 if the agent does not carry that item.
        """
        inventory = self.getInventoryJson()
        if inventory == None:
            return -1
        
        for i in range(0, len(inventory)):
            currentItem = inventory[i]
            if currentItem["type"] == item.value:
                return currentItem["index"] 
        return -1

    def __startMoving__(self, speed):
        """
        Start moving backwards or forwards at a specific speed. Accepted values range from -1 to 1.
        """
        self.host.sendCommand("move {}".format(speed))

    def stopMoving(self):
        """
        Stop moving forwards/backwards.
        """
        self.host.sendCommand("move 0")

    def __startStrafing__(self, speed):
        """
        Start moving left or right continuously at a specific speed. Accepted values range from -1 to 1.
        """
        self.host.sendCommand("strafe {}".format(speed))

    def __stopStrafing__(self, speed):
        """
        Stop moving left/right.
        """
        self.host.sendCommand("strafe 0")

    def __startChangingPitch__(self, speed):
        """
        Start tilting the agent's head up or down continuously at a specific speed. Accepted values range from -1 to 1.
        """
        self.host.sendCommand("pitch {}".format(speed))

    def __stopChangingPitch__(self):
        """
        Stop tilting the agent's head up/down.
        """
        self.host.sendCommand("pitch 0")

    def __startChangingYaw__(self, speed):
        """
        Start turning continuously to the left or right at a specific speed. Accepted values range from -1 to 1.
        """
        self.host.sendCommand("turn {}".format(speed))

    def __stopChangingYaw__(self):
        """
        Stop turning left/right.
        """
        self.host.sendCommand("turn 0")
    
    def stopTurning(self):
        """
        Stop turning left/right and up/down.
        """
        self.__stopChangingYaw__()
        self.__stopChangingPitch__()

    def __startJumping__(self):
        """
        Start jumping continuously.
        """
        self.host.sendCommand("jump 1")

    def __stopJumping__(self):
        """
        Stop jumping.
        """
        self.host.sendCommand("jump 0")

    def __startCrouching__(self):
        """
        Start crouching continuously.
        """
        self.host.sendCommand("crouch 1")

    def __stopCrouching__(self):
        """
        Stop crouching.
        """
        self.host.sendCommand("crouch 0")

    def __startAttacking__(self):
        """
        Start attacking continuously.
        """
        self.host.sendCommand("attack 1")

    def stopAttacking(self):
        """
        Stop attacking.
        """
        self.host.sendCommand("attack 0")

    def __startUsingItem__(self):
        """
        Begin continuously using the item in the currently selected hotbar slot.
        """
        self.host.sendCommand("use 1")

    def __stopUsingItem__(self):
        """
        Stop using the item in the currently selected hotbar slot.
        """
        self.host.sendCommand("use 0")

    def __throwItem__(self):
        """
        Throws item currently equipped.
        """
        self.host.sendCommand("discardCurrentItem")

    def stopAllMovement(self):
        """
        Stops any form of movement by this agent, including yaw/pitch turning and walking.
        """
        self.stopTurning()
        self.stopMoving()
        self.stopAttacking()

    def noAction(self):
        """
        An action to perform if there is nothing left to do for the current environment.
        Should usually be called upon at the bottom of the mission loop.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.noAction:
            return self.actionOverride.function(*self.actionOverride.args)

        self.stopAllMovement()
        return True

    def getNearbyEntities(self):
        """
        Returns a list of named EntityInfo tuples of all entities within a 20x20 area around this agent.
        Returns None on error.
        """
        worldState = self.getObservationJson()
        if worldState == None:
            return None
        entities = [EntityInfo("{}{}".format(k["name"], numerifyId(k["id"]).replace("-", "")), k["name"], Vector(k["x"], k["y"], k["z"]), k.get("quantity")) for k in worldState["nearby_entities"]]
        return entities

    def getNearbyEntityById(self, entityId):
        """
        Returns a named EntityInfo tuple describing an entity near this agent, using its id. If an entity with that id is not found, returns None.
        """
        entities = self.getNearbyEntities()
        for entity in entities:
            if entity.id == entityId:
                return entity
        return None

    def getClosestMob(self):
        """
        Returns a named EntityInfo tuple of the nearest mob within a 20x20 area of this agent.
        Returns none if no such mob exists.
        """
        agentPos = self.getPosition()
        entities = self.getNearbyEntities()
        if agentPos == None or entities == None:
            return None
        nearestDistance = 1000000
        nearestEntity = None
        for entity in entities:   # First entity is always the agent itself
            if isMob(entity.type):
                entityPos = entity.position
                distanceToEntity = MathExt.distanceBetweenPoints(agentPos, entityPos)
                if distanceToEntity < nearestDistance:
                    nearestDistance = distanceToEntity
                    nearestEntity = entity
        if nearestEntity == None:
            Logger.logClosestMob(self, None)
            self.lastClosestMob = "None"
            return None
        Logger.logMobDefinition(nearestEntity)    # In case we never saw this entity before
        Logger.logClosestMob(self, nearestEntity)
        self.lastClosestMob = nearestEntity.id
        return nearestEntity

    def getClosestPeacefulMob(self):
        """
        Returns a named EntityInfo tuple of the nearest peaceful mob within a 20x20 area of this agent.
        Returns None if no such mob exists.
        """
        agentPos = self.getPosition()
        entities = self.getNearbyEntities()
        if agentPos == None or entities == None:
            return None
        nearestDistance = 1000000
        nearestEntity = None
        for entity in entities:
            if isPeacefulMob(entity.type):
                entityPos = entity.position
                distanceToEntity = MathExt.distanceBetweenPoints(agentPos, entityPos)
                if distanceToEntity < nearestDistance:
                    nearestDistance = distanceToEntity
                    nearestEntity = entity
        if nearestEntity == None:
            Logger.logClosestPeacefulMob(self, None)
            self.lastClosestPeacefulMob = "None"
            return None
        Logger.logMobDefinition(nearestEntity)    # In case we never saw this entity before
        Logger.logClosestPeacefulMob(self, nearestEntity)
        self.lastClosestPeacefulMob = nearestEntity.id
        return nearestEntity

    def getClosestHostileMob(self):
        """
        Returns a named EntityInfo tuple of the nearest harmful mob within a 20x20 area of this agent.
        Returns None if no such mob exists.
        """
        agentPos = self.getPosition()
        entities = self.getNearbyEntities()
        if agentPos == None or entities == None:
            return None
        nearestDistance = 1000000
        nearestEntity = None
        for entity in entities:
            if isHostileMob(entity.type):
                entityPos = entity.position
                distanceToEntity = MathExt.distanceBetweenPoints(agentPos, entityPos)
                if distanceToEntity < nearestDistance:
                    nearestDistance = distanceToEntity
                    nearestEntity = entity
        if nearestEntity == None:
            Logger.logClosestHostileMob(self, None)
            self.lastClosestHostileMob = "None"
            return None
        Logger.logMobDefinition(nearestEntity)    # In case we never saw this entity before
        Logger.logClosestHostileMob(self, nearestEntity)
        self.lastClosestHostileMob = nearestEntity.id
        return nearestEntity

    def getClosestFoodMob(self):
        """
        Returns a named EntityInfo tuple of the nearest food mob within a 20x20 area of this agent.
        Returns None if no such mob exists.
        """
        agentPos = self.getPosition()
        entities = self.getNearbyEntities()
        if agentPos == None or entities == None:
            return None
        nearestDistance = 1000000
        nearestEntity = None
        for entity in entities:
            if isFoodMob(entity.type):
                entityPos = entity.position
                distanceToEntity = MathExt.distanceBetweenPoints(agentPos, entityPos)
                if distanceToEntity < nearestDistance:
                    nearestDistance = distanceToEntity
                    nearestEntity = entity
        if nearestEntity == None:
            Logger.logClosestFoodMob(self, None)
            self.lastClosestFoodMob = "None"
            return None
        Logger.logMobDefinition(nearestEntity)    # In case we never saw this entity before
        Logger.logClosestFoodMob(self, nearestEntity)
        self.lastClosestFoodMob = nearestEntity.id
        return nearestEntity

    def getClosestFoodItem(self):
        """
        Returns a named EntityInfo tuple of the nearest food item within a 20x20 area of this agent.
        Returns None if no such item exists.
        """
        agentPos = self.getPosition()
        entities = self.getNearbyEntities()
        if agentPos == None or entities == None:
            return None
        nearestDistance = 1000000
        nearestEntity = None
        for entity in entities:
            if isFoodItem(entity.type):
                entityPos = entity.position
                distanceToEntity = MathExt.distanceBetweenPoints(agentPos, entityPos)
                if distanceToEntity < nearestDistance:
                    nearestDistance = distanceToEntity
                    nearestEntity = entity
        if nearestEntity == None:
            #Logger.logClosestFoodItem(self, None)
            self.lastClosestFoodItem = "None"
            return None

        #Logger.logClosestFoodItem(self, nearestEntity)
        self.lastClosestFoodItem = nearestEntity.id
        return nearestEntity

    def getAllNearbyItems(self):
        """
        Returns a list of items that are lying on the ground within a 20x20 area of this agent.
        """
        entities = self.getNearbyEntities()
        itemList = []
        if entities == None:
            return itemList
        for entity in entities:
            if isItem(entity.type):
                itemList.append(entity)
        return itemList

    def getClosestBlockByType(self, blockType):
        """
        Returns the nearest block of a given type as an entity. If no such block is found, returns None.
        """
        currentPos = self.getPosition()
        grid = self.getBlockGrid()
        if grid == None or currentPos == None:
            return None

        # Find the block type in the observation grid of nearby blocks
        index = 0
        for y in range(0, GRID_OBSERVATION_Y_LEN):
            for z in range(0, GRID_OBSERVATION_Z_LEN):
                for x in range(0, GRID_OBSERVATION_X_LEN):
                    if grid[index] == blockType.value:
                        xDiff = x - GRID_OBSERVATION_X_HALF_LEN
                        yDiff = y - GRID_OBSERVATION_Y_HALF_LEN
                        zDiff = z - GRID_OBSERVATION_Z_HALF_LEN
                        return EntityInfo("someBlock...", blockType.value, Vector(currentPos.x + xDiff, currentPos.y + yDiff, currentPos.z + zDiff), 1)
                    index += 1
        return None

    def getBlockTypeAtLocation(self, loc):
        """
        Get the block type at the position given. This position must be within observable distance to this agent. Returns None on error.
        """
        currentPos = self.getPosition()
        grid = self.getBlockGrid()
        if grid == None or currentPos == None:
            return None

        # Convert the x, y, z position to a location in the grid
        xIdx = GRID_OBSERVATION_X_HALF_LEN + (loc.x - currentPos.x)
        yIdx = GRID_OBSERVATION_Y_HALF_LEN + (loc.y - currentPos.y)
        zIdx = GRID_OBSERVATION_Z_HALF_LEN + (loc.z - currentPos.z)
        idx = int(yIdx * GRID_OBSERVATION_Z_LEN * GRID_OBSERVATION_X_LEN + zIdx * GRID_OBSERVATION_X_LEN + xIdx)

        if idx < 0 or idx >= len(grid):
            return None

        # We want to return the actual enum.. not just the string
        return stringToBlockEnum(grid[idx])

    def __getYawRateToFacePosition__(self, targetPosition):
        """
        Obtain a rate in which to turn along the yaw angle to face a given target position.
        """
        worldState = self.getObservationJson()
        agentPos = self.getPosition()
        if worldState == None or agentPos == None:
            return False    
        currentAngle = worldState["Yaw"] if worldState["Yaw"] >= 0 else 360.0 - abs(worldState["Yaw"])
        vector = MathExt.vectorFromPoints(agentPos, targetPosition)
        vector = MathExt.normalizeVector(vector)

        # Get the angle that we wish to face
        targetAngle = None
        if MathExt.valuesAreEqual(vector.x, 0, 1.0e-14): # Avoid dividing by 0
            if vector.z >= 0:
                targetAngle = -MathExt.PI_OVER_TWO
            else:
                targetAngle = MathExt.PI_OVER_TWO
        else:
            targetAngle = math.atan(vector.z / vector.x)
    
        # Adjust angle based on quadrant of vector
        if vector.x <= 0:   # Quadrant 1 or 2
            targetAngle = MathExt.PI_OVER_TWO + targetAngle
        elif vector.x > 0:  # Quadrant 3 or 4
            targetAngle = MathExt.THREE_PI_OVER_TWO + targetAngle

        targetAngle = math.degrees(targetAngle)
        if MathExt.valuesAreEqual(targetAngle, 360.0, 1.0e-14):
            targetAngle = 0

        # Get difference between the two angles
        diff = None
        if currentAngle <= targetAngle:
            diff = min(targetAngle - currentAngle, 360 - targetAngle + currentAngle)
        else:
            diff = min(currentAngle - targetAngle, 360 - currentAngle + targetAngle)
        
        # Get the turning direction
        multiplier = 1
        if currentAngle > targetAngle and currentAngle - targetAngle < 180:
            multiplier = -1
        elif targetAngle > currentAngle and targetAngle - currentAngle > 180:
            multiplier = -1

        # Get the turning rate
        rate = 0
        if diff > 10:
            rate = 1.0 * multiplier
        elif diff > 5:
            rate = .25 * multiplier
        elif diff > 2:
            rate = .05 * multiplier
        else:
            rate = MathExt.affineTransformation(diff, 0.0, 180.0, 0, 1.0) * multiplier

        return rate

    def __getPitchRateToFacePosition__(self, targetPosition):
        """
        Obtain a rate in which to turn along the pitch angle to face the given target position.
        """
        worldState = self.getObservationJson()
        agentPos = self.getPosition()
        if worldState == None or agentPos == None:
            return False  
        currentAngle = worldState["Pitch"]
        vectorWithHeight = MathExt.vectorFromPoints(agentPos, targetPosition)
        vectorWithHeight = MathExt.normalizeVector(vectorWithHeight)
        vectorWithoutHeight = Vector(vectorWithHeight.x, 0, vectorWithHeight.z)

        # Get the angle that we wish to change the pitch to (account for range -90 to 90)
        if MathExt.isZeroVector(vectorWithHeight) or MathExt.isZeroVector(vectorWithoutHeight): # Avoid dividing by 0
            return False
        cosValue = MathExt.dotProduct(vectorWithHeight, vectorWithoutHeight) / (MathExt.vectorMagnitude(vectorWithHeight) * MathExt.vectorMagnitude(vectorWithoutHeight))
        if cosValue > 1:
            cosValue = 1
        elif cosValue < -1:
            cosValue = -1
        targetAngle = math.acos(cosValue)
        if vectorWithHeight.y > 0:
            targetAngle = -targetAngle

        targetAngle = math.degrees(targetAngle)

        # Get difference between two angles
        diff = None
        if currentAngle <= targetAngle:
            diff = targetAngle - currentAngle
        else:
            diff = currentAngle - targetAngle

        # Get the turning direction
        multiplier = 1
        if currentAngle > targetAngle:
            multiplier = -1

        # Get the turning rate
        rate = 0
        if diff > 10:
            rate = 1.0 * multiplier
        elif diff > 5:
            rate = .25 * multiplier
        elif diff > 2:
            rate = .05 * multiplier
        else:
            rate = MathExt.affineTransformation(diff, 0.0, 180.0, 0, 1.0) * multiplier
        return rate

    def __isLookingAt__(self, targetPosition):
        """
        Returns true if this agent is currently looking in the proximity of the target position.
        """
        # Our tolerance depends on how close we are to the object
        agentPos = self.getPosition()
        distanceFromTarget = MathExt.distanceBetweenPoints(agentPos, targetPosition)
        yawRate = self.__getYawRateToFacePosition__(targetPosition)
        pitchRate = self.__getPitchRateToFacePosition__(targetPosition)
        if distanceFromTarget > 7:
            if abs(yawRate) >= .25 or abs(pitchRate) >= .25:
                return False
        else:
            if abs(yawRate) >= .8 or abs(pitchRate) >= .8:
                return False
        return True

    def __lookAtPosition__(self, targetPosition):
        """
        Begin continuously turning/looking to face a Vector position.
        Returns true if the agent is currently looking at the target. Returns false otherwise.
        """
        # Our tolerance depends on how close we are to the object
        agentPos = self.getPosition()
        if agentPos == None:
            return False
        distanceFromTarget = MathExt.distanceBetweenPoints(agentPos, targetPosition)
        yawRate = self.__getYawRateToFacePosition__(targetPosition)
        pitchRate = self.__getPitchRateToFacePosition__(targetPosition)
        self.__startChangingYaw__(yawRate)
        self.__startChangingPitch__(pitchRate)
        if distanceFromTarget > 7:
            if abs(yawRate) >= .25 or abs(pitchRate) >= .25:
                return False
        else:
            if abs(yawRate) >= .8 or abs(pitchRate) >= .8:
                return False
        return True

    def lookAtEntity(self, entity):
        """
        Begin continuously turning/looking to face the specified entity.
        Returns true if the agent is currently facing the entity. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.lookAtEntity:
            return self.actionOverride.function(*self.actionOverride.args)

        if not isItem(entity.type):
            Logger.logLookAtStart(self, entity)
            self.lastStartedLookingAt = entity.id

        # Look at the target
        isLookingAt = self.__lookAtPosition__(entity.position)
        if isLookingAt:
            self.__stopChangingPitch__()
            self.__stopChangingYaw__()
            if not isItem(entity.type):
                Logger.logLookAtFinish(self, entity)
                self.lastFinishedLookingAt = entity.id
            return True
        return False

    def lookAtAgent(self, agent):
        """
        Begin continuously turning/looking to face the specified agent.
        Returns true if the agent is currently facing the agent. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.lookAtAgent:
            return self.actionOverride.function(*self.actionOverride.args)

        agentId = agent.getId()
        agentPos = agent.getPosition()
        if agentId == None or agentPos == None:
            return False

        # Represent the agent as an EntityInfo tuple
        agentEntity = EntityInfo(agentId, "agent", agentPos, 1)

        Logger.logLookAtStart(self, agentEntity)
        self.lastStartedLookingAt = agentId

        # Look at the target
        isLookingAt = self.__lookAtPosition__(agentPos)
        if isLookingAt:
            self.__stopChangingPitch__()
            self.__stopChangingYaw__()
            self.lastFinishedLookingAt = agent.id
            Logger.logLookAtFinish(self, agentEntity)
            return True
        return False

    def __isAt__(self, targetPosition, tol = 0.5):
        """
        Returns true if this agent is currently at the target position (within the tolerance provided).
        """
        agentPos = self.getPosition()
        if agentPos == None:
            return False

        distance = MathExt.distanceBetweenPointsXZ(agentPos, targetPosition)
        if distance > tol:
            return False
        
        return True

    def __moveToPosition__(self, targetPosition, tol = 0.5, minDistance = 0.0, hardStop = True):
        """
        Begin continuously moving to reach a desired Vector position.
        Optionally specify a tolerance, as well as a minimum distance that the agent can be close to the target.
        Returns true if the agent is currently at the desired target. Returns false otherwise.
        """
        agentPos = self.getPosition()
        if agentPos == None:
            return False

        distance = MathExt.distanceBetweenPointsXZ(agentPos, targetPosition)

        if distance < tol and distance > minDistance:
            if hardStop:
                self.stopMoving()
            else:
                self.__startMoving__(0.4)
            return True
        elif distance > tol:
            self.__startMoving__(1)
            return False
        else:
            self.__startMoving__(-1)
            return False

    def moveToEntity(self, entity):
        """
        Begin continuously moving to reach the specified entity.
        Returns true if the agent is currently within striking distance of the mob. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.moveToEntity:
            return self.actionOverride.function(*self.actionOverride.args)

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: We are looking at the target
            isLooking = self.__isLookingAt__(entity.position)
            if not isLooking:
                self.stopAllMovement()
                return False

        if not isItem(entity.type):
            Logger.logMoveToStart(self, entity)
            self.lastStartedMovingTo = entity.id
        
        # Move to the target
        isAt = self.__moveToPosition__(entity.position, STRIKING_DISTANCE)
        if isAt:
            if not isItem(entity.type):
                self.lastFinishedMovingTo = entity.id
                Logger.logMoveToFinish(self, entity)
            self.stopMoving()
            return True
        return False

    def __moveToItem__(self, item):
        """
        Begin continuously moving to reach a the specified item.
        Returns the list of items that were added to the agent's inventory on success.
        Returns None on failure.
        """
        # DO NOT CHECK ACTION OVERRIDE HERE... The only way we will have called this action is from PickUpItem...
        # Which locks waiting for this action to report true

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: We are looking at the target
            isLooking = self.__isLookingAt__(item.position)
            if not isLooking:
                self.stopAllMovement()
                return None

        # If this is the first call to move to this item, remember the amount of the item we started with.
        # Additionally, queue up each item id in the stack so that when they appear in the AgentInventory, the ids will be preserved.
        if self.lastStartedMovingTo != item.id:
            self.lastItemAmount = self.inventory.amountOfItem(item.type)

        # Move to the target (do not allow hard-stop, in case we are not yet quite close enough to pick up item)
        isAt = self.__moveToPosition__(item.position, PICK_UP_ITEM_DISTANCE, 0, False)
        if isAt:
            # Do not report true until we have officially picked up the item
            newItems, _ = self.inventory.update()
            newAmount = self.inventory.amountOfItem(item.type)
            if newAmount > self.lastItemAmount:
                self.actionOverride = None  # Release lock
                self.stopMoving()   # Stop moving, since __moveToPosition__ will not stop agent automatically in this case
                return newItems
        return None

    def moveToAgent(self, agent):
        """
        Begin continuously moving & turning to reach the specified agent.
        Returns true if the agent is currently at the agent. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.moveToAgent:
            return self.actionOverride.function(*self.actionOverride.args)

        agentId = agent.getId()
        agentPos = agent.getPosition()
        if agentPos == None:
            return False
        
        # Represent the agent as an EntityInfo tuple
        agentEntity = EntityInfo(agentId, "agent", agentPos, 1)

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: We are looking at target
            isLooking = self.__isLookingAt__(agentPos)
            if not isLooking:
                self.stopAllMovement()
                return False

        Logger.logMoveToStart(self, agentEntity)
        self.lastStartedMovingTo = agentId

        # Move to the target
        isAt = self.__moveToPosition__(agentPos, GIVING_DISTANCE, 2)
        if isAt:
            self.lastFinishedMovingTo = agent.id
            Logger.logMoveToFinish(self, agentEntity)
            return True
        return False

    def pickUpItem(self, item):
        """
        Begin looking at and moving to a nearby item to pick it up and add it to the agent's inventory.
        Returns true if the action has successfully completed, and false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.pickUpItem:
            return self.actionOverride.function(*self.actionOverride.args)

        # Look at the item (if we have already looked at the item and locked this function, skip this step)
        if self.actionOverride == None:
            isLookingAt = self.lookAtEntity(item)
            if not isLookingAt:
                return False

        # We don't want to keep turning if we have no way to stop after locking
        self.stopTurning()

        # Note: At this point, we will lock down this function and force it to complete, as not to miss an addition to the agent's inventory
        self.actionOverride = Action(self.pickUpItem, [item])
        pickedUpItems = self.__moveToItem__(item)
        if pickedUpItems != None:
            self.actionOverride = None  # Release lock
            for item in pickedUpItems:
                Logger.logPickUpItem(self, item)
            return True
        else:
            return False

    def craft(self, item, recipeItems):
        """
        Craft an item from other items in this agent's inventory. This requires providing a list of RecipeItems.
        Returns true if the item was successfully crafted and is in the agent's inventory. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.craft:
            return self.actionOverride.function(*self.actionOverride.args)

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition - We have enough of each recipe item in our inventory
            for recipeItem in recipeItems:
                if self.inventory.amountOfItem(recipeItem.type) < recipeItem.quantity:
                    return False

        # Get a list of the items to be used
        itemsUsed = []
        for recipeItem in recipeItems:
            items = self.inventory.allItemsByType(recipeItem.type)
            for i in range(0, recipeItem.quantity):
                itemsUsed.append(items[i])

        # Craft the item and add it to our inventory, recording its id
        self.host.sendCommand("craft {}".format(item.value))
        time.sleep(0.5)

        # Log the successful crafting of the item
        Logger.logCraft(self, item, itemsUsed)
        return True
    
    def attackMob(self, mob):
        """
        Attack a mob using the currently equipped item, provided that it is within striking distance. This method
        calls LookAt if it is necessary for the agent to turn to face the mob. Returns true if successful, and false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.attackMob:
            return self.actionOverride.function(*self.actionOverride.args)

        oldMobsKilled = self.getMobsKilled()
        if oldMobsKilled == None:
            return False

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: The provided entity is a mob
            if not isMob(mob.type):
                return False

            # Precondition: We are looking at target
            isLooking = self.__isLookingAt__(mob.position)
            if not isLooking:
                self.stopAttacking()
                return False

            # Precondition: We are at the target
            isAt = self.__isAt__(mob.position, STRIKING_DISTANCE)
            if not isAt:
                self.stopAllMovement()
                return False

        self.__startAttacking__()
        self.stopAllMovement()  # Momentarily stop all movement to check if we killed the entity
        time.sleep(0.5)         # Prevents possible spamming of the attack action
        newMobsKilled = self.getMobsKilled()

        if newMobsKilled > oldMobsKilled:
            Logger.logAttack(self, mob, True)
        else:
            Logger.logAttack(self, mob, False)

        return True

    def equip(self, item):
        """
        Changes the currently equipped item to something in this agent's inventory. This can cause items to be
        swapped from the hot-bar. Returns true if the specified item is equipped. Returns false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.equip:
            return self.actionOverride.function(*self.actionOverride.args)

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: We have atleast one of that item
            itemIdx = self.__locationOfItemInInventory__(item)
            if itemIdx == -1:
                return False
        
        # Obtain the inventory item we will give
        inventoryItem = self.inventory.itemByType(item)
        if inventoryItem == None:
            return False

        # Check if item is already in hotbar (note: key commands are 1-indexed)
        if itemIdx < 9:
            self.host.sendCommand("hotbar.{} 1".format(itemIdx + 1))
            self.host.sendCommand("hotbar.{} 0".format(itemIdx + 1))
            Logger.logEquipItem(self, inventoryItem)
            self.lastEquippedItem = inventoryItem.id
            return True
        
        # Try to swap the item into the hotbar where there currently exists no item
        swapIndex = self.__getNextAvailableHotbarIndex__()
        if swapIndex != -1:
            self.host.sendCommand("swapInventoryItems {} {}".format(swapIndex, itemIdx))
            self.host.sendCommand("hotbar.{} 1".format(swapIndex + 1))
            self.host.sendCommand("hotbar.{} 0".format(swapIndex + 1))
            Logger.logEquipItem(self, inventoryItem)
            self.lastEquippedItem = inventoryItem.id
            return True

        # Try to swap the item into the index currently in use
        swapIndex = self.getCurrentHotbarIndex()
        if swapIndex != -1:
            self.host.sendCommand("swapInventoryItems {} {}".format(swapIndex, itemIdx))
            self.host.sendCommand("hotbar.{} 1".format(swapIndex + 1))
            self.host.sendCommand("hotbar.{} 0".format(swapIndex + 1))
            Logger.logEquipItem(self, inventoryItem)
            self.lastEquippedItem = inventoryItem.id
            return True
        
        return False

    def currentlyEquipped(self):
        """
        Returns the item currently equipped in this agent's inventory. Returns None if no such item exists.
        """
        inventoryJson = self.getInventoryJson()
        hotbarIdx = self.getCurrentHotbarIndex()
        if inventoryJson == None or hotbarIdx == None:
            return
        
        for inventorySlot in inventoryJson:
            if inventorySlot["index"] == hotbarIdx:
                itemType = stringToItemEnum(inventorySlot["type"])
                return self.inventory.itemByType(itemType)
        return None

    def giveItemToAgent(self, item, agent):
        """
        Give an item in this agent's inventory to another agent.
        Returns true if successful, and false otherwise.
        """
        # Check action override
        if self.actionOverride != None and self.actionOverride.function != self.giveItemToAgent:
            return self.actionOverride.function(*self.actionOverride.args)

        self.stopMoving()  # Make sure we are stopped before checking our direction and position
        agentPos = agent.getPosition()
        if agentPos == None:
            return False

        # PRECONDITIONS
        if self.actionOverride == None:
            # Precondition: We have that item equipped (not possible if we do not have the item)
            equippedItem = self.currentlyEquipped()
            equippedItemType = "None" if equippedItem == None else equippedItem.type
            if equippedItemType != item.value:
                return False

            # Precondition: We are looking at the agent
            isLookingAt = self.__isLookingAt__(agentPos)
            if not isLookingAt:
                return False

            # Precondition: We are at the agent
            isAt = self.__isAt__(agentPos, GIVING_DISTANCE)
            if not isAt:
                return False

        # Remove one item of that type from this agent's inventory
        inventoryItem = self.inventory.itemByType(item)
        if inventoryItem == None:
            return False
        self.inventory.removeItem(inventoryItem)
        agent.inventory.addItem(item.value, inventoryItem.id)   # We must preserve the id of the item

        # Log the results
        Logger.logGiveItemToAgent(self, inventoryItem, agent)

        self.equip(item)
        time.sleep(0.5) # There is a small delay in equipping an item
        self.__throwItem__()
        time.sleep(3)   # Wait for agent to pick up item
        return True