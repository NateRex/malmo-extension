# ==============================================================================================
# This file contains functionality for building up a scenario to be ran as a Malmo Python
# mission. Note: The only class in this file that should be used directly by callers is the
# MissionBuilder
# ==============================================================================================
from malmoext.Utils import *
from malmoext.Agent import *

class EnvironmentBuilder:
    """
    Internal class used by the MissionBuilder for developing XML for the environment of a Malmo mission
    """

    def __init__(self):
        self.__generatorString = "3;7,2*3,2;1;"
        self.__decoratorsXML = ""
        self.__allowedMobs = set([])

    def getAllowedMobsList(self):
        """
        Returns a list of strings representing all mobs that are allowed to spawn.
        """
        return self.__allowedMobs

    def turnOnAnimalSpawning(self):
        """
        Allow for the natural spawning of animals & villagers.
        """
        self.__allowedMobs.add(Mobs.Peaceful.Pig.value)
        self.__allowedMobs.add(Mobs.Peaceful.Sheep.value)
        self.__allowedMobs.add(Mobs.Peaceful.Cow.value)
        self.__allowedMobs.add(Mobs.Peaceful.Chicken.value)
        self.__allowedMobs.add(Mobs.Peaceful.Ozelot.value)
        self.__allowedMobs.add(Mobs.Peaceful.Rabbit.value)
        self.__allowedMobs.add(Mobs.Peaceful.Villager.value)

    def turnOffAnimalSpawning(self):
        """
        Disallow the natural spawning of animals & villagers.
        """
        self.__allowedMobs.discard(Mobs.Peaceful.Pig.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Sheep.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Cow.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Chicken.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Ozelot.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Rabbit.value)
        self.__allowedMobs.discard(Mobs.Peaceful.Villager.value)

    def turnOnMonsterSpawning(self):
        """
        Allow for the natural spawning of monsters.
        """
        self.__allowedMobs.add(Mobs.Hostile.Spider.value)
        self.__allowedMobs.add(Mobs.Hostile.Zombie.value)
        self.__allowedMobs.add(Mobs.Hostile.Skeleton.value)
        self.__allowedMobs.add(Mobs.Hostile.Creeper.value)

    def turnOffMonsterSpawning(self):
        """
        Disallow for the natural spawning of monsters.
        """
        self.__allowedMobs.discard(Mobs.Hostile.Spider.value)
        self.__allowedMobs.discard(Mobs.Hostile.Zombie.value)
        self.__allowedMobs.discard(Mobs.Hostile.Skeleton.value)
        self.__allowedMobs.discard(Mobs.Hostile.Creeper.value)

    def addCube(self, blockType, point0, point1, variant = None):
        """
        Add a cuboid of a specific block type from lower-left-near corner point0 to upper-right-far corner point1.
        Each point is specified as a named Vector. If the block type specified is a mob spawner an additional mob type
        must be provided.
        """
        if (blockType == Blocks.Mob_spawner):
            if (variant != None):
                self.__allowedMobs.add(variant.value)   # Ensure the mob is allowed to spawn
                self.__decoratorsXML += '''<DrawCuboid x1="{}" y1="{}" z1="{}" x2="{}" y2="{}" z2="{}" type="{}" variant="{}"/>'''.format(point0.x, point0.y, point0.z, point1.x, point1.y, point1.z, blockType.value, variant.value)
        else:
            self.__decoratorsXML += '''<DrawCuboid x1="{}" y1="{}" z1="{}" x2="{}" y2="{}" z2="{}" type="{}"/>'''.format(point0.x, point0.y, point0.z, point1.x, point1.y, point1.z, blockType.value)

    def addLine(self, blockType, point0, point1, variant = None):
        """
        Add a line of a specific block type from point0 to point1, where each point is specified as a named Vector.
        If the block type specified is a mob spawner, an additional mob type must be provided.
        """
        if (blockType == Blocks.Mob_spawner):
            if (variant != None):
                self.__allowedMobs.add(variant.value)   # Ensure the mob is allowed to spawn
                self.__decoratorsXML += '''<DrawLine x1="{}" y1="{}" z1="{}" x2="{}" y2="{}" z2="{}" type="{}" variant="{}"/>'''.format(point0.x, point0.y, point0.z, point1.x, point1.y, point1.z, blockType.value, variant.value)
        else:
            self.__decoratorsXML += '''<DrawLine x1="{}" y1="{}" z1="{}" x2="{}" y2="{}" z2="{}" type="{}"/>'''.format(point0.x, point0.y, point0.z, point1.x, point1.y, point1.z, blockType.value)

    def addBlock(self, blockType, location, variant = None):
        """
        Add a block of a specific type at the location specified. The location should be given as a named Vector.
        If the block type specified is a mob spawner, an additional mob type must be provided.
        """
        if (blockType == Blocks.Mob_spawner):
            if (variant != None):
                self.__allowedMobs.add(variant.value)   # Ensure the mob is allowed to spawn
                self.__decoratorsXML += '''<DrawBlock x="{}" y="{}" z="{}" type="{}" variant="{}"/>'''.format(location.x, location.y, location.z, blockType.value, variant.value)
        else:
            self.__decoratorsXML += '''<DrawBlock x="{}" y="{}" z="{}" type="{}"/>'''.format(location.x, location.y, location.z, blockType.value)

    def addSphere(self, blockType, center, radius, variant = None):
        """
        Add a sphere of a specific block type, with a given radius and center. The center should be given as a named Vector.
        If the block type specified is a mob spawner, an additional mob type must be provided.
        """
        if (blockType == Blocks.Mob_spawner):
            if (variant != None):
                self.__allowedMobs.add(variant.value)   # Ensure the mob is allowed to spawn
                self.__decoratorsXML += '''<DrawSphere x="{}" y="{}" z="{}" radius="{}" type="{}" variant="{}"/>'''.format(center.x, center.y, center.z, radius, blockType.value, variant.value)
        else:
            self.__decoratorsXML += '''<DrawSphere x="{}" y="{}" z="{}" radius="{}" type="{}"/>'''.format(center.x, center.y, center.z, radius, blockType.value)

    def addDropItem(self, itemType, location):
        """
        Add a drop-item at a specific location specified as a named Vector.
        """
        self.__decoratorsXML += '''<DrawItem x="{}" y="{}" z="{}" type="{}"/>'''.format(location.x, location.y, location.z, itemType.value)

    def addMob(self, mobType, location):
        """
        Spawn a mob of a specific type at the named Vector location given.
        """
        self.__decoratorsXML += '''<DrawEntity x="{}" y="{}" z="{}" type="{}"/>'''.format(location.x, location.y, location.z, mobType.value)

    def finish(self):
        """
        Return the complete XML string for this set of decorations
        """
        return '''
        <FlatWorldGenerator forceReset="true" generatorString="{}"/>
        {}
        '''.format(self.__generatorString, "<DrawingDecorator>" + self.__decoratorsXML + "</DrawingDecorator>" if len(self.__decoratorsXML) > 0 else "")
    

