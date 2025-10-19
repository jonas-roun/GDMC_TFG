# room_grammar.py
from random import randint

from gdpc import Editor, Block

from grammar import MCSplitGrammar, SplitGrammar
from grammar.MCSplitGrammar import collect_blocks, start_symbol
from urbanismo.parcela import Parcela
from .SplitGrammar import rule, split, fill, void, Dimension, clearrules, CONTEXT, reorient, rotate

# ---- Constantes de materiales ----
MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3
FENCE_BLOCK = 4
DOOR_BLOCK = 5
GATE_BLOCK = 6

CURRENT_PLOT: Parcela

# ---- Limpiar reglas previas ----
clearrules(__file__)


# ==================================================
# REGLAS DE GRAMÁTICA
# ==================================================


@rule
def plot():
    """
    Rota la parcela aleatoriamente 0, 90, 180 o 270 grados
    """
    orientacion = randint(0, 3)
    rotation_degrees = orientacion * 90  # 0, 90, 180, 270

    with rotate(rotation_degrees):
        plot_oriented()


@rule
def plot_oriented():
    if CURRENT_PLOT.uso == "lowDesRes":
        with split(Dimension.Y, [6, -1]):
            chaletPlot()
            void()
    elif CURRENT_PLOT.uso == "hiDesRes":
        blockPlot()
    else:
        raise ValueError(f"Uso {CURRENT_PLOT.uso} no implementado en la gramática")


