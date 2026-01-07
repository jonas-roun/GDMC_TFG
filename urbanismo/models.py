from typing import List

from gdpc import Block, Editor, Transform
from gdpc.model import Model

lamp_posts: List[Model] = []
first_staircase: Model
staircase: Model

def load_models():
    global lamp_posts, first_staircase, staircase
    lamp_post1 = Model((3,5,3))
    lamp_post1.setBlock((1,0,1), Block("minecraft:cobblestone_wall"))
    lamp_post1.setBlock((1,1,1), Block("minecraft:oak_fence"))
    lamp_post1.setBlock((1,2,1), Block("minecraft:oak_fence"))
    lamp_post1.setBlock((1,3,1), Block("minecraft:oak_planks"))
    lamp_post1.setBlock((2,3,1), Block("minecraft:stone_slab"))
    lamp_post1.setBlock((0,3,1), Block("minecraft:stone_slab"))
    lamp_post1.setBlock((2,2,1), Block("minecraft:lantern"))
    lamp_post1.setBlock((0,2,1), Block("minecraft:lantern"))

    lamp_post2 = Model((3, 5, 3))
    lamp_post2.setBlock((1, 0, 1), Block("minecraft:cobblestone"))
    lamp_post2.setBlock((1, 1, 1), Block("minecraft:cobblestone_wall"))
    lamp_post2.setBlock((1, 2, 1), Block("minecraft:oak_fence"))
    lamp_post2.setBlock((1, 3, 1), Block("minecraft:glowstone"))

    lamp_posts.append(lamp_post1)
    lamp_posts.append(lamp_post2)

    first_staircase = Model((4, 5, 5))

    for y in range(5):
        for z in range(5):  #side walls
            first_staircase.setBlock((0, y, z), Block("cobblestone"))
            first_staircase.setBlock((3, y, z), Block("cobblestone"))
        for x in range(4):  #back wall
            first_staircase.setBlock((x, y, 4), Block("cobblestone"))

    for x in range(1,3):
        for z in range(0,4):
            first_staircase.setBlock((x, 0, z), Block("oak_planks"))

    first_staircase.setBlock((1, 1, 0), Block("oak_stairs", {"facing": "south"}))
    first_staircase.setBlock((1, 1, 1), Block("oak_stairs", {"facing": "north", "half": "top"}))
    first_staircase.setBlock((1, 2, 1), Block("oak_stairs", {"facing": "south"}))
    first_staircase.setBlock((1, 2, 2), Block("oak_stairs", {"facing": "north", "half": "top"}))
    first_staircase.setBlock((1, 3, 2), Block("oak_stairs", {"facing": "south"}))
    first_staircase.setBlock((1, 3, 3), Block("oak_planks"))
    first_staircase.setBlock((2, 3, 3), Block("oak_planks"))
    first_staircase.setBlock((2, 3, 2), Block("oak_stairs", {"facing": "south", "half": "top"}))
    first_staircase.setBlock((2, 4, 2), Block("oak_stairs", {"facing": "north"}))
    first_staircase.setBlock((2, 4, 1), Block("oak_planks"))
    first_staircase.setBlock((2 ,4 ,0), Block("waxed_copper_bulb",{"lit": "true"}))

    staircase = Model((4, 5, 5))

    for y in range(5):
        for z in range(5):  # side walls
            staircase.setBlock((0, y, z), Block("cobblestone"))
            staircase.setBlock((3, y, z), Block("cobblestone"))
        for x in range(4):  # back wall
            staircase.setBlock((x, y, 4), Block("cobblestone"))


    staircase.setBlock((2, 0, 0), Block("oak_planks"))
    staircase.setBlock((1, 0, 0), Block("oak_stairs", {"facing": "north", "half": "top"}))
    staircase.setBlock((2, 0, 1), Block("oak_stairs", {"facing": "north"}))

    staircase.setBlock((1, 1, 0), Block("oak_stairs", {"facing": "south"}))
    staircase.setBlock((1, 1, 1), Block("oak_stairs", {"facing": "north", "half": "top"}))
    staircase.setBlock((1, 2, 1), Block("oak_stairs", {"facing": "south"}))
    staircase.setBlock((1, 2, 2), Block("oak_stairs", {"facing": "north", "half": "top"}))
    staircase.setBlock((1, 3, 2), Block("oak_stairs", {"facing": "south"}))
    staircase.setBlock((1, 3, 3), Block("oak_planks"))
    staircase.setBlock((2, 3, 3), Block("oak_planks"))
    staircase.setBlock((2, 3, 2), Block("oak_stairs", {"facing": "south", "half": "top"}))
    staircase.setBlock((2, 4, 2), Block("oak_stairs", {"facing": "north"}))
    staircase.setBlock((2, 4, 1), Block("oak_planks"))
    staircase.setBlock((2 ,4 ,0), Block("glowstone",{"lit": "true"}))




# editor = Editor(buffering=True)
#
# buildArea = editor.getBuildArea()
#
# # Load world slice of the build area
# editor.loadWorldSlice(cache=True)
#
load_models()
# coords_x = buildArea.offset.x + 75
# coords_y = 100
# first_staircase.build(editor, transformLike=Transform((coords_x, coords_y, buildArea.offset.z), rotation=1))
# coords_y+=5
# staircase.build(editor, transformLike=Transform((coords_x, coords_y, buildArea.offset.z), rotation=1))
# coords_y+=5
# staircase.build(editor, transformLike=Transform((coords_x, coords_y, buildArea.offset.z), rotation=1))
# coords_y+=5
# staircase.build(editor, transformLike=Transform((coords_x, coords_y, buildArea.offset.z), rotation=1))
# editor.flushBuffer()