class AgentBuilder:
    """
    Internal class used by the MissionBuilder for developing XML for an agent in a Malmo mission.
    """

    def __init__(self, name, startPosition, startDirection):
        self.name = name
        self.__position = startPosition
        self.__direction = startDirection.value
        self.__inventoryXML = ""
        self.__handlersXML = ""

    def setPosition(self, position):
        """
        Set the position of this agent in world-space given a named Vector.
        """
        self.__position = position

    def getPosition(self):
        """
        Returns the position of this agent in world-space as a named Vector.
        """
        return self.__position

    def setDirection(self, direction):
        """
        Set the direction for this agent to face (North, South, East, West).
        """
        self.__direction = direction.value

    def getDirection(self):
        """
        Returns the starting direction this agent is currently set to face as an integer value representing the yaw angle in degrees.
        """
        return self.__direction
    
    def addInventory(self, item, slot, quantity = 1):
        """
        Add an item to this agent's inventory at a designated item slot number, specifying a quantity.
        Each agent has 39 item slots, where 0-8 are the hotbar slots, 9-35 are the inventory slots, and 36-39 are the armor slots.
        """
        self.__inventoryXML += '''<InventoryItem slot="{}" type="{}" quantity="{}"/>'''.format(slot.value, item.value, quantity)


    def finish(self):
        """
        Returns the complete XML string for this agent being built.
        """
        return '''
        <AgentSection mode="Survival">
        <Name>{}</Name>
        <AgentStart>
            <Placement x="{}" y="{}" z="{}" yaw="{}"/>
            <Inventory>
            {}
            </Inventory>
        </AgentStart>
        <AgentHandlers>
        <ObservationFromFullStats/>
        <ObservationFromFullInventory flat="false"/>
        <InventoryCommands/>
        <SimpleCraftCommands/>
        <MissionQuitCommands/>
        <ContinuousMovementCommands/>
        <ObservationFromGrid>
            <Grid name="blockgrid">
                <min x="{}" y="{}" z="{}"/>
                <max x="{}" y="{}" z="{}"/>
            </Grid>
        </ObservationFromGrid>
        <ObservationFromNearbyEntities>
            <Range name="nearby_entities" xrange="25" yrange="2" zrange="25" />
        </ObservationFromNearbyEntities>
        {}
        </AgentHandlers>
        </AgentSection>'''.format(self.name, self.__position.x, self.__position.y, self.__position.z, self.__direction, self.__inventoryXML, -GRID_OBSERVATION_X_HALF_LEN, -GRID_OBSERVATION_Y_HALF_LEN, -GRID_OBSERVATION_Z_HALF_LEN, GRID_OBSERVATION_X_HALF_LEN, GRID_OBSERVATION_Y_HALF_LEN, GRID_OBSERVATION_Z_HALF_LEN, self.__handlersXML)