@rule
def blockPlot():
    # Calcular cuántos pisos caben
    available_height = CONTEXT[-1].get_value(Dimension.Y) // 2
    floor_height = 5  # Misma altura que chalet
    num_floors = randint(2, (available_height // floor_height))

    if num_floors <= 1:
        chalet()
    else:
        floor_sizes = [floor_height] * num_floors
        remaining = available_height - (floor_height * num_floors)
        if remaining > 0:
            floor_sizes.append(-1)  # Espacio restante vacío

        with split(Dimension.Y, floor_sizes):
            for _ in range(num_floors):
                room()
            if remaining > 0:
                void()


@rule(constraint=(Dimension.X < 9) & (Dimension.Z < 9))
def chaletPlot():
    chalet()


@rule(constraint=(Dimension.X >= 9) | (Dimension.Z >= 9))
def chaletPlot():
    plot_width = CONTEXT[-1].get_value(Dimension.X)
    if plot_width <= 8:
        chalet()
    else:
        chalet_width = randint(6, max(6, plot_width - 2))  # Asegurar >= 6

        # Asegurar que hay espacio para jardines
        remaining_space = plot_width - chalet_width
        if remaining_space < 2:  # No hay espacio para jardines a ambos lados
            chalet()
            return

        garden_width_left = randint(1, remaining_space - 1)
        garden_width_right = remaining_space - garden_width_left

        with split(Dimension.X, [garden_width_left, chalet_width, garden_width_right]):
            left_garden_side()
            garden_center()
            right_garden_side()


@rule(constraint=(Dimension.X >= 2))
def right_garden_side():
    with split(Dimension.Z, [1, -1, 1]):
        fence()
        with split(Dimension.X, [-1, 1]):
            void()
            fence()
        fence()


@rule(constraint=(Dimension.X >= 2))
def left_garden_side():
    with split(Dimension.Z, [1, -1, 1]):
        fence()
        with split(Dimension.X, [1, -1]):
            fence()
            void()
        fence()


@rule(constraint=(Dimension.X == 1))
def left_garden_side():
    fence()


@rule(constraint=(Dimension.X == 1))
def right_garden_side():
    fence()


@rule
def fence():
    with split(Dimension.Y, [1, 1, -1]):
        void()
        fill(FENCE_BLOCK)
        void()


@rule
def front_fence():
    width = CONTEXT[-1].get_value(Dimension.X)
    if width < 3:
        # No hay espacio para puerta, solo vallas
        fill(FENCE_BLOCK)
        return
    left_space_gate = randint(1, width - 2)
    right_space_gate = width - left_space_gate - 1
    with split(Dimension.Y, [1, 1, -1]):
        void()
        with split(Dimension.X, [left_space_gate, 1, right_space_gate]):
            fill(FENCE_BLOCK)
            fill(GATE_BLOCK)
            fill(FENCE_BLOCK)
        void()


@rule
def garden_center():
    plot_depth = CONTEXT[-1].get_value(Dimension.Z)
    if plot_depth <= 8:  # Mínimo para jardín + casa
        chalet()  # Solo casa, sin jardines
    else:
        chalet_depth = randint(6, plot_depth - 2)
        garden_depth_back = randint(0, plot_depth - chalet_depth - 2)  # dejar hueco para la puerta delantera del jardin
        garden_depth_front = plot_depth - chalet_depth - garden_depth_back
        with split(Dimension.Z, [garden_depth_back, chalet_depth, garden_depth_front]):
            garden_back()
            chalet()
            garden_front()


@rule
def garden_back():
    with split(Dimension.Z, [1, -1]):
        fence()
        void()


@rule
def garden_front():
    with split(Dimension.Z, [CONTEXT[-1].get_value(Dimension.Z) - 1, 1]):
        void()
        front_fence()


@rule
def chalet():
    # with split(Dimension.X, [-1, -1]):
    #     with split(Dimension.Z, [-1, -1]):
    #         corner(90)  # Noreste - 90°
    #         corner(0)  # Noroeste - 0°
    #     with split(Dimension.Z, [-1, -1]):
    #         corner(180)  # Sureste - 180°
    #         corner(270)  # Suroeste - 270°
    room()


@rule
def house():
    """
    Estructura completa de la casa:
    - 6 bloques de habitación (paredes + interior)
    - 3 bloques de tejado encima
    """
    with split(Dimension.Y, [6, 3, -1]):
        walls_and_interior()
        # roof()
        void()


@rule
def walls_and_interior():
    """
    Habitación de 6 bloques de alto.
    Las paredes se crean primero (de arriba a abajo completas).
    """
    room()


@rule
def room():
    """
    Divide el espacio en 4 cuartos iguales (2x2).
    Cada cuarto construye sus paredes según su posición.
    """
    with split(Dimension.X, [-1, -1]):
        with split(Dimension.Z, [-1, -1]):
            corner(0)  # Cuarto noreste - 90°
            corner(270)  # Cuarto suroeste - 270°
        with split(Dimension.Z, [-1, -1]):
            corner(90)  # Cuarto sureste - 180°
            corner(180)  # Cuarto noroeste - 0°


@rule(probability=9)
def corner(degrees):
    """
    Versión normal (90%): construye paredes exteriores (forma rectángulo)
    """
    corner_normal(degrees)


@rule(probability=1, constraint=(Dimension.X > 4) & (Dimension.Z > 4))
def corner(degrees):
    """
    Versión invertida (10%): construye paredes interiores (forma L)
    Solo si el cuarto es grande (>5 en X y Z)
    """
    print("corner invertido")
    corner_inverted(degrees)


@rule
def corner_normal(degrees):
    """
    Cuarto normal: construye paredes en sus bordes exteriores.
    Usa rotación para simplificar: define solo la esquina noroeste (0°)
    y rota según los grados recibidos.
    """
    # if degrees == 90:
    #     fill(FENCE_BLOCK)
    #     return

    with rotate(degrees):
        # Siempre construimos la esquina noroeste (pared oeste + pared norte)
        with split(Dimension.X, [1, -1]):
            # fill(MAIN_BLOCK)
            # fill(COLUMN_BLOCK)
            walls_only()
            with split(Dimension.Z, [1, -1]):
                walls_only()
                interior()


@rule
def corner_inverted(degrees):
    """
    Cuarto invertido: construye paredes en la esquina opuesta.
    Usa rotación para simplificar: define solo un caso base y rota.
    """
    print(f"DEBUG corner_inverted: rotation={degrees}°")

    with rotate(degrees):
        # Caso base: noroeste invertido (paredes en esquina sureste)
        with split(Dimension.X, [-1, 1]):
            with split(Dimension.Z, [-1, 1]):
                void()
                walls_only()
            walls_only()


@rule
def interior():
    """
    Interior hueco con suelo y techo.
    """
    with split(Dimension.Y, [1, -1, 1]):
        fill(FLOOR_BLOCK)
        void()
        fill(COLUMN_BLOCK)


@rule
def walls_only():
    """
    Solo paredes sólidas (sin suelo ni techo).
    """
    with split(Dimension.Y, [2, 1, -1]):
        fill(MAIN_BLOCK)
        windows()
        fill(MAIN_BLOCK)


@rule
def windows():
    L = CONTEXT[-1].get_value(Dimension.LARGEST)

    # Número total de tramos aleatorio (al menos 1)
    n_tramos = randint(1, max(1, L))

    if n_tramos == 1:
        # Solo un tramo, todo 'a'
        fill(MAIN_BLOCK)
        return

    # Calculamos longitud base de cada tramo
    len_base = L // n_tramos

    # Construimos patrón alternando 'a' y 'b'
    patron = [len_base] * n_tramos

    # Dar el sobrante al último tramo
    sobrante = L - sum(patron)
    patron[-1] += sobrante

    # Aplicar patrón
    with reorient(x=Dimension.LARGEST, y=Dimension.Y):
        with split(Dimension.X, patron):
            for i, tramo in enumerate(patron):
                if i % 2 == 0:
                    fill(MAIN_BLOCK)  # 'a'
                else:
                    fill(8)  # 'b'


# ==================================================
# FUNCIÓN PRINCIPAL
# ==================================================

def get_room(parcela: Parcela):
    """
    Genera una casa en la parcela usando la gramática.

    Retorna un diccionario {(x, y, z): block_id} con todos los bloques.
    """
    global CURRENT_PLOT
    CURRENT_PLOT = parcela
    # Registrar materiales
    SplitGrammar.register_material(MAIN_BLOCK, parcela.mainBlock)
    SplitGrammar.register_material(FLOOR_BLOCK, parcela.floorBlock)
    SplitGrammar.register_material(COLUMN_BLOCK, parcela.columnBlock)
    SplitGrammar.register_material(FENCE_BLOCK, parcela.fenceBlock)
    SplitGrammar.register_material(DOOR_BLOCK, parcela.door)
    SplitGrammar.register_material(GATE_BLOCK, [Block("oak_fence_gate")])
    SplitGrammar.register_material(8, [Block("glass_pane")])

    from .GrammarBox import BoundingBox

    # Caja de construcción: 9 bloques de alto (6 habitación + 3 tejado)
    bbox = BoundingBox(
        (parcela.x, parcela.altura, parcela.y),
        (parcela.ancho, 150, parcela.alto)
    )

    # Crear scope raíz y ejecutar gramática
    sc = MCSplitGrammar.start_symbol(bbox, None)
    plot()

    # Recoger todos los bloques generados
    blocks = collect_blocks(sc)
    return blocks