from grammar import SplitGrammar
from grammar.SplitGrammar import rule, split, reorient, void, fill, Dimension, Direction, Constraint, Scope, clearrules


# --------------------------------------------------
# Scope adaptado para almacenar bloques en un diccionario
# --------------------------------------------------
# Clase MCScope compatible con SplitGrammar
class MCScope(SplitGrammar.Scope):
    def __init__(self, level, box, **kwargs):
        super(MCScope, self).__init__(box, **kwargs)
        self.level = level
        self.blocks = {}  # Aquí almacenaremos todos los bloques

    def make_child(self, box, **kwargs):
        return MCScope(self.level, box, **kwargs)

    def set_material(self, material):
        for (x, y, z) in self.box.positions:
            self.blocks[(x, y, z)] = material  # Guardamos en el diccionario


def start_symbol(box, level):
    scope = MCScope(level, box, source="Root")
    return SplitGrammar.start_symbol(scope)




def collect_blocks(scope):
    blocks = dict(scope.blocks)
    for child in scope.children:
        blocks.update(collect_blocks(child))
    return blocks

# --------------------------------------------------
# Registro de materiales (como strings)
# --------------------------------------------------
SplitGrammar.register_material(-1, "minecraft:stone")
SplitGrammar.register_material(0, "minecraft:air")
SplitGrammar.register_material(1, "minecraft:cobblestone")
SplitGrammar.register_material(2, "minecraft:oak_planks")
SplitGrammar.register_material(3, "minecraft:granite")
SplitGrammar.register_material(4, "minecraft:diorite")
SplitGrammar.register_material(5, "minecraft:andesite")
SplitGrammar.register_material(6, "minecraft:quartz_block")
