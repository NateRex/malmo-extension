import malmoext.MalmoPython as MalmoPython
import json
import math
import time
import copy
from enum import Enum
from collections import namedtuple
from malmoext.Utils import MathUtils, Mobs, Items, LogUtils, Vector, Entity, numerifyId, STRIKING_DISTANCE, GIVING_DISTANCE, PICK_UP_ITEM_LOCKDOWN_DISTANCE
from malmoext.Inventory import Inventory

class Agent:
    '''
    Wrapper class for a Malmo AgentHost object. Exposes methods corresponding to 'high-level'
    actions such as looking at or moving to vectorized positions. Any completed actions by this
    agent automatically triggers logging by any loggers that get updated.
    '''
    allAgents = {}  # A map containing all agents that were created, accessible by ID
    ActionOverride = namedtuple("ActionOverride", "function args")  # Representation of an action w/ args and cached data that should internally override any other action called

    def __init__(self, agentID, agentType):
        if agentID in Agent.allAgents:
            raise Exception("Two agents can not have the same ID")

        self.__host = MalmoPython.AgentHost()   # Reference to wrapped Malmo AgentHost
        self.__json = None                      # Cache of the last obtained JSON representation of this Agent from Malmo
        self.__actionOverride = None            # Possible action override of whatever action was called
        self.__logReports = []                  # A list of log reports to be read by the Logger next iteration
        self.id = agentID                       # The ID of this agent
        self.type = agentType                   # The AgentType of this agent
        self.inventory = Inventory(self)        # Reference to this agent's inventory

        # Add this agent to the global registry
        Agent.allAgents[self.id] = self

    def isMissionActive(self):
        '''
        Returns true if the mission involving this agent is still running.
        '''
        return self.__host.peekWorldState().is_mission_running

    def getMalmoAgent(self):
        '''
        Returns a reference to the raw Malmo AgentHost object that this object serves as a wrapper for.
        '''
        return self.__host

    def toJSON(self):
        '''
        Returns the JSON representation of this agent output by Malmo.
        '''
        malmoJSON = self.__host.getWorldState()
        if len(malmoJSON.observations) > 0:
            self.__json = json.loads(malmoJSON.observations[-1].text)
        return self.__json

    def getAndClearLogReports(self):
        '''
        THIS METHOD SHOULD ONLY BE USED INTERNALLY BY THE LOGGER. Returns the list of actions that
        need logging since last iteration, and resets the list.
        '''
        result = self.__logReports
        self.__logReports = []
        return result

    def isAlive(self):
        '''
        Returns true if this agent is alive.
        '''
        return self.toJSON()["IsAlive"]

    def __position(self):
        '''
        Returns the (x,y,z) position of this agent.
        '''
        agentJSON = self.toJSON()
        return Vector(agentJSON["XPos"], agentJSON["YPos"] + 1, agentJSON["ZPos"])

    def __mobsKilled(self):
        '''
        Returns the number of mobs this agent has killed.
        '''
        return self.toJSON()["MobsKilled"]

    def __startWalking(self, speed):
        '''
        Start walking forwards or backwards. Accepts speed of [-1, 1].
        '''
        self.__host.sendCommand("move {}".format(speed))

    def __stopWalking(self):
        '''
        Stop walking.
        '''
        self.__host.sendCommand("move 0")

    def __startChangingPitch(self, speed):
        '''
        Start moving the agent's POV up or down. Accepts speeds of [-1, 1].
        '''
        self.__host.sendCommand("pitch {}".format(speed))

    def __startChangingYaw(self, speed):
        '''
        Start moving the agent's POV left or right. Accepts speeds of [-1, 1].
        '''
        self.__host.sendCommand("turn {}".format(speed))

    def __stopTurning(self):
        '''
        Stop moving the agent's POV in all directions.
        '''
        self.__host.sendCommand("pitch 0")
        self.__host.sendCommand("turn 0")

    def __startAttacking(self):
        '''
        Causes the agent to begin attacking continuously.
        '''
        self.__host.sendCommand("attack 1")

    def __stopAttacking(self):
        '''
        Causes the agent to stop attacking.
        '''
        self.__host.sendCommand("attack 0")

    def __throwItem(self):
        '''
        Causes the agent to throw the currently held item.
        '''
        self.__host.sendCommand("discardCurrentItem")

    def __checkPreconditions(self, *preconditionResults):
        '''
        Returns true if all of the given precondition boolean results are met, false otherwise.
        '''
        # Return hardcoded true if caller is currently in action override mode (avoids infinite loop)
        if self.__actionOverride != None:
            return True

        for result in preconditionResults:
            if not result:
                return False
        return True

    def __shouldPerformActionOverride(self, callerAction):
        '''
        Returns true if there exists an action override that should be performed instead of
        the caller. Returns false otherwise.
        '''
        if self.__actionOverride != None and self.__actionOverride.function != callerAction:
            return True
        return False

    def stopMoving(self):
        '''
        Stop all movement of this agent.
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.stopMoving):
            return self.__actionOverride.function(*self.__actionOverride.args)

        self.__stopTurning()
        self.__stopWalking()
        self.__stopAttacking()

    def nearbyEntities(self):
        '''
        Returns a list of all nearby entities to this agent.
        '''
        agentJSON = self.toJSON()
        return [Entity("{}{}".format(k["name"], numerifyId(k["id"]).replace("-", "")), k["name"], Vector(k["x"], k["y"], k["z"]), k.get("quantity")) for k in agentJSON["nearby_entities"]]

    def closestMob(self, variant=Mobs.All):
        '''
        Get the closest mob to this agent. Optionally specify additional modifiers for filtering mobs by an enumerated type.
        Returns None if no mob was found nearby to this agent.
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.closestMob):
            self.__actionOverride.function(*self.__actionOverride.args)
            return None

        aPos = self.__position()
        nearbyEntities = self.nearbyEntities()
        if variant == Mobs.All:
            comparator = Mobs.All.isMember
        elif variant == Mobs.Peaceful:
            comparator = Mobs.Peaceful.isMember
        elif variant == Mobs.Hostile:
            comparator = Mobs.Hostile.isMember
        elif variant == Mobs.Food:
            comparator = Mobs.Food.isMember
        else:
            raise Exception("Closest mob variant must be an enumerated type")

        closestDistance = 1000000.0
        closestMob = None
        for entity in nearbyEntities:
            if comparator(entity.type):
                ePos = entity.position
                distance = MathUtils.distanceBetweenPoints(aPos, ePos)
                if distance < closestDistance:
                    closestDistance = distance
                    closestMob = entity
        self.__logReports.append(LogUtils.ClosestMobReport(variant, closestMob))
        return closestMob

    def closestItem(self, variant=Items.All):
        '''
        Get the closest item on the ground to this agent. Optionally specify additional modifiers for filtering
        items by an enumerated type. Returns None if no item was found nearby to this agent.
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.closestItem):
            self.__actionOverride.function(*self.__actionOverride.args)
            return None

        aPos = self.__position()
        nearbyEntities = self.nearbyEntities()
        if variant == Items.All:
            comparator = Items.All.isMember
        elif variant == Items.Food:
            comparator = Items.Food.isMember
        else:
            raise Exception("Closest item variant must be an enumerated type")

        closestDistance = 1000000.0
        closestItem = None
        for entity in nearbyEntities:
            if comparator(entity.type):
                ePos = entity.position
                distance = MathUtils.distanceBetweenPoints(aPos, ePos)
                if distance < closestDistance:
                    closestDistance = distance
                    closestItem = entity
        self.__logReports.append(LogUtils.ClosestItemReport(variant, closestItem))
        return closestItem

    def __calculateTargetPitchRate(self, targetPos):
        '''
        Calculate the rate at which to move the agent's POV up/down in order to face an (x,y,z) position.
        '''
        aJSON = self.toJSON()
        aPos = self.__position()
        currAngle = aJSON["Pitch"]
        vec = MathUtils.vectorFromPoints(aPos, targetPos)
        vec = MathUtils.normalizeVector(vec)
        trimmedVec = Vector(vec.x, 0, vec.z)

        # Convert target position to a target angle (-90 to 90 degrees)
        if MathUtils.isZeroVector(trimmedVec):
            return 0.0
        cos = MathUtils.dotProduct(vec, trimmedVec) / (MathUtils.vectorMagnitude(vec) * MathUtils.vectorMagnitude(trimmedVec))
        if cos > 1:
            cos = 1
        elif cos < -1:
            cos = -1
        targetAngle = math.acos(cos)
        if vec.y > 0:
            targetAngle = -targetAngle
        targetAngle = math.degrees(targetAngle)

        # Get difference between current and target angle
        if currAngle <= targetAngle:
            angleDiff = targetAngle - currAngle
        else:
            angleDiff = currAngle - targetAngle

        # Get the turning direction
        if currAngle > targetAngle:
            turnDirection = -1
        else:
            turnDirection = 1

        # Calculate the turning rate
        rate = MathUtils.affineTransformation(angleDiff, 0.0, 180.0, 0, 1.0) * 4 * turnDirection
        rate = min(rate, 1) if rate >= 0 else max(rate, -1)
        return rate

    def __calculateTargetYawRate(self, targetPos):
        '''
        Calculate the rate at which to move the agent's POV left/right in order to face an (x,y,z) position.
        '''
        aJSON = self.toJSON()
        aPos = self.__position()
        currAngle = aJSON["Yaw"] if aJSON["Yaw"] >= 0 else 360.0 - abs(aJSON["Yaw"])
        vec = MathUtils.vectorFromPoints(aPos, targetPos)
        vec = MathUtils.normalizeVector(vec)

        # Convert target position to a target angle (360 degrees)
        if MathUtils.valuesAreEqual(vec.x, 0):
            if vec.z >= 0:
                targetAngle = -MathUtils.PI_OVER_TWO
            else:
                targetAngle = MathUtils.PI_OVER_TWO
        else:
            targetAngle = math.atan(vec.z / vec.x)

        # Modify target angle based on which quadrant the vector lies in
        if vec.x <= 0:   # quadrant 1 or 2
            targetAngle = MathUtils.PI_OVER_TWO + targetAngle
        else:
            targetAngle = MathUtils.THREE_PI_OVER_TWO + targetAngle
        targetAngle = math.degrees(targetAngle)
        if MathUtils.valuesAreEqual(targetAngle, 360.0):
            targetAngle = 0

        # Get difference between current and target angle
        if currAngle <= targetAngle:
            angleDiff = min(targetAngle - currAngle, 360 - targetAngle + currAngle)
        else:
            angleDiff = min(currAngle - targetAngle, 360 - currAngle + targetAngle)

        # Get the turning direction
        if currAngle > targetAngle and currAngle - targetAngle < 180:
            turnDirection = -1
        elif targetAngle > currAngle and targetAngle - currAngle > 180:
            turnDirection = -1
        else:
            turnDirection = 1

        # Calculate the turning rate
        rate = MathUtils.affineTransformation(angleDiff, 0.0, 180.0, 0, 1.0) * 4 * turnDirection
        rate = min(rate, 1) if rate >= 0 else max(rate, -1)
        return rate

    def __isLookingAt(self, targetPos, pitchRate=None, yawRate=None):
        '''
        Returns true if the agent is currently looking at the given (x,y,z) position.
        Optionally provide the pitch and yaw turning rates if they were already previously calculated.
        '''
        pitchRate = pitchRate if pitchRate != None else self.__calculateTargetPitchRate(targetPos)
        yawRate = yawRate if yawRate != None else self.__calculateTargetYawRate(targetPos)

        # Tolerance depends on how close we are to the target
        aPos = self.__position()
        distance = MathUtils.distanceBetweenPoints(aPos, targetPos)

        # If we are close to target and yaw is 1, there is a chance we got stuck and are
        # circling the target. Step back and return false for this iteration..
        # if distance < 2 and yawRate > .9:
        #     self.__startWalking(-1)
        #     time.sleep(0.2)
        #     self.stopMoving()
        #     return False

        if distance < 2:
            return abs(pitchRate) <= .4 and abs(yawRate) <= .4
        else:
            return abs(pitchRate) <= .2 and abs(yawRate) <= .2

    def lookAt(self, entity):
        '''
        Begin moving the agent's POV up/down and left/right to face the given entity.
        Returns true if the agent is facing the entity, false otherwise.

            Preconditions:
                None
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.lookAt):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # If entity is an agent, represent it as an entity
        if isinstance(entity, Agent):
            entity = Entity(entity.id, "agent", entity.__position(), 1)

        # Preconditions - None

        # Action
        pitchRate = self.__calculateTargetPitchRate(entity.position)
        yawRate = self.__calculateTargetYawRate(entity.position)
        if self.__isLookingAt(entity.position, pitchRate, yawRate):
            self.__stopTurning()
            if not Items.All.isMember(entity.type):  # Items are a special case for which we do not log
                self.__logReports.append(LogUtils.LookAtReport(entity))
            return True
        else:
            self.__startChangingPitch(pitchRate)
            self.__startChangingYaw(yawRate)
            return False

    def __isAt(self, targetPos, minTol=0.0, maxTol=STRIKING_DISTANCE):
        '''
        Returns true if the agent is currently at the given (x,y,z) position within tolerance.
        Tolerance values are as follows:

            minTol: Agent must be no closer than this value
            maxTol: Agent must be closer than this value
        '''
        aPos = self.__position()
        distance = MathUtils.distanceBetweenPointsXZ(aPos, targetPos)
        if distance >= minTol and distance <= maxTol:
            return True
        else:
            return False

    def __moveToPosition(self, targetPos, minTol=0.0, maxTol=STRIKING_DISTANCE, hardStop=True):
        '''
        Command the agent to begin walking forwards or backwards in order to reach the given target
        (x,y,z) position within tolerance. Returns true if the agent is at the target, false otherwise.
        This function takes several optional arguments:

            minTol: Agent must be no closer than this value
            maxTol: Agent must be closer than this value
            hardStop: Once within tolerance, should the agent come to a complete stop, or slow down
        '''
        aPos = self.__position()
        distance = MathUtils.distanceBetweenPointsXZ(aPos, targetPos)
        if distance >= minTol and distance <= maxTol:
            if hardStop:
                self.stopMoving()
            else:
                self.__startWalking(0.4)
            return True
        elif distance > maxTol:
            self.__startWalking(1)
            return False
        else:
            self.__startWalking(-1)
            return False

    def moveTo(self, entity):
        '''
        Begin moving the agent to the given entity. Returns true if the agent is at the entity,
        false otherwise.

            Preconditions:
                - The agent is looking at the entity
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.moveTo):
            return self.__actionOverride.function(*self.__actionOverride.args)

        minTol = 0.0
        maxTol = STRIKING_DISTANCE

        # If entity is an agent, represent it as an entity
        if isinstance(entity, Agent):
            entity = Entity(entity.id, "agent", entity.__position(), 1)
            minTol = 2.0
            maxTol = GIVING_DISTANCE

        # Preconditions
        if not self.__checkPreconditions(self.__isLookingAt(entity.position)):
            self.stopMoving()
            return False

        # Items are a special case since they can be picked up. Once close, lock down on the pickUpItem action.
        if Items.All.isMember(entity.type):
            distanceToItem = MathUtils.distanceBetweenPointsXZ(self.__position(), entity.position)
            if distanceToItem <= PICK_UP_ITEM_LOCKDOWN_DISTANCE:
                currentInventoryAmt = self.inventory.amountOfItem(entity.type)
                self.__actionOverride = Agent.ActionOverride(self.__pickUpItem, [entity, currentInventoryAmt])
                return self.__pickUpItem(entity, currentInventoryAmt)

        # Action
        if self.__moveToPosition(entity.position, minTol, maxTol):
            self.__stopWalking()
            self.__logReports.append(LogUtils.MoveToReport(entity))
            return True
        else:
            return False

    def pickUpItem(self, item):
        '''
        Commands the agent to look at and move to an item on the ground to pick it up. Is the equivalent of calling lookAt(item)
        followed by moveTo(item). Is best used for items within close proximity to the agent.
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.pickUpItem):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # Note - Once we are close enough, moveTo will cause the agent to lock down on the internal __pickUpItem function,
        #        which will return true once the item appears in inventory
        if not self.lookAt(item):
            return False
        if not self.moveTo(item):
            return False
        return True

    def __pickUpItem(self, item, previousInventoryAmt):
        '''
        Internal lockdown action for continuously moving an agent towards an item until it has been picked up and
        shows up in the agent's inventory. Requires the previous amount of that item in the agent's inventory to be
        passed in as a parameter.
        '''
        # Do not check for action override. Otherwise, we'd get stuck in an infinite loop!
        # Do not check any preconditions - we assume that if we locked down on this override that preconditions remain satisfied

        # Move to the position, slowing down as we approach
        self.__moveToPosition(item.position, 0, PICK_UP_ITEM_LOCKDOWN_DISTANCE, False)

        # Make sure we log that we picked up all kinds of items, regardless of what they are
        newInventoryItems, _ = self.inventory.sync()
        for item in newInventoryItems:
            self.__logReports.append(LogUtils.PickUpItemReport(item))

        # Only report true when we picked up the target item
        newInventoryAmt = self.inventory.amountOfItem(item.type)
        if newInventoryAmt > previousInventoryAmt:
            # Avoid stopMoving() function since it checks for action override
            self.__stopTurning()
            self.__stopWalking()
            self.__stopAttacking()
            self.__actionOverride = None
            return True
        return False

    def attackMob(self, mob):
        '''
        Direct this agent to attack a mob using the currently equipped item. Returns true if the agent successfully
        swung, false otherwise.

            Preconditions:
                - The given entity is a mob
                - The agent is looking at the mob
                - The agent is at the mob
        '''
        # Check action override
        if self.__shouldPerformActionOverride(self.attackMob):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # Preconditions
        if not self.__checkPreconditions(
            Mobs.All.isMember(mob.type),
            self.__isLookingAt(mob.position),
            self.__isAt(mob.position)):
            self.stopMoving()
            return False

        # Action
        oldMobsKilled = self.__mobsKilled()
        self.__startAttacking()
        self.stopMoving()
        time.sleep(0.7)
        newMobsKilled = self.__mobsKilled()

        if newMobsKilled > oldMobsKilled:
            self.__attackCleanup(mob)
        else:
            self.__logReports.append(LogUtils.AttackReport(mob, False, [], []))

        return True

    def __attackCleanup(self, mob):
        '''
        Perform additional cleanup work and logging as a result of an agent having killed the given mob.
        '''
        # Get any items that were immediately picked up
        itemsPickedUp, _ = self.inventory.sync()
        
        # Get any items that were dropped to the ground (register their IDs w/ Inventory class to preserve them)
        nearbyEntities = self.nearbyEntities()
        itemsDropped = [x for x in nearbyEntities if Items.All.isMember(x.type)]
        for item in itemsDropped:
            for i in range(0, item.quantity):
                Inventory.registerDropItem(item)
        
        # Create the log report for the attack
        self.__logReports.append(LogUtils.AttackReport(mob, True, itemsDropped, itemsPickedUp))

        # Trigger a log report for new closest mobs of this mob's type for all agents
        allAgents = list(Agent.allAgents.values())
        for agent in allAgents:
            if Mobs.All.isMember(mob.type):
                agent.closestMob()
            if Mobs.Peaceful.isMember(mob.type):
                agent.closestMob(Mobs.Peaceful)
            if Mobs.Hostile.isMember(mob.type):
                agent.closestMob(Mobs.Hostile)
            if Mobs.Food.isMember(mob.type):
                agent.closestMob(Mobs.Food)

    def craft(self, itemType, recipe):
        '''
        Craft an item of the given enumerated type using a list of RecipeItems. Returns true if successful, and
        false otherwise.

            Preconditions:
                - The agent has enough of each recipe item
        '''
        # Check for override
        if self.__shouldPerformActionOverride(self.craft):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # Preconditions
        hasAllItems = True
        for recipeItem in recipe:
            if self.inventory.amountOfItem(recipeItem) < recipeItem.quantity:
                hasAllItems = False
                break
        if not self.__checkPreconditions(hasAllItems):
            return False

        # Remove each recipe item from the inventory
        consumedItems = []
        for recipeItem in recipe:
            for i in range(0, recipeItem.quantity):
                consumedItems.append(self.inventory.removeItem(recipeItem.type))
        
        # Add the crafted item to the inventory
        craftedItem = self.inventory.addItem(itemType)

        # Action
        self.__host.sendCommand("craft {}".format(itemType.value))
        time.sleep(0.5)
        self.__logReports.append(LogUtils.CraftReport(craftedItem, recipeItem))
        return True

    def equip(self, itemType):
        '''
        Equip an item of the given enumerated type from this agent's inventory. Returns true if the agent successfully equips the item,
        false otherwise.

            Preconditions:
                - The agent has an item of the given type
        '''
        # Check action override
        if self.__shouldPerformActionOverride(self.equip):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # Preconditions
        if not self.__checkPreconditions(
            self.inventory.amountOfItem(itemType) >= 1):
            return False

        # Obtain a reference to the item we will equip
        inventoryItem = self.inventory.getItem(itemType)
        oldIndex = self.inventory.getItemIndex(itemType)
        if inventoryItem == None or oldIndex == None:
            return False

        # If item is already in the hotbar...
        if oldIndex < 9:
            self.__host.sendCommand("hotbar.{} 1".format(oldIndex + 1))
            self.__host.sendCommand("hotbar.{} 0".format(oldIndex + 1))
            self.__logReports.append(LogUtils.EquipReport(inventoryItem))
            return True

        # If there is an available hotbar slot...
        newIndex = self.inventory.nextUnusedHotbarIndex()
        if newIndex != None:
            self.__host.sendCommand("swapInventoryItems {} {}".format(newIndex, oldIndex))
            self.__host.sendCommand("hotbar.{} 1".format(newIndex + 1))
            self.__host.sendCommand("hotbar.{} 0".format(newIndex + 1))
            self.__logReports.append(LogUtils.EquipReport(inventoryItem))
            return True

        # Swap item in overflow w/ item in hotbar
        newIndex = self.inventory.equippedIndex()
        if newIndex != -1:
            self.__host.sendCommand("swapInventoryItems {} {}".format(newIndex, oldIndex))
            self.__host.sendCommand("hotbar.{} 1".format(newIndex + 1))
            self.__host.sendCommand("hotbar.{} 0".format(newIndex + 1))
            self.__logReports.append(LogUtils.EquipReport(inventoryItem))
            return True
        
        return False

    def giveItem(self, itemType, agent):
        '''
        Give an item of the given enumerated type to another agent. Returns true if successful, false otherwise.

            Preconditions:
                - The agent has an item of the given type
                - The agent has that item currently equipped
                - The agent is looking at the agent to give the item to
                - The agent is at the agent to give the item to
        '''
        # Check action override
        if self.__shouldPerformActionOverride(self.giveItem):
            return self.__actionOverride.function(*self.__actionOverride.args)

        # Stop moving before going any further...
        self.stopMoving()

        # Preconditions
        equippedItem = self.inventory.equippedItem()
        if not self.__checkPreconditions(
            equippedItem != None,
            equippedItem.type == itemType.value,
            self.__isLookingAt(agent.__position()),
            self.__isAt(agent.__position(), 2, GIVING_DISTANCE)
        ):
            return False

        # Record the exchange in each agent's inventory
        toGive = self.inventory.removeItem(itemType)
        agent.inventory.addItem(itemType, toGive.id)  # Preserve the ID

        # Action
        self.__throwItem()
        time.sleep(2.8)
        self.__logReports.append(LogUtils.GiveItemReport(toGive, agent))
        return True