class MissionBuilder:
    '''
    Builder for creating a new Malmo mission.
    '''

    def __init__(self, description, timeLimit, timeOfDay=TimeOfDay.Noon):
        self.__description = description
        self.__timeLimit = timeLimit
        self.__timeOfDay = timeOfDay.value
        self.environment = EnvironmentBuilder()
        self.agents = {}

    def setDescription(self, description):
        """
        Set a description for this specific scenario.
        """
        self.__description = description

    def setTimeLimit(self, timeLimit):
        """
        Set a time limit for the mission to run.
        """
        self.__timeLimit = timeLimit

    def setTimeOfDay(self, timeOfDay):
        """
        Set the time of day for this scenario.
        """
        self.__timeOfDay = timeOfDay.value

    def addAgent(self, name, agentType=AgentType.Hardcoded, startPosition = Vector(0, 0, 0), startDirection = Direction.North):
        """
        Add a new agent to this scenario, giving it a name.
        Optionally specify a starting location as a named Vector, as well as a direction.
        Otherwise, the agent will start at the origin (0, 0, 0) facing north.
        """
        agent = Agent(name, agentType)
        self.agents[name] = AgentBuilder(agent.id, startPosition, startDirection)
        return agent

    def finish(self):
        """
        Returns the complete XML string for the current scenario.
        """
        mobsList = self.environment.getAllowedMobsList()
        mobsAllowed = ""
        for mob in mobsList:
            mobsAllowed = mobsAllowed + mob + " "
        returnValue = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no" ?>
        <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <About>
                <Summary>{}</Summary>
            </About>

            <ServerSection>
                    <ServerInitialConditions>
                        <Time>
                            <StartTime>{}</StartTime>
                            <AllowPassageOfTime>false</AllowPassageOfTime>
                        </Time>
                        <Weather>clear</Weather>
                        <AllowSpawning>{}</AllowSpawning>
                        <AllowedMobs>{}</AllowedMobs>
                    </ServerInitialConditions>
            
                <ServerHandlers>
                        {}
                        <ServerQuitFromTimeUp timeLimitMs="{}" description="out_of_time"/>
                    <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
            </ServerSection>
            '''.format(self.__description, self.__timeOfDay, "false" if len(mobsList) == 0 else "true", mobsAllowed, self.environment.finish(), self.__timeLimit)
        for agent in self.agents.values():
            returnValue += agent.finish()
        return returnValue + "</Mission>"