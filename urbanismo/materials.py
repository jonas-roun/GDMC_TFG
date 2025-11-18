import random
from typing import List

from gdpc import Block

buildingBricks = ["bricks","mud_bricks","red_nether_bricks","resin_bricks",
                  "nether_bricks","polished_blackstone_bricks","red_nether_bricks",
                  "stone_bricks","tuff_bricks","deepslate_bricks","end_stone_bricks",
                  "quartz_bricks", "deepslate_tiles"] #que hacer con ladrillos prismarina
#prismarine_bricks->roofing

colours = ["white", "light_gray", "gray", "black", "brown", "red", "orange","yellow","lime",
           "green","cyan", "light_blue","blue","purple","magenta","pink"]
coloured_blocks = ["concrete", "terracotta"]

woods = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak",
              "mangrove", "cherry", "pale_oak", "bamboo", "crimson", "warped"]
wood_blocks = ["planks", "door", "fence", "log"]
wall_blocks = ["cobblestone","stone_brick","granite","diorite", "andesite", "cobbled_deepslate", "polished_deepslate", "deepslate_brick", "deepslate_tile", "tuff", "polished_tuff", "tuff_brick", "brick", "mud_brick", "resin_brick", "sandstone", "red_sandstone", "prismarine", "nether_brick", "red_nether_brick", "blackstone", "polished_blackstone", "polished_blackstone_brick", "end_stone_brick"]

fence_blocks = ["fence", "wall"]

wallBlocks = ["concrete", "cobblestone", "terracotta"] +buildingBricks

column_blocks = ["log", "quartz_pillar", "polished_basalt"]


door_materials = woods + ["waxed_copper", "waxed_oxidized_copper"]

#mossy_blocks = ["stone_bricks", "cobblestone"]
#blocks with a cracked variant
cracked_blocks = ["stone_bricks", "polished_blackstone_bricks", "deepslate_bricks", "deepslate_tiles","nether_bricks"]

#blocks that dont exist on their own, but are used because of their colour variants or similar
block_black_list = coloured_blocks+wood_blocks

floorBlocks = ["planks"]

lighting_blocks = ["glowstone", "shroomlight", "sea_lantern", "waxed_copper_bulb"]

flowers = [
    "allium", "azure_bluet", "blue_orchid", "dandelion", "closed_eyeblossom", "open_eyeblossom", "lily_of_the_valley", "oxeye_daisy", "poppy",
    "torchflower", "orange_tulip", "pink_tulip", "red_tulip", "white_tulip", "wither_rose", "lilac", "peony", "pitcher_plant", "rose_bush", "sunflower"
]

def manageBlockVariations(block: str) -> List[Block]:
    result = []

    if block not in block_black_list:
        result += [Block(block)]

    if block in coloured_blocks:
        result += [Block(f"{random.choice(colours)}_{block}")]

    if block in cracked_blocks:
        result+= [Block("cracked_"+block)]

    if block in wood_blocks:
        wood_type = random.choice(woods)
        if block=="log":
            if wood_type=="crimson" or wood_type=="warped":
                block = "stem"
            if wood_type=="bamboo":
                block = "block"
        result += [Block(f"{wood_type}_{block}")]


    return result


def getBlock(purpose: str, facing=None, hinge=None, half=None) -> List[Block]:
    if purpose == "wall":
        block = random.choice(wallBlocks)
        return manageBlockVariations(block)
    elif purpose == "floor":
        block = random.choice(floorBlocks)
        return manageBlockVariations(block)
    elif purpose == "column":
        block = random.choice(column_blocks)
        return manageBlockVariations(block)
    elif purpose == "fence":
        block = random.choice(fence_blocks)
        if block == "fence":
            return [Block(random.choice(woods)+"_fence")]
        else:
            return [Block(random.choice(wall_blocks)+"_wall")]
    elif purpose == "gate":
        return [Block(random.choice(woods)+"_fence_gate")]
    elif purpose == "door":
        return [Block(random.choice(door_materials)+"_door")]
    elif purpose == "light":
        block_name = random.choice(lighting_blocks)
        if block_name == "waxed_copper_bulb":
            block = [Block(block_name, {"lit":"true"})]
        else:
            block = [Block(block_name)]
        return block
    elif purpose == "flower":
        if random.randint(0,10) == 1:
            return [Block(random.choice(flowers))]
        else: return [Block("air")]
    else:
        raise ValueError(f"Unknown purpose: {purpose}")
        
        
