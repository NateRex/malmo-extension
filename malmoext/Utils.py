# ==============================================================================================
# This file contains constants/enumerated types, utility classes, and functionality relating to
# supporting companion agent actions.
# ==============================================================================================
import math
from collections import namedtuple
from enum import Enum

# ==============================================================================================
# Globals
# ==============================================================================================

# Inventory
NUMBER_OF_INVENTORY_SLOTS = 40

# Tolerances for completing continuous actions
STRIKING_DISTANCE = 3
GIVING_DISTANCE = 4.5
PICK_UP_ITEM_LOCKDOWN_DISTANCE = 7

# The size of the observation grid for an agent, as well as how many blocks are in each axis
GRID_OBSERVATION_SIZE = 605
GRID_OBSERVATION_X_LEN = 11
GRID_OBSERVATION_Y_LEN = 5
GRID_OBSERVATION_Z_LEN = 11
GRID_OBSERVATION_X_HALF_LEN = int(GRID_OBSERVATION_X_LEN / 2)
GRID_OBSERVATION_Y_HALF_LEN = int(GRID_OBSERVATION_Y_LEN / 2)
GRID_OBSERVATION_Z_HALF_LEN = int(GRID_OBSERVATION_Z_LEN / 2)

# ==============================================================================================
# Named tuples
# ==============================================================================================

Vector = namedtuple("Vector", "x y z")                               # Vector/Position holding x, y, and z values
Entity = namedtuple("EntityInfo", "id type position quantity")       # Information for an entity observed by an agent
Item = namedtuple("Item", "id type")                                 # An item with an associated id
RecipeItem = namedtuple("RecipeItem", "type quantity")               # An item that is part of a recipe for crafting

# ==============================================================================================
# Functions
# ==============================================================================================

def isEntityInfoNamedTuple(x):
    t = type(x)
    b = t.__bases__
    if len(b) != 1 or b[0] != tuple: return False
    f = getattr(t, '_fields', None)
    if not isinstance(f, tuple): return False
    return all(type(n)==str for n in f)

def stringToBlockEnum(string):
    """
    Converts a plain string to an enum object from BlockType. If it does not exist, returns None.
    """
    for block in Blocks:
        if block.value == string:
            return block
    return None

def stringToItemEnum(string):
    """
    Converts a plain string to an enum object from ItemType. If it does not exist, returns None.
    """
    for item in Items.All:
        if item.value == string:
            return item
    return None

def numerifyId(string):
    """
    Given a string containing hexadecimal values that make up an id, return a new id that contains all digits and no letters.
    """
    for i in range(0, len(string)):
        if string[i] < "0" or string[i] > "9":
            string = string[:i] + "{}".format(ord(string[i]) % 10) + string[i + 1:]
    return string

# ==============================================================================================
# Classes
# ==============================================================================================

