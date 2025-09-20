from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline
import city_simulator as city

class HiDesResBuilder:
    def construir(self, parcela):

        x0 = city.buildArea.offset.x + parcela.x
        z0 = city.buildArea.offset.z + parcela.z
        placeRectOutline(city.editor, Rect(offset=(x0, z0),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:cobblestone_wall"))
        print(f"Construyendo bloque de apartamentos en {parcela.x}, {parcela.z}")
