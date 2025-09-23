from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline
import city_simulator as city
from urbanismo.parcela import Parcela


class HiDesResBuilder:
    def __init__(self, parcela: Parcela):
        self.x0 = 0
        self.z0 = 0
        self.floorplan = None
        self.mainBlock = None

    def construir(self, parcela):

        x0 = city.buildArea.offset.x + parcela.x
        z0 = city.buildArea.offset.z + parcela.y
        placeRectOutline(city.editor, Rect(offset=(x0, z0),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:cobblestone_wall"))
        print(f"Construyendo bloque de apartamentos en {parcela.x}, {parcela.y}")