class MathUtils:
    '''
    A collection of static functions for working with 3D vectors.
    '''
    PI_OVER_TWO = math.pi / 2
    THREE_PI_OVER_TWO = 3 * math.pi / 2
    TWO_PI = math.pi * 2

    @staticmethod
    def valuesAreEqual(a, b, tol = 1.0e-14):
        """
        Returns true if two numeric values are equal. Optionally supply a tolerance.
        """
        diff = a - b
        if diff < 0:
            diff = diff * -1
        if diff <= tol:
            return True
        else:
            return False

    @staticmethod
    def affineTransformation(value, x, y, a, b):
        """
        Transform a value from the range [x, y] to the range [a, b] and return it.
        """
        return (value - x) * (b - a) / (y - x) + a

    @staticmethod
    def distanceBetweenPoints(pointA, pointB):
        """
        Returns the distance between two points, where each point is specified as a named Vector.
        """
        return math.sqrt(math.pow(pointB.x - pointA.x, 2) + math.pow(pointB.y - pointA.y, 2) + math.pow(pointB.z - pointA.z, 2))

    @staticmethod
    def distanceBetweenPointsXZ(pointA, pointB):
        """
        Returns the distance between two points, taking only the x-axis and z-axis into account.
        Each point should be specified as a named Vector.
        """
        return math.sqrt(math.pow(pointB.x - pointA.x, 2) + math.pow(pointB.z - pointA.z, 2))

    @staticmethod
    def vectorFromPoints(pointA, pointB):
        """
        Returns a Vector from point A to point B.
        """
        return Vector(pointB.x - pointA.x, pointB.y - pointA.y, pointB.z - pointA.z)

    @staticmethod
    def vectorMagnitude(vector):
        """
        Returns the magnitude of a 'Vector'.
        """
        return math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z)

    @staticmethod
    def normalizeVector(vector):
        """
        Normalize a Vector into the range (-1, -1, -1) to (1, 1, 1) and return it.
        If the given Vector is the zero vector, returns the zero vector.
        """
        mag = MathUtils.vectorMagnitude(vector)
        if MathUtils.valuesAreEqual(mag, 0, 1.0e-14):
            return Vector(0, 0, 0)
        else:
            return Vector(vector.x / mag, vector.y / mag, vector.z / mag)

    @staticmethod
    def dotProduct(vectorA, vectorB):
        """
        Returns the dot product of a Vector with another Vector.
        """
        return vectorA.x * vectorB.x + vectorA.y * vectorB.y + vectorA.z * vectorB.z

    @staticmethod
    def isZeroVector(vector):
        """
        Returns true if the Vector given is equal to the zero vector.
        """
        if vector.x == 0 and vector.y == 0 and vector.z == 0:
            return True
        return False
    
    @staticmethod
    def substractVectors(vectorA, vectorB):
        """
        Returns the vector A - B.
        """
        return Vector(vectorA.x - vectorB.x, vectorA.y - vectorB.y, vectorA.z - vectorB.z)

class LogUtils:
    '''
    A collection of named tuples to make conveying information from the Agent class to the Logger easier.
    '''
    ClosestMobReport   = namedtuple("ClosestMobReport", "variant mob")
    ClosestItemReport  = namedtuple("ClosestItemReport", "variant item")
    LookAtReport       = namedtuple("LookAtReport", "entity")
    MoveToReport       = namedtuple("MoveToReport", "entity")
    PickUpItemReport   = namedtuple("PickUpItemReport", "item")
    CraftReport        = namedtuple("CraftReport", "itemCrafted itemsUsed")
    AttackReport       = namedtuple("AttackReport", "mob didKill itemsDropped itemsPickedUp")
    EquipReport        = namedtuple("EquipReport", "item")
    GiveItemReport     = namedtuple("GiveItemReport", "item agent")

# ==============================================================================================
# Enumerated Types
# ==============================================================================================

class AgentType(Enum):
    '''
    A type of Agent.
    '''
    Hardcoded = "hardcoded"
    Trained = "trained"
    Human = "human"

