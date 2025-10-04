# simple_room_grammar.py
from gdpc import Editor, Block


from grammar import MCSplitGrammar, SplitGrammar
from grammar.MCSplitGrammar import collect_blocks, start_symbol
from urbanismo.parcela import Parcela
from .SplitGrammar import rule, split, fill, void, start_symbol, Dimension, Direction, Scope, clearrules, CONTEXT


MAIN_BLOCK = 1
FLOOR_BLOCK = 2
COLUMN_BLOCK = 3

# ---- Limpiar reglas previas ----
clearrules(__file__)


# ---- Reglas ----

@rule
def plot():
    with split(Dimension.Y, [6, -1]):
        room()
        void()

@rule
def room():
    with split(Dimension.X, [1, -1, 1]):
        fill(1)
        with split(Dimension.Z, [1, -1, 1]):
            fill(1)
            interior()
            fill(1)
        fill(1)



def interior():
    with split(Dimension.Y, [1, -1, 1]):
        fill(2)
        void()
        fill(3)


# ---- main para generar el castillo ----
def get_room(parcela: Parcela):
    SplitGrammar.register_material(MAIN_BLOCK, parcela.mainBlock)
    SplitGrammar.register_material(FLOOR_BLOCK, parcela.floorBlock)
    SplitGrammar.register_material(COLUMN_BLOCK, parcela.columnBlock)

    from .GrammarBox import BoundingBox



    # Definir la caja de construcción como BoundingBox de GrammarBox
    bbox = BoundingBox((parcela.x, parcela.altura, parcela.y), (parcela.ancho, 100, parcela.alto))

    # Crear scope raíz
    sc = MCSplitGrammar.start_symbol(bbox, None)

    # Ejecutar la gramática (esto rellena el árbol de scopes con bloques)
    plot()

    # Recoger todos los bloques generados en un único diccionario
    blocks = collect_blocks(sc)
    return blocks;