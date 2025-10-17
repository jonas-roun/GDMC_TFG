from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline
import city_simulator as city
from grammar import room_grammar
from urbanismo.parcela import Parcela


class HiDesResBuilder:
    @staticmethod
    def build(parcela: Parcela):
        blocks = room_grammar.get_room(parcela)

        # Colocar los bloques en el mundo
        for coord, block in blocks.items():
            if isinstance(block[0], Block):
                city.editor.placeBlock(
                    (coord[0] + city.buildArea.offset.x, coord[1], coord[2] + city.buildArea.offset.z), block)

        # Confirmar cambios (importante si usamos buffering=True)
        city.editor.flushBuffer()

    def construir(self, parcela):

        x0 = city.buildArea.offset.x + parcela.x
        z0 = city.buildArea.offset.z + parcela.y
        placeRectOutline(city.editor, Rect(offset=(x0, z0),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:cobblestone_wall"))
        print(f"Construyendo bloque de apartamentos en {parcela.x}, {parcela.y}")

    @staticmethod
    def create_floorplan(parcela: Parcela) -> None:
        pass