class Blocks(Enum):
    '''
    A type of Minecraft block.
    '''
    Air = "air"
    Stone = "stone"
    Grass = "grass"
    Dirt = "dirt"
    Cobblestone = "cobblestone"
    Planks = "planks"
    Sapling = "sapling"
    Bedrock = "bedrock"
    Flowing_water = "flowing_water"
    Water = "water"
    Flowing_lava = "flowing_lava"
    Lava = "lava"
    Sand = "sand"
    Gravel = "gravel"
    Gold_ore = "gold_ore"
    Iron_ore = "iron_ore"
    Coal_ore = "coal_ore"
    Log = "log"
    Leaves = "leaves"
    Sponge = "sponge"
    Glass = "glass"
    Lapis_ore = "lapis_ore"
    Lapis_block = "lapis_block"
    Dispenser = "dispenser"
    Sandstone = "sandstone"
    Noteblock = "noteblock"
    Bed = "bed"
    Golden_rail = "golden_rail"
    Detector_rail = "detector_rail"
    Sticky_piston = "sticky_piston"
    Web = "web"
    Tallgrass = "tallgrass"
    Deadbush = "deadbush"
    Piston = "piston"
    Piston_head = "piston_head"
    Wool = "wool"
    Piston_extension = "piston_extension"
    Yellow_flower = "yellow_flower"
    Red_flower = "red_flower"
    Brown_mushroom = "brown_mushroom"
    Red_mushroom = "red_mushroom"
    Gold_block = "gold_block"
    Iron_block = "iron_block"
    Double_stone_slab = "double_stone_slab"
    Stone_slab = "stone_slab"
    Brick_block = "brick_block"
    Tnt = "tnt"
    Bookshelf = "bookshelf"
    Mossy_cobblestone = "mossy_cobblestone"
    Obsidian = "obsidian"
    Torch = "torch"
    Fire = "fire"
    Mob_spawner = "mob_spawner"
    Oak_stairs = "oak_stairs"
    Chest = "chest"
    Redstone_wire = "redstone_wire"
    Diamond_ore = "diamond_ore"
    Diamond_block = "diamond_block"
    Crafting_table = "crafting_table"
    Wheat = "wheat"
    Farmland = "farmland"
    Furnace = "furnace"
    Lit_furnace = "lit_furnace"
    Standing_sign = "standing_sign"
    Wooden_door = "wooden_door"
    Ladder = "ladder"
    Rail = "rail"
    Stone_stairs = "stone_stairs"
    Wall_sign = "wall_sign"
    Lever = "lever"
    Stone_pressure_plate = "stone_pressure_plate"
    Iron_door = "iron_door"
    Wooden_pressure_plate = "wooden_pressure_plate"
    Redstone_ore = "redstone_ore"
    Lit_redstone_ore = "lit_redstone_ore"
    Unlit_redstone_torch = "unlit_redstone_torch"
    Redstone_torch = "redstone_torch"
    Stone_button = "stone_button"
    Snow_layer = "snow_layer"
    Ice = "ice"
    Snow = "snow"
    Cactus = "cactus"
    Clay = "clay"
    Reeds = "reeds"
    Jukebox = "jukebox"
    Fence = "fence"
    Pumpkin = "pumpkin"
    Netherrack = "netherrack"
    Soul_sand = "soul_sand"
    Glowstone = "glowstone"
    Portal = "portal"
    Lit_pumpkin = "lit_pumpkin"
    Cake = "cake"
    Unpowered_repeater = "unpowered_repeater"
    Powered_repeater = "powered_repeater"
    Stained_glass = "stained_glass"
    Trapdoor = "trapdoor"
    Monster_egg = "monster_egg"
    Stonebrick = "stonebrick"
    Brown_mushroom_block = "brown_mushroom_block"
    Red_mushroom_block = "red_mushroom_block"
    Iron_bars = "iron_bars"
    Glass_pane = "glass_pane"
    Melon_block = "melon_block"
    Pumpkin_stem = "pumpkin_stem"
    Melon_stem = "melon_stem"
    Vine = "vine"
    Fence_gate = "fence_gate"
    Brick_stairs = "brick_stairs"
    Stone_brick_stairs = "stone_brick_stairs"
    Mycelium = "mycelium"
    Waterlily = "waterlily"
    Nether_brick = "nether_brick"
    Nether_brick_fence = "nether_brick_fence"
    Nether_brick_stairs = "nether_brick_stairs"
    Nether_wart = "nether_wart"
    Enchanting_table = "enchanting_table"
    Brewing_stand = "brewing_stand"
    Cauldron = "cauldron"
    End_portal = "end_portal"
    End_portal_frame = "end_portal_frame"
    End_stone = "end_stone"
    Dragon_egg = "dragon_egg"
    Redstone_lamp = "redstone_lamp"
    Lit_redstone_lamp = "lit_redstone_lamp"
    Double_wooden_slab = "double_wooden_slab"
    Wooden_slab = "wooden_slab"
    Cocoa = "cocoa"
    Sandstone_stairs = "sandstone_stairs"
    Emerald_ore = "emerald_ore"
    Ender_chest = "ender_chest"
    Tripwire_hook = "tripwire_hook"
    Tripwire = "tripwire"
    Emerald_block = "emerald_block"
    Spruce_stairs = "spruce_stairs"
    Birch_stairs = "birch_stairs"
    Jungle_stairs = "jungle_stairs"
    Command_block = "command_block"
    Beacon = "beacon"
    Cobblestone_wall = "cobblestone_wall"
    Flower_pot = "flower_pot"
    Carrots = "carrots"
    Potatoes = "potatoes"
    Wooden_button = "wooden_button"
    Skull = "skull"
    Anvil = "anvil"
    Trapped_chest = "trapped_chest"
    Light_weighted_pressure_plate = "light_weighted_pressure_plate"
    Heavy_weighted_pressure_plate = "heavy_weighted_pressure_plate"
    Unpowered_comparator = "unpowered_comparator"
    Powered_comparator = "powered_comparator"
    Daylight_detector = "daylight_detector"
    Redstone_block = "redstone_block"
    Quartz_ore = "quartz_ore"
    Hopper = "hopper"
    Quartz_block = "quartz_block"
    Quartz_stairs = "quartz_stairs"
    Activator_rail = "activator_rail"
    Dropper = "dropper"
    Stained_hardened_clay = "stained_hardened_clay"
    Stained_glass_pane = "stained_glass_pane"
    Leaves2 = "leaves2"
    Log2 = "log2"
    Acacia_stairs = "acacia_stairs"
    Dark_oak_stairs = "dark_oak_stairs"
    Slime = "slime"
    Barrier = "barrier"
    Iron_trapdoor = "iron_trapdoor"
    Prismarine = "prismarine"
    Sea_lantern = "sea_lantern"
    Hay_block = "hay_block"
    Carpet = "carpet"
    Hardened_clay = "hardened_clay"
    Coal_block = "coal_block"
    Packed_ice = "packed_ice"
    Double_plant = "double_plant"
    Standing_banner = "standing_banner"
    Wall_banner = "wall_banner"
    Daylight_detector_inverted = "daylight_detector_inverted"
    Red_sandstone = "red_sandstone"
    Red_sandstone_stairs = "red_sandstone_stairs"
    Double_stone_slab2 = "double_stone_slab2"
    Stone_slab2 = "stone_slab2"
    Spruce_fence_gate = "spruce_fence_gate"
    Birch_fence_gate = "birch_fence_gate"
    Jungle_fence_gate = "jungle_fence_gate"
    Dark_oak_fence_gate = "dark_oak_fence_gate"
    Acacia_fence_gate = "acacia_fence_gate"
    Spruce_fence = "spruce_fence"
    Birch_fence = "birch_fence"
    Jungle_fence = "jungle_fence"
    Dark_oak_fence = "dark_oak_fence"
    Acacia_fence = "acacia_fence"
    Spruce_door = "spruce_door"
    Birch_door = "birch_door"
    Jungle_door = "jungle_door"
    Acacia_door = "acacia_door"
    Dark_oak_door = "dark_oak_door"
    End_rod = "end_rod"
    Chorus_plant = "chorus_plant"
    Chorus_flower = "chorus_flower"
    Purpur_block = "purpur_block"
    Purpur_pillar = "purpur_pillar"
    Purpur_stairs = "purpur_stairs"
    Purpur_double_slab = "purpur_double_slab"
    Purpur_slab = "purpur_slab"
    End_bricks = "end_bricks"
    Beetroots = "beetroots"
    Grass_path = "grass_path"
    End_gateway = "end_gateway"
    Repeating_command_block = "repeating_command_block"
    Chain_command_block = "chain_command_block"
    Frosted_ice = "frosted_ice"
    Magma = "magma"
    Nether_wart_block = "nether_wart_block"
    Red_nether_brick = "red_nether_brick"
    Bone_block = "bone_block"
    Structure_void = "structure_void"
    Observer = "observer"
    White_shulker_box = "white_shulker_box"
    Orange_shulker_box = "orange_shulker_box"
    Magenta_shulker_box = "magenta_shulker_box"
    Light_blue_shulker_box = "light_blue_shulker_box"
    Yellow_shulker_box = "yellow_shulker_box"
    Lime_shulker_box = "lime_shulker_box"
    Pink_shulker_box = "pink_shulker_box"
    Gray_shulker_box = "gray_shulker_box"
    Silver_shulker_box = "silver_shulker_box"
    Cyan_shulker_box = "cyan_shulker_box"
    Purple_shulker_box = "purple_shulker_box"
    Blue_shulker_box = "blue_shulker_box"
    Brown_shulker_box = "brown_shulker_box"
    Green_shulker_box = "green_shulker_box"
    Red_shulker_box = "red_shulker_box"
    Black_shulker_box = "black_shulker_box"
    Structure_block = "structure_block"

    @classmethod
    def isMember(cls, string):
        '''
        Returns true if the given string is a member of Blocks
        '''
        return string in cls._value2member_map_

