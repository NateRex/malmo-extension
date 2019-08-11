import copy
from enum import Enum
from malmoext.Utils import Item

class Inventory:
    '''
    A representation of an agent's inventory.
    '''
    __nextID = 1               # Global counter for uniquely identifying new items
    __dropItemRegistry = {}    # Map of item types to a list of known drop item IDs (used to preserve IDs between drop time & pickup time)

    @staticmethod
    def __getNextID():
        '''
        Get the next ID to be used for defining an item, and increment the counter.
        '''
        result = Inventory.__nextID
        Inventory.__nextID += 1
        return result

    @staticmethod
    def registerDropItem(item):
        '''
        THIS METHOD SHOULD ONLY BE USED INTERNALLY BY THE AGENT. Register a drop item so that its ID will be preserved once an agent goes
        to pick it up.
        '''
        if item.type not in Inventory.__dropItemRegistry:
            Inventory.__dropItemRegistry[item.type] = []
        Inventory.__dropItemRegistry[item.type].append(item)

    def __init__(self, agent):
        self.__agent = agent        # A reference to the agent whos inventory this represents
        self.__map = {}             # The map of item types to a list of items (FIFO)

    def asList(self):
        '''
        Returns a deep copy of this inventory as a list of items.
        '''
        result = []
        for itemList in list(self.__map.values()):
            result += copy.deepcopy(itemList)
        return result

    def asMap(self):
        '''
        Returns a deep copy of this inventory as a map of item IDs to the item each ID represents.
        '''
        result = {}
        allItems = [item for sublist in list(self.__map.values()) for item in sublist]
        for item in allItems:
            result[item.id] = item
        return result

    def sync(self):
        '''
        THIS METHOD SHOULD ONLY BE USED INTERNALLY BY THE AGENT. Synchronize this inventory object with the
        Malmo-generated inventory JSON data for an agent. Returns a 2-tuple containing a list of items added
        and a list of items removed.
        '''
        json = self.__agent.toJSON()["inventory"]
        areItemsLeft = len(json) != 0       # Whether or not there are items left to parse in the JSON object
        typesFound = []                     # A list of item types found in the JSON
        itemsAdded = []                     # Return list of items that were added
        itemsRemoved = []                   # Return list of items that were removed

        while (areItemsLeft):
            itemType = json[0]["type"]
            typesFound.append(itemType)
            itemQuantity = json[0]["quantity"]

            # Pull out all other items of this type from the JSON, adding to the quantity
            for i in range(1, len(json)):
                if json[i]["type"] == itemType:
                    itemQuantity += json[i]["quantity"]
            json = [item for item in json if item["type"] != itemType]

            # If key for this item type did not previously exist, create it
            if itemType not in self.__map:
                self.__map[itemType] = []

            # If the item quantity is greater than what we had previously, add items. Otherwise, remove items.
            previousQuantity = len(self.__map[itemType])
            if itemQuantity > previousQuantity:
                for i in range(previousQuantity, itemQuantity):
                    itemsAdded.append(self.addItem(itemType))
            elif itemQuantity < previousQuantity:
                for i in range(itemQuantity, previousQuantity):
                    if len(self.__map[itemType]) > 0:
                        itemsRemoved.append(self.__map[itemType].pop(0))
            
            if len(json) == 0:
                areItemsLeft = False

        # For any item types in the map that were not in the JSON, clear the corresponding list of IDs
        for itemType in self.__map.keys():
            if itemType not in typesFound:
                self.__map[itemType].clear()
        
        return (itemsAdded, itemsRemoved)

    def addItem(self, itemType, itemID=None):
        '''
        Manually add an item to this inventory given its item type. Optionally provide an ID for the
        item. If no ID is given, one will be generated. Returns the new item in the inventory.
        '''
        # If type was given as an Enum, convert it to string
        if isinstance(itemType, Enum):
            itemType = itemType.value

        # If ID was not given, search for a known one in the registry, or generate one from scratch
        if itemID == None:
            if itemType in Inventory.__dropItemRegistry and len(Inventory.__dropItemRegistry[itemType]) != 0:
                itemID = Inventory.__dropItemRegistry[itemType].pop(0).id
            else:    
                itemID = "{}{}".format(itemType, Inventory.__getNextID())

        newItem = Item(itemID, itemType)
        if itemType in self.__map:
            self.__map[itemType].append(newItem)
        else:
            self.__map[itemType] = [ newItem ]
        return newItem

    def removeItem(self, itemType):
        '''
        Manually remove an item from this inventory given its item type. Returns the item that was removed.
        If there were no items in this inventory of that type, returns None.
        '''
        # If type was given as an Enum, convert it to string
        if isinstance(itemType, Enum):
            itemType = itemType.value

        if itemType not in self.__map:
            return None
        elif len(self.__map[itemType]) == 0:
            return None
        else:
            return self.__map[itemType].pop(0)

    def getItem(self, itemType):
        '''
        Returns the 'topmost' item in this inventory for the given type. If no item for that type exists
        in the inventory, returns None.
        '''
        # If type was given as an Enum, convert it to string
        if isinstance(itemType, Enum):
            itemType = itemType.value

        if itemType not in self.__map:
            return None
        elif len(self.__map[itemType]) == 0:
            return None
        else:
            return self.__map[itemType][0]

    def getItemIndex(self, itemType):
        '''
        Returns the first inventory slot index found containing an item of the given type.
        Returns None if no item for that type exists in the inventory.
        '''
        # If type was given as an Enum, convert it to string
        if isinstance(itemType, Enum):
            itemType = itemType.value
        
        json = self.__agent.toJSON()["inventory"]
        for item in json:
            if item["type"] == itemType:
                return item["index"]
        return None
    
    def amountOfItem(self, itemType):
        '''
        Returns the amount of items for the given type in this inventory.
        '''
        # If type was given as an Enum, convert it to string
        if isinstance(itemType, Enum):
            itemType = itemType.value

        if itemType not in self.__map:
            return 0
        else:
            return len(self.__map[itemType])

    def nextUnusedHotbarIndex(self):
        '''
        Returns the inventory slot index of the first hotbar slot found to not be containing
        any items. Returns None if all of the hostbar slots are in use.
        '''
        json = self.__agent.toJSON()["inventory"]

        # Get all inventory slots in use
        slotsInUse = set()
        for item in json:
            if item["index"] < 9:
                slotsInUse.add(item["index"])
        
        # Find first hotbar slot (0-9) not in use, if any
        for i in range(0, 9):
            if i not in slotsInUse:
                return i
        return None

    def equippedItem(self):
        '''
        Returns the currently equipped item. Returns None if no item is equipped.
        '''
        json = self.__agent.toJSON()["inventory"]
        currentIndex = self.equippedIndex()

        for item in json:
            if item["index"] == currentIndex:
                return self.__map[item["type"]][0]
        return None

    def equippedIndex(self):
        '''
        Returns the inventory hotbar slot index currently selected by the agent.
        '''
        return self.__agent.toJSON()["currentItemIndex"]