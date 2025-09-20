from gdpc import Block, Rect
from gdpc.geometry import placeRectOutline
import city_simulator as city

class LowDesResBuilder:
    def construir(self, parcela):

        x0 = city.buildArea.offset.x + parcela.x
        z0 = city.buildArea.offset.z + parcela.z
        placeRectOutline(city.editor, Rect(offset=(x0, z0),
                                           size=(parcela.ancho, parcela.alto)), parcela.altura + 1,
                         Block("minecraft:oak_fence"))
        print(f"Construyendo chalet de apartamentos en {parcela.x}, {parcela.z}")