class Items:
    '''
    A type of Minecraft item.
    '''

    class All(Enum):
        '''
        A type of Minecraft item.
        '''
        iron_shovel = "iron_shovel"
        iron_pickaxe = "iron_pickaxe"
        iron_axe = "iron_axe"
        flint_and_steel = "flint_and_steel"
        apple = "apple"
        bow = "bow"
        arrow = "arrow"
        coal = "coal"
        diamond = "diamond"
        iron_ingot = "iron_ingot"
        gold_ingot = "gold_ingot"
        iron_sword = "iron_sword"
        wooden_sword = "wooden_sword"
        wooden_shovel = "wooden_shovel"
        wooden_pickaxe = "wooden_pickaxe"
        wooden_axe = "wooden_axe"
        stone_sword = "stone_sword"
        stone_shovel = "stone_shovel"
        stone_pickaxe = "stone_pickaxe"
        stone_axe = "stone_axe"
        diamond_sword = "diamond_sword"
        diamond_shovel = "diamond_shovel"
        diamond_pickaxe = "diamond_pickaxe"
        diamond_axe = "diamond_axe"
        stick = "stick"
        bowl = "bowl"
        mushroom_stew = "mushroom_stew"
        golden_sword = "golden_sword"
        golden_shovel = "golden_shovel"
        golden_pickaxe = "golden_pickaxe"
        golden_axe = "golden_axe"
        string = "string"
        feather = "feather"
        gunpowder = "gunpowder"
        wooden_hoe = "wooden_hoe"
        stone_hoe = "stone_hoe"
        iron_hoe = "iron_hoe"
        diamond_hoe = "diamond_hoe"
        golden_hoe = "golden_hoe"
        wheat_seeds = "wheat_seeds"
        wheat = "wheat"
        bread = "bread"
        leather_helmet = "leather_helmet"
        leather_chestplate = "leather_chestplate"
        leather_leggings = "leather_leggings"
        leather_boots = "leather_boots"
        chainmail_helmet = "chainmail_helmet"
        chainmail_chestplate = "chainmail_chestplate"
        chainmail_leggings = "chainmail_leggings"
        chainmail_boots = "chainmail_boots"
        iron_helmet = "iron_helmet"
        iron_chestplate = "iron_chestplate"
        iron_leggings = "iron_leggings"
        iron_boots = "iron_boots"
        diamond_helmet = "diamond_helmet"
        diamond_chestplate = "diamond_chestplate"
        diamond_leggings = "diamond_leggings"
        diamond_boots = "diamond_boots"
        golden_helmet = "golden_helmet"
        golden_chestplate = "golden_chestplate"
        golden_leggings = "golden_leggings"
        golden_boots = "golden_boots"
        flint = "flint"
        porkchop = "porkchop"
        cooked_porkchop = "cooked_porkchop"
        painting = "painting"
        golden_apple = "golden_apple"
        sign = "sign"
        wooden_door = "wooden_door"
        bucket = "bucket"
        water_bucket = "water_bucket"
        lava_bucket = "lava_bucket"
        minecart = "minecart"
        saddle = "saddle"
        iron_door = "iron_door"
        redstone = "redstone"
        snowball = "snowball"
        boat = "boat"
        leather = "leather"
        milk_bucket = "milk_bucket"
        brick = "brick"
        clay_ball = "clay_ball"
        reeds = "reeds"
        paper = "paper"
        book = "book"
        slime_ball = "slime_ball"
        chest_minecart = "chest_minecart"
        furnace_minecart = "furnace_minecart"
        egg = "egg"
        compass = "compass"
        fishing_rod = "fishing_rod"
        clock = "clock"
        glowstone_dust = "glowstone_dust"
        fish = "fish"
        cooked_fish = "cooked_fish"
        dye = "dye"
        bone = "bone"
        sugar = "sugar"
        cake = "cake"
        bed = "bed"
        repeater = "repeater"
        cookie = "cookie"
        filled_map = "filled_map"
        shears = "shears"
        melon = "melon"
        pumpkin_seeds = "pumpkin_seeds"
        melon_seeds = "melon_seeds"
        beef = "beef"
        cooked_beef = "cooked_beef"
        chicken = "chicken"
        cooked_chicken = "cooked_chicken"
        rotten_flesh = "rotten_flesh"
        ender_pearl = "ender_pearl"
        blaze_rod = "blaze_rod"
        ghast_tear = "ghast_tear"
        gold_nugget = "gold_nugget"
        nether_wart = "nether_wart"
        potion = "potion"
        glass_bottle = "glass_bottle"
        spider_eye = "spider_eye"
        fermented_spider_eye = "fermented_spider_eye"
        blaze_powder = "blaze_powder"
        magma_cream = "magma_cream"
        brewing_stand = "brewing_stand"
        cauldron = "cauldron"
        ender_eye = "ender_eye"
        speckled_melon = "speckled_melon"
        spawn_egg = "spawn_egg"
        experience_bottle = "experience_bottle"
        fire_charge = "fire_charge"
        writable_book = "writable_book"
        written_book = "written_book"
        emerald = "emerald"
        item_frame = "item_frame"
        flower_pot = "flower_pot"
        carrot = "carrot"
        potato = "potato"
        baked_potato = "baked_potato"
        poisonous_potato = "poisonous_potato"
        map = "map"
        golden_carrot = "golden_carrot"
        skull = "skull"
        carrot_on_a_stick = "carrot_on_a_stick"
        nether_star = "nether_star"
        pumpkin_pie = "pumpkin_pie"
        fireworks = "fireworks"
        firework_charge = "firework_charge"
        enchanted_book = "enchanted_book"
        comparator = "comparator"
        netherbrick = "netherbrick"
        quartz = "quartz"
        tnt_minecart = "tnt_minecart"
        hopper_minecart = "hopper_minecart"
        prismarine_shard = "prismarine_shard"
        prismarine_crystals = "prismarine_crystals"
        rabbit = "rabbit"
        cooked_rabbit = "cooked_rabbit"
        rabbit_stew = "rabbit_stew"
        rabbit_foot = "rabbit_foot"
        rabbit_hide = "rabbit_hide"
        armor_stand = "armor_stand"
        iron_horse_armor = "iron_horse_armor"
        golden_horse_armor = "golden_horse_armor"
        diamond_horse_armor = "diamond_horse_armor"
        lead = "lead"
        name_tag = "name_tag"
        command_block_minecart = "command_block_minecart"
        mutton = "mutton"
        cooked_mutton = "cooked_mutton"
        banner = "banner"
        spruce_door = "spruce_door"
        birch_door = "birch_door"
        jungle_door = "jungle_door"
        acacia_door = "acacia_door"
        dark_oak_door = "dark_oak_door"
        chorus_fruit = "chorus_fruit"
        chorus_fruit_popped = "chorus_fruit_popped"
        beetroot = "beetroot"
        beetroot_seeds = "beetroot_seeds"
        beetroot_soup = "beetroot_soup"
        dragon_breath = "dragon_breath"
        splash_potion = "splash_potion"
        spectral_arrow = "spectral_arrow"
        tipped_arrow = "tipped_arrow"
        lingering_potion = "lingering_potion"
        shield = "shield"
        elytra = "elytra"
        spruce_boat = "spruce_boat"
        birch_boat = "birch_boat"
        jungle_boat = "jungle_boat"
        acacia_boat = "acacia_boat"
        dark_oak_boat = "dark_oak_boat"
        totem_of_undying = "totem_of_undying"
        shulker_shell = "shulker_shell"
        iron_nugget = "iron_nugget"
        record_13 = "record_13"
        record_cat = "record_cat"
        record_blocks = "record_blocks"
        record_chirp = "record_chirp"
        record_far = "record_far"
        record_mall = "record_mall"
        record_mellohi = "record_mellohi"
        record_stal = "record_stal"
        record_strad = "record_strad"
        record_ward = "record_ward"
        record_11 = "record_11"
        record_wait = "record_wait"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Items.All
            '''
            return string in cls._value2member_map_

    class Food(Enum):
        '''
        A type of Minecraft food item.
        '''
        apple = "apple"
        mushroom_stew = "mushroom_stew"
        bread = "bread"
        porkchop = "porkchop"
        cooked_porkchop = "cooked_porkchop"
        golden_apple = "golden_apple"
        fish = "fish"
        cooked_fish = "cooked_fish"
        cake = "cake"
        cookie = "cookie"
        beef = "beef"
        cooked_beef = "cooked_beef"
        chicken = "chicken"
        cooked_chicken = "cooked_chicken"        
        carrot = "carrot"
        potato = "potato"
        baked_potato = "baked_potato"
        golden_carrot = "golden_carrot"
        pumpkin_pie = "pumpkin_pie"
        rabbit = "rabbit"
        cooked_rabbit = "cooked_rabbit"
        rabbit_stew = "rabbit_stew"
        mutton = "mutton"
        cooked_mutton = "cooked_mutton"
        beetroot_soup = "beetroot_soup"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Items.Food
            '''
            return string in cls._value2member_map_

