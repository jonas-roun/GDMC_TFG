from random import randint

from .SplitGrammar import rule, split, fill, void, Dimension, CONTEXT, rotate, Rounding, debug_rule
from .lowDesRes_grammar import chalet, room

# ---- Constantes de materiales ----
MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3
FENCE_BLOCK = 4
DOOR_BLOCK = 5
GATE_BLOCK = 6

@rule
@debug_rule
def blockPlot():
    available_height = CONTEXT[-1].get_value(Dimension.Y) // 2
    floor_height = 5
    num_floors = randint(2, (available_height // floor_height))

    if num_floors <= 1:
        chalet()
    else:
        floor_sizes = [floor_height] * num_floors
        remaining = available_height - (floor_height * num_floors)
        if remaining > 0:
            floor_sizes.append(-1)

        with split(Dimension.Y, floor_sizes, rounding_mode=Rounding.END):
            for _ in range(num_floors):
                room()
            if remaining > 0:
                void()