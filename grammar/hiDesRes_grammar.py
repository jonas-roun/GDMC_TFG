from random import randint

from .SplitGrammar import rule, split, fill, void, Dimension, CONTEXT, Rounding, debug_rule, rotate
from .common_rules import windowed_wall, wall_with_door, lit_interior, corner_normal

# ---- Constantes de materiales ----
MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3
FENCE_BLOCK = 4
DOOR_BLOCK = 5
GATE_BLOCK = 6
LIGHT_BLOCK = 7
WINDOW_BLOCK = 8
ROOF_BLOCK = 9
ACCENT_BLOCK = 10
STAIR_SPAWN = 11
FIRST_STAIR_SPAWN = 12

corridor_width:int

@rule
@debug_rule
def blockPlot():
    global corridor_width
    if CONTEXT[-1].get_value(Dimension.Z)<13:
        void()
        return
    available_height = CONTEXT[-1].get_value(Dimension.Y) // 2
    floor_height = 5
    num_floors = randint(2, (available_height // floor_height))
    corridor_width = randint(2, 4)
    floor_sizes = [floor_height] * num_floors
    remaining = available_height - (floor_height * num_floors)
    if remaining > 0:
        floor_sizes.append(-1)
    with rotate(90):
        with split(Dimension.Y, floor_sizes, rounding_mode=Rounding.END):
            for i in range(num_floors):
                if i==0:
                    first_story()
                else:
                    story()
            if remaining > 0:
                void()

@rule
@debug_rule
def story():
    with split(Dimension.Z, [corridor_width, -1]):
        with split(Dimension.X, [-1, 1], rounding_mode=Rounding.END):
            corridor()
            windowed_wall()
        with split(Dimension.X, [4,-1], rounding_mode=Rounding.END):
            with split(Dimension.Z, [5,-1], rounding_mode=Rounding.END):
                staircase()
                corner_normal(270)
            apartment_row()#fill(COLUMN_BLOCK)

@rule
@debug_rule
def first_story():
    with split(Dimension.Z, [corridor_width, -1]):
        with split(Dimension.X, [-1,1], rounding_mode=Rounding.END):
            corridor()
            wall_with_door()
        with split(Dimension.X, [4,-1], rounding_mode=Rounding.END):
            with split(Dimension.Z, [5,-1], rounding_mode=Rounding.END):
                first_staircase()
                corner_normal(270)
            fill(COLUMN_BLOCK)#apartment_row()

@rule
@debug_rule
def corridor():
    with split(Dimension.X, [1,-1]):
        with split(Dimension.Y, [-1,1]):
            fill(MAIN_BLOCK)
            fill(COLUMN_BLOCK)
        with split(Dimension.Z, [1,-1]):
            with split(Dimension.Y, [-1,1]):
                windowed_wall()
                fill(COLUMN_BLOCK)
            with split(Dimension.Y,[1,-1,1]):
                fill(FLOOR_BLOCK)
                void()
                fill(COLUMN_BLOCK)

@rule
@debug_rule
def apartment_row():
    rooms = split(Dimension.X, [5], repeat=True)
    while rooms:
        apartment()

@rule
@debug_rule
def apartment():
    with split(Dimension.Z, [-1,3]):
        with split(Dimension.X, [1, -1], rounding_mode=Rounding.END):
            with split(Dimension.Y, [-1, 1], rounding_mode=Rounding.END):
                fill(MAIN_BLOCK)
                fill(COLUMN_BLOCK)
            with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
                wall_with_door()
                with rotate(180):
                    lit_interior()
        with split(Dimension.Y, [-1, 1], rounding_mode=Rounding.END):
            exterior_wall()
            fill(COLUMN_BLOCK)


@rule
@debug_rule
def exterior_wall():
    with split(Dimension.X, [1,-1]):
        fill(MAIN_BLOCK)
        with split(Dimension.Z, [-1,1]):
            with split(Dimension.Y, [1,-1]):
                fill(FLOOR_BLOCK)
                void()
            windowed_wall()


@rule#(constraint=(Dimension.Z>1000000))
@debug_rule
def exterior_wall():
    terrace()

@rule
@debug_rule
def terrace():
    enclosed_terrace()

@rule
@debug_rule
def terrace():
    open_terrace()

@rule
@debug_rule
def enclosed_terrace():
    with split(Dimension.X, [1,-1], rounding_mode=Rounding.END):
        fill(MAIN_BLOCK)
        with split(Dimension.Z, [-1,1], rounding_mode=Rounding.END):
            with split(Dimension.Y, [1,-1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                void()
            with split(Dimension.Y, [1,1,2,-1], rounding_mode=Rounding.END):
                fill(MAIN_BLOCK)
                fill(COLUMN_BLOCK)
                fill(WINDOW_BLOCK)
                fill(COLUMN_BLOCK)


@rule
@debug_rule
def open_terrace():
    with split(Dimension.X, [1,-1], rounding_mode=Rounding.END):
        fill(MAIN_BLOCK)
        with split(Dimension.Z, [-1,1], rounding_mode=Rounding.END):
            with split(Dimension.Y, [1,-1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                void()
            with split(Dimension.Y, [1,1,-1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                fill(FENCE_BLOCK)
                void()

@rule
@debug_rule
def staircase():
    with split(Dimension.X, [-1,1], rounding_mode=Rounding.END):
        void()
        with split(Dimension.Z, [-1,1], rounding_mode=Rounding.END):
            void()
            with split(Dimension.Y, [1,-1], rounding_mode=Rounding.END):
                fill(STAIR_SPAWN)
                void()

@rule
@debug_rule
def first_staircase():
    with split(Dimension.X, [-1,1], rounding_mode=Rounding.END):
        void()
        with split(Dimension.Z, [-1,1], rounding_mode=Rounding.END):
            void()
            with split(Dimension.Y, [1,-1], rounding_mode=Rounding.END):
                fill(FIRST_STAIR_SPAWN)
                void()