class InventorySlot:
    '''
    A Minecraft inventory slot.
    '''
    class HotBar(Enum):
        '''
        A Minecraft inventory slot along the hotbar.
        '''
        _0 = 0
        _1 = 1
        _2 = 2
        _3 = 3
        _4 = 4
        _5 = 5
        _6 = 6
        _7 = 7
        _8 = 8

    class Main(Enum):
        '''
        A Minecraft inventory slot in an agent's main inventory.
        '''
        _9 = 9
        _10 = 10
        _11 = 11
        _12 = 12
        _13 = 13
        _14 = 14
        _15 = 15
        _16 = 16
        _17 = 17
        _18 = 18
        _19 = 19
        _20 = 20
        _21 = 21
        _22 = 22
        _23 = 23
        _24 = 24
        _25 = 25
        _26 = 26
        _27 = 27
        _28 = 28
        _29 = 29
        _30 = 30
        _31 = 31
        _32 = 32
        _33 = 33
        _34 = 34
        _35 = 35
    
    class Armor(Enum):
        '''
        A Minecraft inventory slot that defines places to equip armor.
        '''
        Boots = 36
        Leggings = 37
        Chestplate = 38
        Helmet = 39

class Direction(Enum):
    '''
    A compass direction in Minecraft.
    '''
    North = 180
    East = -90
    South = 0
    West = 90

