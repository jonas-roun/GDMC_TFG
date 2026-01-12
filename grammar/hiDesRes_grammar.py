from random import randint

from .SplitGrammar import rule, split, fill, void, Dimension, CONTEXT, Rounding, debug_rule, rotate
from .common_rules import windowed_wall, wall_with_door, lit_interior, corner_normal, weighted_random_choice

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

TERRACE_WEIGHT = 1
WALL_WEIGHT = 1
CLOSED_TERRACE_WEIGHT = 1
OPEN_TERRACE_WEIGHT = 1

@rule
@debug_rule
def blockPlot():
    global corridor_width
    # if CONTEXT[-1].get_value(Dimension.Z)<13:
    #     void()
    #     return
    available_height = CONTEXT[-1].get_value(Dimension.Y) // 2
    floor_height = 5
    num_floors = randint(2, (available_height // floor_height))
    corridor_width = 2#min(randint(2, 4), CONTEXT[-1].get_value(Dimension.Z-6))
    floor_sizes = [floor_height] * num_floors
    floor_sizes.append(1)
    remaining = available_height - (floor_height * num_floors) -1
    if remaining > 0:
        floor_sizes.append(-1)
    with rotate(90):
        with split(Dimension.Y, floor_sizes, rounding_mode=Rounding.END):
            for i in range(num_floors):
                if i==0:
                    first_story()
                else:
                    story()
            fill(ROOF_BLOCK)
            if remaining > 0:
                void()

@rule
@debug_rule
def story():
    with split(Dimension.Z, [corridor_width, -1]):
        with split(Dimension.X, [-1, 1], rounding_mode=Rounding.END):
            corridor()
            with split(Dimension.Y, [-1, 1], rounding_mode=Rounding.END):
                windowed_wall()
                fill(COLUMN_BLOCK)
        with split(Dimension.X, [4,-1], rounding_mode=Rounding.END):
            with split(Dimension.Z, [5,-1], rounding_mode=Rounding.END):
                staircase()
                corner_normal(270)
            apartment_row()

@rule
@debug_rule
def first_story():
    with split(Dimension.Z, [corridor_width, -1]):
        with split(Dimension.X, [-1,1], rounding_mode=Rounding.END):
            corridor()
            with split(Dimension.Z, [-1,1], rounding_mode=Rounding.START):
                windowed_wall()
                wall_with_door()
        with split(Dimension.X, [4,-1], rounding_mode=Rounding.END):
            with split(Dimension.Z, [5,-1], rounding_mode=Rounding.END):
                first_staircase()
                corner_normal(270)
            apartment_row()#fill(COLUMN_BLOCK)

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
    min_apartment_width = 4
    available_width = CONTEXT[-1].get_value(Dimension.X)

    # Cuántos apartamentos caben como mínimo
    num_apartments = available_width // min_apartment_width

    # Si no cabe ni uno, no hacemos nada
    if num_apartments < 1:
        # corner_normal(180)
        # void()
        apartment()
        return


    # Ancho real de cada apartamento (equitativo)
    apartment_width = available_width // num_apartments

    # Ancho que sobra y NO se usa
    used_width = apartment_width * num_apartments
    remaining = available_width - used_width

    sizes = [apartment_width] * num_apartments
    if remaining > 0:
        sizes.append(-1)  # el sobrante se descarta

    with split(Dimension.X, sizes, rounding_mode=Rounding.END):
        for _ in range(num_apartments):
            apartment()
        if remaining > 0:
            with split(Dimension.Y, [-1,1], rounding_mode=Rounding.END):
                fill(MAIN_BLOCK)
                fill(COLUMN_BLOCK)

@rule
@debug_rule
def apartment():
    with split(Dimension.Z, [-1,2]):
        with split(Dimension.X, [-1, 1], rounding_mode=Rounding.START):

            with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
                wall_with_door()
                with rotate(180):
                    lit_interior()

            with split(Dimension.Y, [-1, 1], rounding_mode=Rounding.END):
                fill(MAIN_BLOCK)
                fill(COLUMN_BLOCK)
        with split(Dimension.Y, [-1, 1], rounding_mode=Rounding.END):
            exterior_wall()
            fill(COLUMN_BLOCK)



@rule
@debug_rule
def exterior_wall():
    """
    Decide si poner una pared normal o una terraza según pesos proporcionales
    """
    choice = weighted_random_choice([WALL_WEIGHT, TERRACE_WEIGHT])

    if choice == 0:
        wall()
    else:  # choice == 1
        terrace()


@rule
@debug_rule
def wall():
    """
    Pared exterior normal con ventana
    """
    with split(Dimension.X, [-1, 1]):
        with split(Dimension.Z, [-1, 1]):
            with split(Dimension.Y, [1, -1]):
                fill(FLOOR_BLOCK)
                void()
            windowed_wall()
        fill(MAIN_BLOCK)


@rule
@debug_rule
def terrace():
    """
    Decide si crear terraza abierta o cerrada según pesos proporcionales
    """
    choice = weighted_random_choice([CLOSED_TERRACE_WEIGHT, OPEN_TERRACE_WEIGHT])

    if choice == 0:
        enclosed_terrace()
    else:  # choice == 1
        open_terrace()


@rule
@debug_rule
def enclosed_terrace():
    """
    Terraza cerrada con ventanas de cristal
    """
    with split(Dimension.X, [-1, 1], rounding_mode=Rounding.END):
        with split(Dimension.Z, [-1, 1], rounding_mode=Rounding.END):
            with split(Dimension.Y, [1, -1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                void()
            with split(Dimension.Y, [1, 1, 2, -1], rounding_mode=Rounding.END):
                fill(MAIN_BLOCK)
                fill(COLUMN_BLOCK)
                fill(WINDOW_BLOCK)
                fill(COLUMN_BLOCK)
        fill(MAIN_BLOCK)


@rule
@debug_rule
def open_terrace():
    """
    Terraza abierta con barandilla
    """
    with split(Dimension.X, [-1, 1], rounding_mode=Rounding.END):
        with split(Dimension.Z, [-1, 1], rounding_mode=Rounding.END):
            with split(Dimension.Y, [1, -1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                void()
            with split(Dimension.Y, [1, 1, -1], rounding_mode=Rounding.END):
                fill(FLOOR_BLOCK)
                fill(FENCE_BLOCK)
                void()
        fill(MAIN_BLOCK)


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
