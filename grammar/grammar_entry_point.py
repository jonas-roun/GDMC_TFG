# room_grammar.py - División Z primero, luego X
from random import randint

from gdpc import Editor, Block

from grammar import MCSplitGrammar, SplitGrammar
from grammar.MCSplitGrammar import collect_blocks, start_symbol
from urbanismo.parcela import Parcela, Direction
from .SplitGrammar import rule, split, fill, void, Dimension, clearrules, CONTEXT, rotate, Rounding, debug_rule
from .hiDesRes_grammar import blockPlot
from .lowDesRes_grammar import chaletPlot

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

CURRENT_PLOT: Parcela


# ---- Limpiar reglas previas ----
clearrules(__file__)


# ==================================================
# REGLAS DE GRAMÁTICA
# ==================================================

@rule
@debug_rule
def plot():
    """
    Rota la parcela aleatoriamente 0, 90, 180 o 270 grados
    """
    orientacion = (CURRENT_PLOT.orientation)%4
    rotation_degrees = orientacion * 90  # 0, 90, 180, 270

    with rotate(rotation_degrees):
        plot_oriented()


@rule
@debug_rule
def plot_oriented():
    if CURRENT_PLOT.uso == "lowDesRes":
        with split(Dimension.Y, [6, -1], rounding_mode=Rounding.END):
            chaletPlot()
            void()
    elif CURRENT_PLOT.uso == "hiDesRes":
        blockPlot()
    else:
        raise ValueError(f"Uso {CURRENT_PLOT.uso} no implementado en la gramática")








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
    SplitGrammar.register_material(MAIN_BLOCK, [Block(parcela.paleta["primary"])])
    SplitGrammar.register_material(FLOOR_BLOCK, [Block(parcela.paleta["floor"])])
    SplitGrammar.register_material(COLUMN_BLOCK, [Block(parcela.paleta["ceiling"])])
    SplitGrammar.register_material(FENCE_BLOCK, [Block(parcela.paleta["fence"])])
    SplitGrammar.register_material(DOOR_BLOCK, [Block(parcela.paleta["door"])])
    SplitGrammar.register_material(GATE_BLOCK, [Block(parcela.paleta["gate"])])
    SplitGrammar.register_material(LIGHT_BLOCK, [Block(parcela.paleta["light"])])
    SplitGrammar.register_material(WINDOW_BLOCK, [Block(parcela.paleta["window"])])
    SplitGrammar.register_material(ROOF_BLOCK, [Block(parcela.paleta["roof"])])
    SplitGrammar.register_material(ACCENT_BLOCK, [Block(parcela.paleta["accent"])])

    SplitGrammar.register_material(STAIR_SPAWN, ["stair_spawn"])
    SplitGrammar.register_material(FIRST_STAIR_SPAWN, ["first_stair_spawn"])

    from .GrammarBox import BoundingBox

    bbox = BoundingBox(
        (parcela.x, parcela.altura, parcela.y),
        (parcela.ancho, 150, parcela.alto)
    )

    sc = MCSplitGrammar.start_symbol(bbox, None)
    plot()

    blocks = collect_blocks(sc)
    return blocks