# room_grammar.py - División Z primero, luego X
from random import randint

from .SplitGrammar import rule, split, fill, void, Dimension, CONTEXT, rotate, Rounding, debug_rule, reorient

# ---- Constantes de materiales ----
MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3
FENCE_BLOCK = 4
DOOR_BLOCK = 5
GATE_BLOCK = 6
LIGHT_BLOCK = 7


@rule(probability=9)
@debug_rule
def corner(degrees):
    corner_normal(degrees)


@rule(probability=1, constraint=(Dimension.X > 4) & (Dimension.Z > 4))
@debug_rule
def corner(degrees):
    print("corner invertido")
    corner_inverted(degrees)


@rule
@debug_rule
def corner_normal(degrees):
    with rotate(degrees):
        with split(Dimension.X, [1, -1], rounding_mode=Rounding.END):
            windowed_wall()
            with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
                windowed_wall()
                interior()


@rule
@debug_rule
def corner_inverted(degrees):
    print(f"DEBUG corner_inverted: rotation={degrees}°")
    with rotate(degrees):
        with split(Dimension.X, [-1, 1], rounding_mode=Rounding.START):
            with split(Dimension.Z, [-1, 1], rounding_mode=Rounding.START):
                void()
                windowed_wall()
            windowed_wall()


@rule
@debug_rule
def interior():
    with split(Dimension.Y, [1, -1, 1], rounding_mode=Rounding.MIDDLE):
        fill(FLOOR_BLOCK)
        void()
        fill(COLUMN_BLOCK)

@rule
@debug_rule
def lit_interior():
    with split(Dimension.Y, [1, -1, 1], rounding_mode=Rounding.MIDDLE):
        fill(FLOOR_BLOCK)
        void()
        with split(Dimension.Z, [-1, 1], rounding_mode=Rounding.END):
            fill(COLUMN_BLOCK)
            with split(Dimension.X, [-1, 1], rounding_mode=Rounding.END):
                fill(COLUMN_BLOCK)
                fill(LIGHT_BLOCK)


@rule
@debug_rule
def windowed_wall():
    with split(Dimension.Y, [2, 1, -1], rounding_mode=Rounding.END):
        fill(MAIN_BLOCK)
        windows()
        fill(MAIN_BLOCK)


@rule
@debug_rule
def windows():
    L = CONTEXT[-1].get_value(Dimension.LARGEST)
    n_tramos = randint(1, max(1, L))

    if n_tramos == 1:
        fill(MAIN_BLOCK)
        return

    len_base = L // n_tramos
    patron = [len_base] * n_tramos
    sobrante = L - sum(patron)
    patron[-1] += sobrante

    with reorient(x=Dimension.LARGEST, y=Dimension.Y):
        with split(Dimension.X, patron, rounding_mode=Rounding.END):
            for i, tramo in enumerate(patron):
                if i % 2 == 0:
                    fill(MAIN_BLOCK)
                else:
                    fill(8)


@rule
@debug_rule
def wall_with_door(door_offset=-1):
    with split(Dimension.Y, [1,2, -1], rounding_mode=Rounding.END):
        fill(MAIN_BLOCK)
        with split(Dimension.LARGEST, [-1, 1, door_offset], rounding_mode=Rounding.END):
            fill(MAIN_BLOCK)
            with split(Dimension.Y, [1,1]):
                fill(DOOR_BLOCK)
                void()
            fill(MAIN_BLOCK)
        fill(MAIN_BLOCK)