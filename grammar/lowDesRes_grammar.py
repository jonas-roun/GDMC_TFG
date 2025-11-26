from random import randint

from . import grammar_entry_point
from .SplitGrammar import rule, split, fill, void, Dimension, CONTEXT, Rounding, debug_rule
from .common_rules import corner, windowed_wall, interior, wall_with_door, lit_interior

# ---- Constantes de materiales ----
MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3
FENCE_BLOCK = 4
DOOR_BLOCK = 5
GATE_BLOCK = 6

@rule(constraint=(Dimension.Z < 10) | (Dimension.X < 10))
@debug_rule
def chaletPlot():
    chalet(grammar_entry_point.CURRENT_PLOT.doorPosition)


@rule(constraint=(Dimension.Z >= 10) & (Dimension.X >= 10))
@debug_rule
def chaletPlot():
    """
    NUEVA LÓGICA: Primero dividimos en Z (atrás-centro-adelante)
    CORREGIDO: Aseguramos que las divisiones cubren toda la parcela
    """
    plot_depth = CONTEXT[-1].get_value(Dimension.Z)

    if plot_depth <= 8:
        chalet(grammar_entry_point.CURRENT_PLOT.doorPosition)
        return

    # Tamaño del chalet en profundidad (Z) - mínimo 6, máximo deja espacio para jardines
    max_chalet_depth = max(6, plot_depth - 4)  # Dejamos al menos 4 para jardines
    chalet_depth = randint(6, max_chalet_depth)

    # Calcular jardines trasero y delantero
    remaining_depth = plot_depth - chalet_depth

    # Si no hay espacio suficiente para jardines, solo chalet
    if remaining_depth < 2:
        chalet(grammar_entry_point.CURRENT_PLOT.doorPosition)
        return

    # Distribuir el espacio restante entre jardines
    garden_depth_back = randint(1, remaining_depth - 1)
    garden_depth_front = remaining_depth - garden_depth_back

    # VERIFICACIÓN: Asegurar que suma exactamente plot_depth
    assert garden_depth_back + chalet_depth + garden_depth_front == plot_depth, \
        f"Error: {garden_depth_back} + {chalet_depth} + {garden_depth_front} != {plot_depth}"

    # Split en Z: atrás, centro, adelante
    with split(Dimension.Z, [garden_depth_back, chalet_depth, garden_depth_front], rounding_mode=Rounding.END):
        garden_back_strip()
        chalet_strip()
        garden_front_strip()


@rule(constraint=Dimension.Z>=1)
@debug_rule
def garden_back_strip():
    """
    Franja trasera: solo jardín (o vacío si no hay espacio)
    """
    depth = CONTEXT[-1].get_value(Dimension.Z)
    if depth == 1:
        fence()
    else:
        with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
            fence()
            with split(Dimension.X, [1,-1,1], rounding_mode=Rounding.MIDDLE):
                fence()
                lawn()
                fence()


@rule(constraint=Dimension.Z>1)
@debug_rule
def garden_front_strip():
    """
    Franja delantera: jardín con valla frontal
    """
    with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
        with split(Dimension.X, [1, -1, 1], rounding_mode=Rounding.MIDDLE):
            fence()
            lawn()
            fence()
        front_fence()


@rule
@debug_rule
def chalet_strip():
    """
    Franja central: ahora dividimos en X (izquierda-chalet-derecha)
    """
    plot_width = CONTEXT[-1].get_value(Dimension.X)


    # Tamaño del chalet en anchura (X)
    chalet_width = randint(6, max(6, plot_width - 3))

    # Calcular jardines laterales
    remaining_width = plot_width - chalet_width
    # if remaining_width <= 2:
    #     chalet()
    #     return

    # Por ahora distribuimos equitativamente (luego usarás doorPosition)
    garden_width_left = remaining_width // 2
    garden_width_right = remaining_width - garden_width_left

    # Split en X: izquierda, centro, derecha
    with split(Dimension.X, [garden_width_left, chalet_width, garden_width_right], rounding_mode=Rounding.MIDDLE):
        garden_left_side()
        chalet()
        garden_right_side()


@rule(constraint=(Dimension.X >= 2))
@debug_rule
def garden_left_side():
    """
    Jardín lateral izquierdo
    """
    with split(Dimension.X, [1, -1], rounding_mode=Rounding.END):
        fence()
        lawn()


@rule(constraint=(Dimension.X >= 2))
@debug_rule
def garden_right_side():
    """
    Jardín lateral derecho
    """
    with split(Dimension.X, [-1, 1], rounding_mode=Rounding.START):
        lawn()
        fence()


@rule(constraint=(Dimension.X == 1))
@debug_rule
def garden_left_side():
    fence()


@rule(constraint=(Dimension.X == 1))
@debug_rule
def garden_right_side():
    fence()


@rule
@debug_rule
def fence():
    with split(Dimension.Y, [1, 1, -1], rounding_mode=Rounding.END):
        void()
        fill(FENCE_BLOCK)
        void()






@rule
@debug_rule
def front_fence():
    """
    Valla frontal con gate en la posición óptima calculada.
    Esta regla se ejecuta en el contexto YA rotado por plot(),
    así que doorPosition ya está en el sistema correcto.
    """
    width = CONTEXT[-1].get_value(Dimension.X)


    # doorPosition ya está ajustado para este sistema de coordenadas
    gate_pos = grammar_entry_point.CURRENT_PLOT.doorPosition

    # Validar que gate_pos está dentro del rango
    if gate_pos < 1:
        gate_pos = 1
    elif gate_pos >= width - 1:
        gate_pos = width - 2

    left_fence = gate_pos
    right_fence = width - gate_pos - 1

    with split(Dimension.Y, [1, 1, -1], rounding_mode=Rounding.END):
        void()
        with split(Dimension.Z, [1, -1], rounding_mode=Rounding.END):
            with split(Dimension.X, [right_fence, 1, left_fence], rounding_mode=Rounding.MIDDLE):
                fill(FENCE_BLOCK)
                fill(GATE_BLOCK)
                fill(FENCE_BLOCK)
            void()
        void()



@rule
@debug_rule
def chalet(door_offset=-1):
    with split(Dimension.Y, [5,-1]):
        with split(Dimension.Z, [-1, -1], rounding_mode=Rounding.END):
            with split(Dimension.X, [-1, -1], rounding_mode=Rounding.END):
                corner(0)
                corner(90)
            chalet_front(door_offset)
    void()

@rule
@debug_rule
def chalet_front(door_offset=-1):
    # fill(MAIN_BLOCK)
    # return
    with split(Dimension.X, [1, -1, 1], rounding_mode=Rounding.END):
        windowed_wall()
        with split(Dimension.Z, [-1, 1], rounding_mode=Rounding.END):
            with split(Dimension.X, [-1, -1], rounding_mode=Rounding.END):
                lit_interior()
                lit_interior()
            wall_with_door(door_offset)
        windowed_wall()


@rule
@debug_rule
def lawn():
    void()
    return
    fill(9)