class Mobs:
    '''
    A type of Minecraft mob.
    '''
    class All(Enum):
        '''
        A type of Minecraft mob.
        '''
        Blaze = "Blaze"
        Creeper = "Creeper"
        ElderGuardian = "ElderGuardian"
        Endermite = "Endermite"
        Ghast = "Ghast"
        Guardian = "Guardian"
        Husk = "Husk"
        EvocationIllager = "EvocationIllager"
        Shulker = "Shulker"
        Silverfish = "Silverfish"
        Skeleton = "Skeleton"
        SkeletonHorse = "SkeletonHorse"
        Slime = "Slime"
        EnderDragon = "EnderDragon"
        WitherBoss = "WitherBoss"
        Spider = "Spider"
        Stray = "Stray"
        Vex = "Vex"
        VindicationIllager = "VindicationIllager"
        Witch = "Witch"
        WitherSkeleton = "WitherSkeleton"
        ZombieVillager = "ZombieVillager"
        Zombie = "Zombie"
        ZombieHorse = "ZombieHorse"
        Giant = "Giant"
        PigZombie = "PigZombie"
        Enderman = "Enderman"
        CaveSpider = "CaveSpider"
        LavaSlime = "LavaSlime"
        Bat = "Bat"
        Donkey = "Donkey"
        Mule = "Mule"
        Pig = "Pig"
        Sheep = "Sheep"
        Cow = "Cow"
        Chicken = "Chicken"
        Squid = "Squid"
        Wolf = "Wolf"
        MushroomCow = "MushroomCow"
        SnowMan = "SnowMan"
        Ozelot = "Ozelot"
        VillagerGolem = "VillagerGolem"
        Horse = "Horse"
        Rabbit = "Rabbit"
        PolarBear = "PolarBear"
        Llama = "Llama"
        Villager = "Villager"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Mobs.All
            '''
            return string in cls._value2member_map_

    class Hostile(Enum):
        '''
        A type of hostile Minecraft mob.
        '''
        Blaze = "Blaze"
        Creeper = "Creeper"
        ElderGuardian = "ElderGuardian"
        Endermite = "Endermite"
        Ghast = "Ghast"
        Guardian = "Guardian"
        Husk = "Husk"
        EvocationIllager = "EvocationIllager"
        Shulker = "Shulker"
        Silverfish = "Silverfish"
        Skeleton = "Skeleton"
        SkeletonHorse = "SkeletonHorse"
        Slime = "Slime"
        EnderDragon = "EnderDragon"
        WitherBoss = "WitherBoss"
        Spider = "Spider"
        Stray = "Stray"
        Vex = "Vex"
        VindicationIllager = "VindicationIllager"
        Witch = "Witch"
        WitherSkeleton = "WitherSkeleton"
        ZombieVillager = "ZombieVillager"
        Zombie = "Zombie"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Mobs.Hostile
            '''
            return string in cls._value2member_map_

    class Peaceful(Enum):
        '''
        A type of peaceful Minecraft mob.
        '''
        ZombieHorse = "ZombieHorse"
        Giant = "Giant"
        PigZombie = "PigZombie"
        Enderman = "Enderman"
        CaveSpider = "CaveSpider"
        LavaSlime = "LavaSlime"
        Bat = "Bat"
        Donkey = "Donkey"
        Mule = "Mule"
        Pig = "Pig"
        Sheep = "Sheep"
        Cow = "Cow"
        Chicken = "Chicken"
        Squid = "Squid"
        Wolf = "Wolf"
        MushroomCow = "MushroomCow"
        SnowMan = "SnowMan"
        Ozelot = "Ozelot"
        VillagerGolem = "VillagerGolem"
        Horse = "Horse"
        Rabbit = "Rabbit"
        PolarBear = "PolarBear"
        Llama = "Llama"
        Villager = "Villager"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Mobs.Peaceful
            '''
            return string in cls._value2member_map_

    class Food(Enum):
        '''
        A type of Minecraft mob that potentially drops food when killed.
        '''
        Pig = "Pig"
        Sheep = "Sheep"
        Cow = "Cow"
        Chicken = "Chicken"
        MushroomCow = "MushroomCow"
        Rabbit = "Rabbit"

        @classmethod
        def isMember(cls, string):
            '''
            Returns true if the given string is a member of Mobs.Food
            '''
            return string in cls._value2member_map_
        
class TimeOfDay(Enum):
    '''
    A time of day in Minecraft.
    '''
    Dawn = 0
    Noon = 6000
    Sunset = 12000
    Midnight = 18000