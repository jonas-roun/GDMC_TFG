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
wood_blocks = ["planks", "door", "fence"]

wallBlocks = ["concrete", "cobblestone", "terracotta"] +buildingBricks

#mossy_blocks = ["stone_bricks", "cobblestone"]
#blocks with a cracked variant
cracked_blocks = ["stone_bricks", "polished_blackstone_bricks", "deepslate_bricks", "deepslate_tiles","nether_bricks"]

#blocks that dont exist on their own, but are used because of their colour variants or similar
block_black_list = ["concrete", "terracotta", "planks", "door", "fence"]

floorBlocks = ["planks"]

def manageBlockVariations(block: str) -> List[Block]:
    result = []

    if block not in block_black_list:
        result += [Block(block)]

    if block in coloured_blocks:
        result += [Block(f"{random.choice(colours)}_{block}")]

    if block in cracked_blocks:
        result+= [Block("cracked_"+block)]

    if block in wood_blocks:
        result += [Block(f"{random.choice(woods)}_{block}")]

    return result


def getBlock(purpose: str, facing=None, half=None) -> List[Block]:
    if purpose == "wall":
        block = random.choice(wallBlocks)
        return manageBlockVariations(block)
    elif purpose == "floor":
        block = random.choice(floorBlocks)
        return manageBlockVariations(block)
    else:
        raise ValueError(f"Unknown purpose: {purpose}")
        
        
